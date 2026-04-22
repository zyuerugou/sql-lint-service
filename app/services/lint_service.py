#!/usr/bin/env python3
# coding=utf-8
"""
优化的LintService，针对大SQL进行性能优化
"""

import importlib
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig
from watchdog.observers import Observer as WatchdogObserver

from app.services.event_handlers import MultiDirectoryEventHandler
from app.services.preprocessor_manager import PreprocessorManager

logger = logging.getLogger(__name__)


class LintService:
    """
    LintService，针对大SQL进行性能优化
    
    优化策略：
    1. 超时机制：防止单个SQL处理时间过长
    2. 采样检查：对于超大SQL，只检查部分内容
    3. 缓存机制：缓存解析结果
    4. 异步处理：使用线程池处理并发请求
    5. 配置优化：使用ANSI方言和解析器优化
    6. 规则过滤：禁用不必要的规则
    
    方言选择说明：
    - 使用ANSI方言：最通用的SQL标准，解析更宽松，减少"Found unparsable section"错误
    - 特别适合ArgoDB等大数据仓库产品，兼容Oracle风格函数（如NVL）
    - 增加解析限制配置，支持长SQL和复杂查询
    """
    
    def __init__(
        self, 
        enable_hot_reload: bool = False, 
        hot_reload_debounce: float = 0.5,
        timeout_seconds: int = 5,
        max_sql_size_mb: int = 10,
        enable_sampling: bool = True,
        sampling_threshold_kb: int = 100,
        cache_size: int = 100,
        sql_dialect: str = "ansi"
    ):
        """
        初始化优化的LintService
        
        Args:
            enable_hot_reload: 是否启用热加载
            hot_reload_debounce: 热加载防抖时间（秒）
            timeout_seconds: 处理超时时间（秒）
            max_sql_size_mb: 最大SQL大小（MB），超过此大小会拒绝处理
            enable_sampling: 是否启用采样检查
            sampling_threshold_kb: 采样阈值（KB），超过此大小启用采样
            cache_size: 缓存大小
            sql_dialect: SQL方言，支持ansi、hive、sparksql、oracle、mysql、postgres等
        """
        # 规则目录路径
        self.rules_dir = str(Path(__file__).parent.parent / "rules")
        
        # 预处理器目录路径
        self.preprocessors_dir = str(Path(self.rules_dir) / "preprocessors")
        
        # 优化参数
        self.timeout_seconds = timeout_seconds
        self.max_sql_size_mb = max_sql_size_mb
        self.enable_sampling = enable_sampling
        self.sampling_threshold_kb = sampling_threshold_kb
        self.cache_size = cache_size
        self.sql_dialect = sql_dialect
        
        # 热加载相关
        self.reload_lock = threading.Lock()
        self.enable_hot_reload = enable_hot_reload
        self.hot_reload_debounce = hot_reload_debounce
        
        # 文件监控器
        self.file_monitor = None
        
        # 缓存
        self.cache = {}
        self.cache_lock = threading.Lock()
        
        # 线程池用于超时控制
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 1. 初始加载预处理器
        self.preprocessor_manager = PreprocessorManager(self.preprocessors_dir)
        
        # 2. 初始加载规则
        self.custom_rules = self.load_rules_from_files()
        
        # 3. 初始化优化的SQLFluff配置
        self.config = self._create_optimized_config()
        
        # 4. 初始化Linter
        self.linter = Linter(config=self.config, user_rules=self.custom_rules)
        
        # 5. 如果启用热加载，启动监控
        if self.enable_hot_reload:
            self._start_file_monitor()
        
        logger.info(f"LintService初始化完成，超时时间: {timeout_seconds}秒，最大SQL大小: {max_sql_size_mb}MB")
    
    def _create_optimized_config(self) -> FluffConfig:
        """
        创建优化的SQLFluff配置
        
        优化点：
        1. 使用配置的SQL方言（默认ansi）
        2. 禁用不必要的规则
        3. 优化解析器设置
        4. 增加解析限制，避免长SQL解析失败
        """
        return FluffConfig(
            overrides={
                "dialect": self.sql_dialect,  # 使用配置的SQL方言
                "rules": "all",  # 使用所有规则
                # 禁用一些耗时的检查
                "max_line_length": 0,  # 禁用行长度检查
                "comma_style": "trailing",  # 简化逗号样式检查
                "indent_unit": "space",  # 简化缩进检查
                "tab_space_size": 4,
                # 解析器优化 - 增加限制避免长SQL解析失败
                "ignore": "",  # 不忽略任何语法
                "max_parse_depth": 1000,  # 增加最大解析深度（默认255）
                "rust_parser_max_iterations": 10000000,  # 增加Rust解析器迭代次数（默认300万）
                "large_file_skip_byte_limit": 100000,  # 增加大文件跳过限制（默认20000）
                "runaway_limit": 50,  # 增加失控限制（默认10）
            }
        )
    
    def _should_sample(self, sql_size_kb: float) -> bool:
        """
        判断是否应该使用采样检查
        
        Args:
            sql_size_kb: SQL大小（KB）
            
        Returns:
            是否启用采样
        """
        return (
            self.enable_sampling and 
            sql_size_kb > self.sampling_threshold_kb
        )
    
    def _sample_sql(self, sql: str, sample_ratio: float = 0.3) -> str:
        """
        对SQL进行采样，只检查部分内容
        
        Args:
            sql: 原始SQL
            sample_ratio: 采样比例（0-1）
            
        Returns:
            采样后的SQL
        """
        if not sql:
            return sql
        
        lines = sql.split('\n')
        total_lines = len(lines)
        
        if total_lines <= 10:
            # 行数太少，不采样
            return sql
        
        # 计算采样行数
        sample_lines = max(10, int(total_lines * sample_ratio))
        
        # 均匀采样：取开头、中间、结尾部分
        start_lines = lines[:sample_lines // 3]
        middle_start = total_lines // 2 - sample_lines // 6
        middle_end = total_lines // 2 + sample_lines // 6
        middle_lines = lines[middle_start:middle_end]
        end_lines = lines[-sample_lines // 3:]
        
        sampled_lines = start_lines + middle_lines + end_lines
        
        # 添加采样标记
        sampled_sql = '\n'.join(sampled_lines)
        sampled_sql += f"\n\n-- [SAMPLED] Original SQL size: {len(sql)} chars, sampled: {len(sampled_sql)} chars ({sample_ratio*100:.0f}%)"
        
        return sampled_sql
    
    def _get_sql_summary(self, sql: str, max_chars: int = 150) -> str:
        """
        生成SQL摘要，避免日志过大
        
        Args:
            sql: SQL字符串
            max_chars: 最大显示字符数
            
        Returns:
            SQL摘要字符串
        """
        if not sql:
            return "空SQL"
        
        length = len(sql)
        lines = sql.count('\n') + 1
        
        # 如果SQL很短，直接显示
        if length <= max_chars:
            return f"{length}字符/{lines}行: {sql}"
        
        # 对于长SQL，显示开头和结尾
        preview_start = sql[:max_chars//2]
        preview_end = sql[-max_chars//2:] if length > max_chars else ""
        
        return f"{length}字符/{lines}行: {preview_start}...{preview_end}"
    
    def _get_cache_key(self, sql: str) -> str:
        """
        生成缓存键
        
        Args:
            sql: SQL字符串
            
        Returns:
            缓存键
        """
        import hashlib
        # 使用MD5哈希作为缓存键
        return hashlib.md5(sql.encode('utf-8')).hexdigest()
    
    def _check_sql_size(self, sql: str) -> bool:
        """
        检查SQL大小是否超过限制
        
        Args:
            sql: SQL字符串
            
        Returns:
            是否超过限制
        """
        size_mb = len(sql) / 1024 / 1024
        if size_mb > self.max_sql_size_mb:
            logger.warning(f"SQL大小超过限制: {size_mb:.1f}MB > {self.max_sql_size_mb}MB")
            return False
        return True
    
    def lint_sql_with_timeout(self, sql: str) -> List[Dict[str, Any]]:
        """
        带超时的SQL lint检查
        
        Args:
            sql: SQL字符串
            
        Returns:
            lint结果列表，如果超时返回超时错误
        """
        # 记录SQL接收日志
        sql_summary = self._get_sql_summary(sql)
        logger.info(f"[SQL检查开始] SQL摘要: {sql_summary}")
        
        # 检查SQL大小
        if not self._check_sql_size(sql):
            size_mb = len(sql) / 1024 / 1024
            logger.warning(f"[SQL大小限制] SQL大小超过限制: {size_mb:.1f}MB > {self.max_sql_size_mb}MB")
            return [{
                "rule_id": "SIZE_LIMIT",
                "message": f"SQL大小超过限制 ({size_mb:.1f}MB > {self.max_sql_size_mb}MB)",
                "severity": "error",
                "line": 1,
                "column": 1
            }]
        
        # 生成缓存键
        cache_key = self._get_cache_key(sql)
        
        # 检查缓存
        with self.cache_lock:
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                logger.info(f"[缓存命中] 缓存键: {cache_key[:8]}...")
                if cached_result:
                    error_count = len([r for r in cached_result if r.get("severity") == "error"])
                    warning_count = len([r for r in cached_result if r.get("severity") == "warning"])
                    logger.info(f"[缓存命中] 使用缓存结果: {len(cached_result)}个问题 (错误: {error_count}, 警告: {warning_count})")
                return cached_result
        
        # 使用预处理器
        processed_sql = self.preprocessor_manager.process(sql)
        
        # 记录预处理日志
        if processed_sql != sql:
            processed_summary = self._get_sql_summary(processed_sql)
            logger.info(f"[SQL预处理] 处理后摘要: {processed_summary}")
        else:
            logger.info(f"[SQL预处理] 无变化")
        
        # 判断是否启用采样
        sql_size_kb = len(processed_sql) / 1024
        if self._should_sample(sql_size_kb):
            logger.info(f"[SQL采样] SQL大小 {sql_size_kb:.1f}KB > {self.sampling_threshold_kb}KB，启用采样检查")
            processed_sql = self._sample_sql(processed_sql)
            sampled_summary = self._get_sql_summary(processed_sql)
            logger.info(f"[SQL采样] 采样后摘要: {sampled_summary}")
        
        # 使用线程池执行带超时的lint检查
        future = self.executor.submit(self._lint_sql_internal, processed_sql)
        
        try:
            result = future.result(timeout=self.timeout_seconds)
            
            # 记录检查结果日志
            if result:
                error_count = len([r for r in result if r.get("severity") == "error"])
                warning_count = len([r for r in result if r.get("severity") == "warning"])
                logger.info(f"[SQL检查完成] 共发现{len(result)}个问题 (错误: {error_count}, 警告: {warning_count})")
                
                # 记录前5个问题（避免日志过大）
                for i, violation in enumerate(result[:5], 1):
                    logger.info(f"[问题{i}] {violation.get('rule_id')}: {violation.get('message')} (行{violation.get('line')})")
                
                if len(result) > 5:
                    logger.info(f"[更多问题] 还有{len(result)-5}个问题未显示")
            else:
                logger.info(f"[SQL检查完成] 未发现问题")
            
            # 缓存结果
            with self.cache_lock:
                if len(self.cache) >= self.cache_size:
                    # 移除最旧的缓存项
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                self.cache[cache_key] = result
            
            return result
            
        except FutureTimeoutError:
            logger.warning(f"[SQL检查超时] SQL lint检查超时 ({self.timeout_seconds}秒)")
            future.cancel()  # 取消任务
            
            return [{
                "rule_id": "TIMEOUT",
                "message": f"SQL lint检查超时 ({self.timeout_seconds}秒)，SQL大小: {len(sql)/1024:.1f}KB",
                "severity": "warning",
                "line": 1,
                "column": 1
            }]
            
        except Exception as e:
            logger.error(f"[SQL检查失败] 错误类型: {type(e).__name__}, 错误信息: {str(e)}")
            logger.error(f"[SQL检查失败] 失败SQL摘要: {self._get_sql_summary(sql)}")
            return [{
                "rule_id": "ERROR",
                "message": f"SQL lint检查失败: {str(e)}",
                "severity": "error",
                "line": 1,
                "column": 1
            }]
    
    def _lint_sql_internal(self, sql: str) -> List[Dict[str, Any]]:
        """
        内部lint检查方法（不带超时控制）
        
        Args:
            sql: 处理后的SQL字符串
            
        Returns:
            lint结果列表
        """
        with self.reload_lock:
            result = self.linter.lint_string(sql)
            return self._format_result(result)
    
    def lint_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        兼容原接口的lint方法
        
        Args:
            sql: SQL字符串
            
        Returns:
            lint结果列表
        """
        return self.lint_sql_with_timeout(sql)
    
    # 以下方法保持与原LintService兼容
    def _clear_rule_module_cache(self, changed_files=None):
        """
        清理发生变动的规则模块缓存
        
        Args:
            changed_files: 发生变动的文件列表（可选）
        """
        import sys
        
        # 规则模块前缀
        module_prefix = "app.rules"
        
        modules_to_delete = []
        
        # 收集所有需要清理的模块
        for module_name in list(sys.modules.keys()):
            if module_name == module_prefix or module_name.startswith(f"{module_prefix}."):
                if changed_files is None:
                    modules_to_delete.append(module_name)
                else:
                    # 只清理变动文件对应的模块
                    file_name = module_name[len(module_prefix) + 1:]
                    for file_path in changed_files:
                        from pathlib import Path
                        if Path(file_path).stem == file_name:
                            modules_to_delete.append(module_name)
                            break
        
        # 删除模块（包括父包，确保重新加载时完全刷新）
        for module_name in modules_to_delete:
            try:
                del sys.modules[module_name]
                logger.debug(f"已清理规则模块缓存: {module_name}")
            except Exception as e:
                logger.warning(f"清理规则模块缓存失败 {module_name}: {e}")
    
    def load_rules_from_files(self):
        """扫描规则目录，动态加载所有规则文件"""
        rules_list = []
        
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.py') and not filename.startswith('_') and not filename.endswith('.disabled'):
                module_name = filename[:-3]
                module_path = f"app.rules.{module_name}"
                
                try:
                    module = importlib.import_module(module_path)
                    rule_class_name = f"Rule_{module_name.split('_')[1].upper()}"
                    rule_class = getattr(module, rule_class_name)
                    rules_list.append(rule_class)
                    logger.info(f"规则加载成功: {rule_class.code}")
                except (ImportError, AttributeError) as e:
                    logger.error(f"加载规则失败: {filename}, 错误: {e}")
        return rules_list
    
    def reload_rules(self, changed_files=None):
        """
        重新加载所有规则
        
        Args:
            changed_files: 发生变动的文件列表（可选）
            
        Returns:
            是否成功
        """
        with self.reload_lock:
            try:
                logger.info("开始重新加载规则...")
                
                # 清理发生变动的规则模块缓存
                self._clear_rule_module_cache(changed_files)
                
                new_rules = self.load_rules_from_files()
                self.custom_rules = new_rules
                
                # 重新创建Linter
                self.linter = Linter(config=self.config, user_rules=self.custom_rules)
                
                # 清空缓存
                with self.cache_lock:
                    self.cache.clear()
                
                logger.info(f"规则重新加载完成，共加载 {len(new_rules)} 个规则: {[r.__name__ for r in new_rules]}")
                return True
            except Exception as e:
                logger.error(f"规则重新加载失败: {e}", exc_info=True)
                return False
    
    def get_loaded_rules(self):
        """获取当前加载的规则列表"""
        with self.reload_lock:
            return [rule.code for rule in self.custom_rules]
    
    def get_loaded_preprocessors(self):
        """获取当前加载的预处理器信息"""
        with self.reload_lock:
            if hasattr(self, 'preprocessor_manager'):
                return self.preprocessor_manager.get_preprocessors_info()
            return []
    
    def manual_reload(self):
        """手动触发规则重新加载"""
        return self.reload_rules()
    
    def stop_monitor(self):
        """停止文件监控"""
        if self.file_monitor:
            self.file_monitor.stop()
            self.file_monitor.join()
            logger.info("watchdog文件监控已停止")
    
    def _start_file_monitor(self):
        """启动文件监控"""
        self._start_watchdog_monitor()
    
    def _start_watchdog_monitor(self):
        """使用watchdog启动文件监控（支持多个目录）"""
        try:
            directories = {
                "rules": self.rules_dir,
                "preprocessors": self.preprocessors_dir
            }
            
            event_handler = MultiDirectoryEventHandler(
                service=self,
                directories=directories,
                debounce_seconds=self.hot_reload_debounce
            )
            
            self.file_monitor = WatchdogObserver()
            
            for dir_type, dir_path in directories.items():
                if os.path.exists(dir_path):
                    self.file_monitor.schedule(
                        event_handler,
                        dir_path,
                        recursive=False
                    )
                    logger.info(f"监控目录 [{dir_type}]: {dir_path}")
                else:
                    logger.warning(f"目录不存在，跳过监控: {dir_path}")
            
            self.file_monitor.start()
            logger.info(f"watchdog多目录文件监控已启动（防抖间隔: {self.hot_reload_debounce}秒）")
            
        except Exception as e:
            logger.error(f"启动watchdog监控失败: {e}")
            raise
    
    @staticmethod
    @staticmethod
    def _format_result(result):
        """将SQLFluff结果格式化为标准JSON"""
        formatted = []
        try:
            # 确保violations是可迭代的
            violations = result.violations
            if hasattr(violations, '__iter__'):
                for violation in violations:
                    # 过滤掉PRS错误和系统规则（只保留SS01、SS02、SS03）
                    rule_code = violation.rule_code()
                    if rule_code == "PRS":
                        continue
                    # 只保留自定义规则
                    if rule_code not in ["SS01", "SS02", "SS03"]:
                        continue
                    formatted.append({
                        "rule_id": rule_code,
                        "message": violation.desc(),
                        "severity": str(violation.warning),
                        "line": violation.line_no,
                        "column": getattr(violation, 'line_pos', 0)
                    })
            else:
                logger.warning(f"[_format_result] violations不是可迭代对象: {type(violations)}")
        except StopIteration:
            logger.error("[_format_result] 捕获到StopIteration异常，violations可能是一个已耗尽的迭代器")
            # 尝试重新获取violations
            try:
                # 如果是生成器，尝试转换为列表
                violations_list = list(result.violations)
                for violation in violations_list:
                    # 过滤掉PRS错误和系统规则（只保留SS01、SS02、SS03）
                    rule_code = violation.rule_code()
                    if rule_code == "PRS":
                        continue
                    # 只保留自定义规则
                    if rule_code not in ["SS01", "SS02", "SS03"]:
                        continue
                    formatted.append({
                        "rule_id": rule_code,
                        "message": violation.desc(),
                        "severity": str(violation.warning),
                        "line": violation.line_no,
                        "column": getattr(violation, 'line_pos', 0)
                    })
            except Exception as e2:
                logger.error(f"[_format_result] 重新获取violations失败: {type(e2).__name__}: {e2}")
        except Exception as e:
            logger.error(f"[_format_result] 格式化结果时发生错误: {type(e).__name__}: {e}")
            # 返回错误信息
            return [{
                "rule_id": "FORMAT_ERROR",
                "message": f"格式化结果时发生错误: {str(e)}",
                "severity": "error",
                "line": 1,
                "column": 1
            }]
        return formatted
    
    def __del__(self):
        """析构函数，确保监控线程被正确停止"""
        try:
            self.stop_monitor()
            self.executor.shutdown(wait=False)
        except:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        with self.cache_lock:
            cache_size = len(self.cache)
        
        return {
            "timeout_seconds": self.timeout_seconds,
            "max_sql_size_mb": self.max_sql_size_mb,
            "enable_sampling": self.enable_sampling,
            "sampling_threshold_kb": self.sampling_threshold_kb,
            "cache_size": cache_size,
            "cache_capacity": self.cache_size,
            "loaded_rules": len(self.custom_rules),
            "loaded_preprocessors": len(self.get_loaded_preprocessors())
        }