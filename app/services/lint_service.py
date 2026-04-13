import importlib
import logging
import os
import threading
import time

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig

logger = logging.getLogger(__name__)

class LintService:
    def __init__(self, enable_hot_reload=False):
        # 规则目录路径
        self.rules_dir = os.path.join(os.path.dirname(__file__), '..', 'rules')
        
        # 文件监控相关
        self.file_mod_times = {}  # 文件最后修改时间缓存
        self.reload_lock = threading.Lock()  # 重新加载锁
        self.enable_hot_reload = enable_hot_reload
        
        # 1. 初始加载规则
        self.custom_rules = self.load_rules_from_files()
        self._update_file_mod_times()

        # 2. 初始化SQLFluff配置
        self.config = FluffConfig(
            overrides={
                "dialect": "hive",
                "rules": "customer"
            }
        )
        
        # 3. 初始化Linter并传入自定义规则
        self.linter = Linter(config=self.config, user_rules=self.custom_rules)
        
        # 4. 如果启用热加载，启动监控线程
        if self.enable_hot_reload:
            self._start_file_monitor()

    def _update_file_mod_times(self):
        """更新文件修改时间缓存"""
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                filepath = os.path.join(self.rules_dir, filename)
                try:
                    mod_time = os.path.getmtime(filepath)
                    self.file_mod_times[filename] = mod_time
                except OSError:
                    pass
    
    def _check_files_changed(self):
        """检查文件是否发生变化"""
        changed_files = []
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                filepath = os.path.join(self.rules_dir, filename)
                try:
                    current_mod_time = os.path.getmtime(filepath)
                    old_mod_time = self.file_mod_times.get(filename)
                    
                    if old_mod_time is None or current_mod_time > old_mod_time:
                        changed_files.append(filename)
                        self.file_mod_times[filename] = current_mod_time
                except OSError:
                    pass
        return changed_files
    
    def _start_file_monitor(self):
        """启动文件监控线程"""
        def monitor_loop():
            while self.enable_hot_reload:
                try:
                    changed_files = self._check_files_changed()
                    if changed_files:
                        logger.info(f"检测到文件变化: {changed_files}")
                        self.reload_rules()
                    time.sleep(1)  # 每秒检查一次
                except Exception as e:
                    logger.error(f"文件监控错误: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("规则热加载监控已启动")
    
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
            result = self.linter.lint_string(sql)
            return self._format_result(result)
    
    def get_loaded_rules(self):
        """获取当前加载的规则列表"""
        with self.reload_lock:
            return [rule.code for rule in self.custom_rules]
    
    def manual_reload(self):
        """手动触发规则重新加载"""
        return self.reload_rules()

    def _format_result(self, result):
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
