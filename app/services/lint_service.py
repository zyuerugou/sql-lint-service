#!/usr/bin/env python3
# coding=utf-8
"""
基于动态加载sqlglot规则的LintService
使用与原有LintService相同的规则加载模式
"""

import logging
import time
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import sqlglot
import sqlglot.expressions as exp
import sqlglot.errors

from app.rules.sqlglot_base import SQLGlotRuleLoader
from app.services.preprocessor_manager import PreprocessorManager
from app.utils.position_recorder import PositionRecorder

logger = logging.getLogger(__name__)


class LintService:
    """
    基于动态加载sqlglot规则的LintService
    
    特点：
    1. 使用与原有LintService相同的规则加载模式
    2. 动态加载sqlglot规则文件
    3. 支持热加载规则
    4. 保持API完全兼容
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
        sql_dialect: str = "hive",
        rules_dir: Optional[str] = None
    ):
        """
        初始化LintService
        
        Args:
            enable_hot_reload: 是否启用热加载
            hot_reload_debounce: 热加载防抖间隔（秒）
            timeout_seconds: SQL解析超时时间（秒）
            max_sql_size_mb: 最大SQL大小（MB）
            enable_sampling: 是否启用采样
            sampling_threshold_kb: 采样阈值（KB）
            cache_size: 缓存大小
            sql_dialect: SQL方言
            rules_dir: 规则目录路径，默认为app/rules
        """
        self.enable_hot_reload = enable_hot_reload
        self.hot_reload_debounce = hot_reload_debounce
        self.timeout_seconds = timeout_seconds
        self.max_sql_size_mb = max_sql_size_mb
        self.enable_sampling = enable_sampling
        self.sampling_threshold_kb = sampling_threshold_kb
        self.cache_size = cache_size
        self.sql_dialect = sql_dialect
        
        # 规则目录
        if rules_dir:
            self.rules_dir = rules_dir
        else:
            self.rules_dir = str(Path(__file__).parent.parent / "rules")
        
        # 预处理器目录
        self.preprocessors_dir = str(Path(self.rules_dir) / "preprocessors")
        
        # 初始化组件
        self.rule_loader = SQLGlotRuleLoader(self.rules_dir)
        self.preprocessor_manager = PreprocessorManager(self.preprocessors_dir)
        
        # 缓存
        self.cache = {}
        self.cache_lock = threading.Lock()
        
        # 热加载监控
        self.monitor_thread = None
        self.stop_monitor_event = threading.Event()
        
        # 加载规则
        self.rules = self.rule_loader.load_rules_from_files()
        logger.info(f"初始化LintService，加载了{len(self.rules)}个规则")
        
        # 启动热加载监控
        if self.enable_hot_reload:
            self.start_monitor()
    
    def lint_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        检查SQL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            检查结果列表，每个元素包含rule_id, message, severity, line, column
        """
        # 记录开始检查
        sql_preview = sql[:100] + "..." if len(sql) > 100 else sql
        logger.info(f"开始检查SQL (长度: {len(sql)} 字符): {sql_preview}")
        
        # 检查SQL大小
        sql_size_mb = len(sql.encode('utf-8')) / (1024 * 1024)
        if sql_size_mb > self.max_sql_size_mb:
            error_msg = f'SQL太大({sql_size_mb:.2f}MB)，超过限制({self.max_sql_size_mb}MB)'
            logger.warning(f"SQL大小超过限制: {error_msg}")
            return [{
                'rule_id': 'SIZE_ERROR',
                'message': error_msg,
                'severity': 'error',
                'line': 1,
                'column': 1
            }]
        
        # 检查缓存
        cache_key = f"{self.sql_dialect}:{sql}"
        with self.cache_lock:
            if cache_key in self.cache:
                logger.debug(f"从缓存返回结果 (缓存键: {hash(cache_key)})")
                return self.cache[cache_key]
        
        try:
            # 预处理SQL
            logger.debug("开始预处理SQL")
            processed_sql = self.preprocessor_manager.process(sql)
            if processed_sql != sql:
                logger.debug(f"SQL预处理完成，原始长度: {len(sql)}，处理后长度: {len(processed_sql)}")
            
            # 解析SQL
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._parse_and_check, processed_sql)
                try:
                    result = future.result(timeout=self.timeout_seconds)
                except FutureTimeoutError:
                    return [{
                        'rule_id': 'TIMEOUT_ERROR',
                        'message': f'SQL解析超时（超过{self.timeout_seconds}秒）',
                        'severity': 'error',
                        'line': 1,
                        'column': 1
                    }]
            
            # 记录检查结果摘要
            if result:
                error_count = sum(1 for item in result if item.get('severity') == 'error')
                warning_count = sum(1 for item in result if item.get('severity') == 'warning')
                logger.info(f"SQL检查完成: 发现 {len(result)} 个问题 (错误: {error_count}, 警告: {warning_count})")
                
                # 记录前几个问题的详细信息
                for i, item in enumerate(result[:3]):
                    logger.info(f"  问题 {i+1}: [{item.get('severity')}] {item.get('rule_id')} - {item.get('message')}")
                if len(result) > 3:
                    logger.info(f"  还有 {len(result)-3} 个问题未显示")
            else:
                logger.info("SQL检查完成: 未发现问题")
            
            # 更新缓存
            with self.cache_lock:
                if len(self.cache) >= self.cache_size:
                    # 移除最旧的缓存项
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    logger.debug(f"缓存已满，移除最旧缓存项: {hash(oldest_key)}")
                self.cache[cache_key] = result
                logger.debug(f"结果已缓存 (缓存键: {hash(cache_key)})")
            
            return result
            
        except Exception as e:
            logger.error(f"SQL检查异常: {type(e).__name__}: {e}")
            return [{
                'rule_id': 'PARSE_ERROR',
                'message': f'SQL解析异常: {str(e)[:100]}',
                'severity': 'error',
                'line': 1,
                'column': 1
            }]
    
    def _parse_and_check(self, sql: str) -> List[Dict[str, Any]]:
        """解析SQL并检查规则"""
        # 采样：对于大SQL，只检查部分
        if self.enable_sampling and len(sql) > self.sampling_threshold_kb * 1024:
            sample_size = self.sampling_threshold_kb * 1024
            sql_to_parse = sql[:sample_size] + "... [采样]"
            logger.info(f"SQL过大({len(sql)} 字符 > {self.sampling_threshold_kb}KB)，启用采样，只检查前{sample_size}字符")
        else:
            sql_to_parse = sql
        
        # 解析SQL - 使用位置记录器解析并记录位置
        try:
            logger.debug(f"开始解析SQL (方言: {self.sql_dialect})")
            asts = PositionRecorder.parse_with_positions(sql_to_parse, self.sql_dialect)
            logger.debug(f"SQL解析成功，得到{len(asts)}个语句")
            
            # 如果没有解析出任何语句，可能SQL是空的或只有注释
            if not asts:
                logger.debug("SQL为空或只包含注释")
                return []
                
        except sqlglot.errors.ParseError as e:
            logger.error(f"SQL解析失败: {type(e).__name__}: {e}")
            
            # 从sqlglot错误中提取位置信息
            line = 1
            column = 1
            error_message = str(e).split(".")[0]  # 提取主要错误信息
            
            if hasattr(e, 'errors') and e.errors:
                # 取第一个错误的位置
                first_error = e.errors[0]
                line = first_error.get('line', 1)
                column = first_error.get('col', 1)
                
                # 使用错误描述作为主要错误信息
                error_desc = first_error.get('description', '')
                if error_desc:
                    error_message = error_desc
                else:
                    # 如果没有描述，使用原始错误信息
                    error_message = str(e).split(".")[0]
            
            # 清理错误信息，移除重复部分
            if error_message and ":" in error_message:
                # 如果已经有冒号分隔，取最后一部分
                parts = error_message.split(":")
                if len(parts) > 1:
                    error_message = parts[-1].strip()
            
            # 限制长度
            error_message = error_message[:100]
            
            # 尝试确定是哪个语句出错
            statement_num = 1
            if sql_to_parse:
                # 计算错误位置之前的语句数量
                lines = sql_to_parse.split('\n')
                # 计算到错误行的字符数
                char_count = 0
                for i in range(line - 1):
                    if i < len(lines):
                        char_count += len(lines[i]) + 1  # +1 for newline
                
                # 在错误位置之前查找分号
                text_before_error = sql_to_parse[:char_count + column - 1]
                # 分号数量+1就是语句编号
                statement_num = text_before_error.count(';') + 1
            
            # 当有语法错误时，只返回语法错误，不进行规则检查
            return [{
                'rule_id': 'PARSE_ERROR',
                'message': f'SQL语法错误（第{statement_num}个语句）: {error_message}',
                'severity': 'error',
                'line': line,
                'column': column
            }]
        except Exception as e:
            logger.error(f"SQL解析失败: {type(e).__name__}: {e}")
            return [{
                'rule_id': 'PARSE_ERROR',
                'message': f'SQL解析失败: {str(e)[:100]}',
                'severity': 'error',
                'line': 1,
                'column': 1
            }]
        
        # 应用所有规则 - 对每个语句分别检查
        violations = []
        rule_stats = {}
        
        # 将多个语句合并成一个大的AST进行规则检查
        # 注意：某些规则可能需要针对单个语句检查，但大多数规则应该能处理
        if asts:
            # 如果有多个语句，创建一个组合的AST
            if len(asts) > 1:
                # 分别检查每个语句，但跳过注释等非实质性AST
                for i, ast in enumerate(asts):
                    # 跳过注释等非实质性AST
                    if self._should_skip_ast(ast):
                        logger.debug(f"跳过非实质性AST {i+1}: {type(ast).__name__}")
                        continue
                    else:
                        logger.debug(f"检查实质性AST {i+1}: {type(ast).__name__}")
                        
                        for rule in self.rules:
                            try:
                                # 为每个语句应用规则
                                rule_violations = rule.check(ast, sql_to_parse)
                                if rule_violations:
                                    rule_stats[rule.code] = rule_stats.get(rule.code, 0) + len(rule_violations)
                                    violations.extend(rule_violations)
                            except Exception as e:
                                logger.error(f"规则{rule.code}检查语句{i+1}异常: {type(e).__name__}: {e}")
            else:
                # 只有一个语句
                ast = asts[0]
                # 检查是否应该跳过
                if not self._should_skip_ast(ast):
                    for rule in self.rules:
                        try:
                            rule_violations = rule.check(ast, sql_to_parse)
                            if rule_violations:
                                rule_stats[rule.code] = len(rule_violations)
                                logger.debug(f"规则 {rule.code} 发现 {len(rule_violations)} 个问题")
                                violations.extend(rule_violations)
                        except Exception as e:
                            logger.error(f"规则{rule.code}检查异常: {type(e).__name__}: {e}")
        
        # 记录规则检查统计
        if rule_stats:
            stats_str = ", ".join([f"{rule}:{count}" for rule, count in rule_stats.items()])
            logger.info(f"规则检查完成，发现 {len(violations)} 个问题 ({stats_str})")
        else:
            logger.info("规则检查完成，未发现问题")
        
        # 转换为字典格式
        result = []
        for violation in violations:
            result.append({
                'rule_id': violation.rule_id,
                'message': violation.message,
                'severity': violation.severity,
                'line': violation.line,
                'column': violation.column
            })
        
        return result
    
    def get_loaded_rules(self) -> List[str]:
        """获取已加载的规则代码列表"""
        return list(self.rule_loader.loaded_rules.keys())
    
    def get_loaded_preprocessors(self) -> List[str]:
        """获取已加载的预处理器列表"""
        preprocessors_info = self.preprocessor_manager.get_preprocessors_info()
        return [info.get("name", "Unknown") for info in preprocessors_info]
    
    def reload_rules(self) -> bool:
        """重新加载规则和预处理器"""
        try:
            # 重新加载规则
            self.rules = self.rule_loader.reload_rules()
            logger.info(f"规则重新加载成功，当前加载{len(self.rules)}个规则")
            
            # 重新加载预处理器
            preprocessor_count = self.preprocessor_manager.reload()
            logger.info(f"预处理器重新加载成功，当前加载{preprocessor_count}个预处理器")
            
            return True
        except Exception as e:
            logger.error(f"重新加载失败: {type(e).__name__}: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            'service_type': self.__class__.__name__,
            'dialect': self.sql_dialect,
            'timeout_seconds': self.timeout_seconds,
            'max_sql_size_mb': self.max_sql_size_mb,
            'enable_sampling': self.enable_sampling,
            'sampling_threshold_kb': self.sampling_threshold_kb,
            'cache_size': self.cache_size,
            'loaded_rules': self.get_loaded_rules(),
            'rules_dir': self.rules_dir,
            'cache_usage': len(self.cache)
        }
    
    def start_monitor(self):
        """启动规则和预处理器文件监控"""
        if not self.enable_hot_reload:
            return
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class FileChangeHandler(FileSystemEventHandler):
                def __init__(self, service):
                    self.service = service
                    self.last_reload_time = 0
                
                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith('.py'):
                        current_time = time.time()
                        if current_time - self.last_reload_time > self.service.hot_reload_debounce:
                            self.last_reload_time = current_time
                            logger.info(f"检测到文件变化: {event.src_path}")
                            
                            # 判断是规则文件还是预处理器文件
                            # 使用更精确的路径判断：检查是否在preprocessors目录中
                            import os
                            src_path = event.src_path.replace('\\', '/')
                            
                            # 检查路径中是否包含/preprocessors/目录
                            if '/preprocessors/' in src_path or '\\preprocessors\\' in src_path:
                                # 预处理器文件变化，重新加载预处理器
                                logger.info(f"检测到预处理器文件变化: {event.src_path}")
                                self.service.preprocessor_manager.reload()
                                logger.info("预处理器重新加载完成")
                            else:
                                # 规则文件变化，重新加载规则
                                logger.info(f"检测到规则文件变化: {event.src_path}")
                                self.service.reload_rules()
            
            self.stop_monitor_event.clear()
            event_handler = FileChangeHandler(self)
            observer = Observer()
            
            # 监控规则目录
            observer.schedule(event_handler, self.rules_dir, recursive=True)
            logger.info(f"启动规则文件监控，目录: {self.rules_dir}")
            
            # 监控预处理器目录
            observer.schedule(event_handler, self.preprocessors_dir, recursive=True)
            logger.info(f"启动预处理器文件监控，目录: {self.preprocessors_dir}")
            
            observer.start()
            self.monitor_thread = observer
            
        except ImportError:
            logger.warning("未安装watchdog，无法启用热加载")
        except Exception as e:
            logger.error(f"启动监控失败: {type(e).__name__}: {e}")
    
    def stop_monitor(self):
        """停止规则文件监控"""
        if self.monitor_thread:
            self.stop_monitor_event.set()
            self.monitor_thread.stop()
            self.monitor_thread.join()
            self.monitor_thread = None
            logger.info("规则文件监控已停止")
    
    def _should_skip_ast(self, ast) -> bool:
        """
        检查是否应该跳过对某个AST的规则检查
        
        Args:
            ast: sqlglot AST
            
        Returns:
            True如果应该跳过，否则False
        """
        import sqlglot.expressions as exp
        
        # 跳过注释、分号等非实质性AST
        skip_types = {
            exp.Semicolon,  # 分号（通常包含注释）
            exp.Comment,    # 注释
        }
        
        for skip_type in skip_types:
            if isinstance(ast, skip_type):
                return True
        
        # 对于Command类型，检查是否是SET语句（应该由预处理器过滤）
        if isinstance(ast, exp.Command):
            command_str = str(ast).lower()
            if command_str.startswith('set '):
                logger.warning(f"发现未过滤的SET语句: {command_str}")
                # 仍然检查，但记录警告
        
        return False
    
    def __del__(self):
        """析构函数，确保监控线程被停止"""
        self.stop_monitor()

