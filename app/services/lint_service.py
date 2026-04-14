# coding=utf-8
import importlib
import logging
import os
import re
import threading
from pathlib import Path

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig
from watchdog.observers import Observer as WatchdogObserver

# 导入本地事件处理器
from app.services.event_handlers import RuleFileEventHandler

logger = logging.getLogger(__name__)


class LintService:
    def __init__(self, enable_hot_reload=False, hot_reload_debounce: float = 0.5):
        # 规则目录路径
        self.rules_dir = str(Path(__file__).parent.parent / "rules")
        
        # 热加载相关
        self.reload_lock = threading.Lock()  # 重新加载锁
        self.enable_hot_reload = enable_hot_reload
        self.hot_reload_debounce = hot_reload_debounce
        
        # 文件监控器
        self.file_monitor = None
        
        # 1. 初始加载规则
        self.custom_rules = self.load_rules_from_files()

        # 2. 初始化SQLFluff配置
        # 使用最简单的配置，仅设置dialect和rules
        self.config = FluffConfig(
            overrides={
                "dialect": "hive",
                "rules": "customer"
            }
        )
        
        # 3. 初始化Linter并传入自定义规则
        self.linter = Linter(config=self.config, user_rules=self.custom_rules)
        
        # 4. 如果启用热加载，启动监控
        if self.enable_hot_reload:
            self._start_file_monitor()
    
    def _start_file_monitor(self):
        """启动文件监控"""
        self._start_watchdog_monitor()
    
    def _start_watchdog_monitor(self):
        """使用watchdog启动文件监控"""
        try:
            event_handler = RuleFileEventHandler(
                service=self,
                debounce_seconds=self.hot_reload_debounce
            )
            
            self.file_monitor = WatchdogObserver()
            self.file_monitor.schedule(
                event_handler,
                self.rules_dir,
                recursive=False  # 只监控当前目录，不递归
            )
            self.file_monitor.start()
            
            logger.info(f"watchdog文件监控已启动（防抖间隔: {self.hot_reload_debounce}秒）")
            logger.info(f"监控目录: {self.rules_dir}")
            
        except Exception as e:
            logger.error(f"启动watchdog监控失败: {e}")
            raise
    
    def load_rules_from_files(self):
        """扫描规则目录，动态加载所有规则文件"""
        rules_list = []
        
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.py') and not filename.startswith('_') and not filename.endswith('.disabled'):
                # 获取规则模块名（如"rule_ss01"）
                module_name = filename[:-3]  # 去掉.py后缀
                module_path = f"app.rules.{module_name}"

                try:
                    # 动态导入模块
                    module = importlib.import_module(module_path)
                    # 获取模块中的规则类（如rule_ss01.Rule_SS01）
                    rule_class_name = f"Rule_{module_name.split('_')[1].upper()}"
                    rule_class = getattr(module, rule_class_name)

                    # 添加规则类到列表
                    rules_list.append(rule_class)
                    logger.info(f"规则加载成功: {rule_class.code}")
                except (ImportError, AttributeError) as e:
                    logger.error(f"加载规则失败: {filename}, 错误: {e}")
        return rules_list
    
    def reload_rules(self):
        """重新加载所有规则"""
        with self.reload_lock:
            try:
                logger.info("开始重新加载规则...")
                
                # 重新加载规则
                new_rules = self.load_rules_from_files()
                
                # 创建新的Linter实例
                new_linter = Linter(config=self.config, user_rules=new_rules)
                
                # 原子性更新
                self.custom_rules = new_rules
                self.linter = new_linter
                
                logger.info(f"规则重新加载完成，共加载 {len(new_rules)} 个规则")
                return True
            except Exception as e:
                logger.error(f"规则重新加载失败: {e}")
                return False

    def lint_sql(self, sql: str) -> list:
        """执行SQL lint，返回格式化结果"""
        with self.reload_lock:
            # 预处理：过滤掉SQLFluff无法解析的Hive SET语句
            processed_sql = self._preprocess_sql(sql)
            result = self.linter.lint_string(processed_sql)
            return self._format_result(result)
    
    @staticmethod
    def _preprocess_sql(sql: str) -> str:
        """
        预处理SQL：
        1. 过滤掉SQLFluff无法解析的Hive SET语句
        2. 过滤掉所有SET配置语句（避免规则误判）
        
        这些语句会被替换为空行，保留原始行号
        因为它们会导致解析错误或规则误判，且不影响业务逻辑
        """
        if not sql:
            return sql
        
        lines = sql.split('\n')
        processed_lines = []
        
        # 需要完全过滤的语句模式
        filter_patterns = [
            # 1. SQLFluff无法解析的Hive SET语句（避免PRS错误）
            r'^\s*set\s+hive\.exec\.dynamic\.partition\.mode\s*=',
            r'^\s*set\s+tez\.queue\.name\s*=',
            r'^\s*set\s+hive\.exec\.parallel\s*=',
            r'^\s*set\s+hive\.exec\.parallel\.thread\.number\s*=',
            r'^\s*set\s+hive\.vectorized\.execution\.enabled\s*=',
            r'^\s*set\s+hive\.vectorized\.execution\.reduce\.enabled\s*=',
            r'^\s*set\s+hive\.cbo\.enable\s*=',
            r'^\s*set\s+hive\.compute\.query\.using\.stats\s*=',
            r'^\s*set\s+hive\.stats\.fetch\.column\.stats\s*=',
            r'^\s*set\s+hive\.stats\.fetch\.partition\.stats\s*=',
            
            # 包含特定值的SET语句
            r'^\s*set\s+.*=.*nonstrict',
            r'^\s*set\s+.*=.*default',
            r'^\s*set\s+.*=.*none',
            
            # 其他已知有问题的模式
            r'^\s*set\s+.*\.mode\s*=',
            r'^\s*set\s+.*\.name\s*=',
            r'^\s*set\s+.*\.enabled\s*=',
            
            # 2. 所有SET配置语句（避免SS02/SS03规则误判）
            # 匹配所有SET语句，但排除UPDATE语句中的SET子句
            r'^\s*set\s+[a-zA-Z0-9_.:$]+\s*=',
        ]
        
        for line in lines:
            should_filter = False
            
            # 检查是否匹配需要过滤的模式
            for pattern in filter_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    should_filter = True
                    logger.debug(f"过滤语句: {line.strip()}")
                    break
            
            if should_filter:
                # 保留空行以维持行号
                processed_lines.append("")
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def get_loaded_rules(self):
        """获取当前加载的规则列表"""
        with self.reload_lock:
            return [rule.code for rule in self.custom_rules]
    
    def manual_reload(self):
        """手动触发规则重新加载"""
        return self.reload_rules()
    
    def stop_monitor(self):
        """停止文件监控"""
        if self.file_monitor:
            self.file_monitor.stop()
            self.file_monitor.join()
            logger.info("watchdog文件监控已停止")
    
    @staticmethod
    def _format_result(result):
        """将SQLFluff结果格式化为标准JSON"""
        formatted = []
        for violation in result.violations:
            formatted.append({
                "rule_id": violation.rule_code(),
                "message": violation.desc(),
                "severity": str(violation.warning),
                "line": violation.line_no,
                "column": getattr(violation, 'line_pos', 0)
            })
        return formatted
    
    def __del__(self):
        """析构函数，确保监控线程被正确停止"""
        try:
            self.stop_monitor()
        except:
            # 忽略析构函数中的错误
            pass