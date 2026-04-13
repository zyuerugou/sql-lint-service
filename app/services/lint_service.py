# coding=utf-8
import importlib
import logging
import os
import threading
import time
from typing import List, Optional

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig

# 尝试导入watchdog，如果不可用则回退到轮询模式
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # 创建虚拟类以便代码可以编译
    class FileSystemEventHandler:
        pass
    class FileSystemEvent:
        pass
    Observer = None

logger = logging.getLogger(__name__)


class RuleFileEventHandler(FileSystemEventHandler):
    """规则文件事件处理器"""
    
    def __init__(self, service, debounce_seconds: float = 0.5):
        self.service = service
        self.debounce_seconds = debounce_seconds
        self.last_reload_time = 0
        self.pending_changes = set()
        self.lock = threading.Lock()
        
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件处理"""
        if not event.is_directory and event.src_path.endswith('.py'):
            filename = os.path.basename(event.src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                with self.lock:
                    self.pending_changes.add(filename)
                    current_time = time.time()
                    
                    # 防抖处理：避免短时间内多次触发
                    if current_time - self.last_reload_time >= self.debounce_seconds:
                        self._schedule_reload()
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件处理"""
        if not event.is_directory and event.src_path.endswith('.py'):
            filename = os.path.basename(event.src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                with self.lock:
                    self.pending_changes.add(filename)
                    current_time = time.time()
                    
                    if current_time - self.last_reload_time >= self.debounce_seconds:
                        self._schedule_reload()
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件处理"""
        if not event.is_directory and event.src_path.endswith('.py'):
            filename = os.path.basename(event.src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                with self.lock:
                    self.pending_changes.add(filename)
                    current_time = time.time()
                    
                    if current_time - self.last_reload_time >= self.debounce_seconds:
                        self._schedule_reload()
    
    def _schedule_reload(self):
        """调度规则重新加载"""
        if self.pending_changes:
            changed_files = list(self.pending_changes)
            self.pending_changes.clear()
            self.last_reload_time = time.time()
            
            # 在单独的线程中执行重新加载，避免阻塞事件处理
            reload_thread = threading.Thread(
                target=self._execute_reload,
                args=(changed_files,),
                daemon=True
            )
            reload_thread.start()
    
    def _execute_reload(self, changed_files: List[str]):
        """执行规则重新加载"""
        try:
            logger.info(f"检测到文件变化，触发重新加载: {changed_files}")
            self.service.reload_rules()
        except Exception as e:
            logger.error(f"规则重新加载失败: {e}")


class PollingFileMonitor:
    """轮询模式文件监控器（watchdog不可用时的备选方案）"""
    
    def __init__(self, service, poll_interval: float = 2.0):
        self.service = service
        self.poll_interval = poll_interval
        self.file_mod_times = {}
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def start(self):
        """启动轮询监控"""
        if self.running:
            return
            
        self.running = True
        self._update_file_mod_times()
        
        def monitor_loop():
            while self.running:
                try:
                    changed_files = self._check_files_changed()
                    if changed_files:
                        logger.info(f"检测到文件变化: {changed_files}")
                        self.service.reload_rules()
                    time.sleep(self.poll_interval)
                except Exception as e:
                    logger.error(f"文件监控错误: {e}")
                    time.sleep(5)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"轮询模式文件监控已启动（间隔: {self.poll_interval}秒）")
    
    def stop(self):
        """停止轮询监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _update_file_mod_times(self):
        """更新文件修改时间缓存"""
        rules_dir = self.service.rules_dir
        for filename in os.listdir(rules_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                filepath = os.path.join(rules_dir, filename)
                try:
                    mod_time = os.path.getmtime(filepath)
                    self.file_mod_times[filename] = mod_time
                except OSError:
                    pass
    
    def _check_files_changed(self):
        """检查文件是否发生变化"""
        changed_files = []
        rules_dir = self.service.rules_dir
        
        for filename in os.listdir(rules_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                filepath = os.path.join(rules_dir, filename)
                try:
                    current_mod_time = os.path.getmtime(filepath)
                    old_mod_time = self.file_mod_times.get(filename)
                    
                    if old_mod_time is None or current_mod_time > old_mod_time:
                        changed_files.append(filename)
                        self.file_mod_times[filename] = current_mod_time
                except OSError:
                    pass
        
        return changed_files


class LintService:
    def __init__(self, enable_hot_reload=False, hot_reload_debounce: float = 0.5):
        # 规则目录路径
        self.rules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rules'))
        
        # 热加载相关
        self.reload_lock = threading.Lock()  # 重新加载锁
        self.enable_hot_reload = enable_hot_reload
        self.hot_reload_debounce = hot_reload_debounce
        
        # 文件监控器
        self.file_monitor: Optional[Observer] = None
        self.polling_monitor: Optional[PollingFileMonitor] = None
        
        # 1. 初始加载规则
        self.custom_rules = self.load_rules_from_files()

        # 2. 初始化SQLFluff配置
        # 从pyproject.toml读取配置
        import tomllib
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        config_path = os.path.join(project_root, 'pyproject.toml')
        
        # 默认配置
        config_dict = {
            "core": {
                "dialect": "hive",
                "templater": "jinja",
                "rules": "customer",  # 默认只启用customer规则组
                "exclude_rules": "LT01,LT02",
            },
            "indentation": {
                "tab_space_size": 4,
                "indented_joins": True
            }
        }
        
        # 如果存在pyproject.toml，读取配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'rb') as f:
                    data = tomllib.load(f)
                    sqlfluff_config = data.get('tool', {}).get('sqlfluff', {})
                    
                    # 更新配置
                    for key, value in sqlfluff_config.items():
                        if key == 'indentation':
                            config_dict['indentation'].update(value)
                        elif key in ['dialect', 'templater', 'exclude_rules']:
                            config_dict['core'][key] = value
                        # 注意：我们不从pyproject.toml读取rules，因为我们要强制使用customer规则组
            except Exception as e:
                logger.warning(f"读取pyproject.toml失败: {e}")
        
        self.config = FluffConfig(config_dict)
        
        # 3. 初始化Linter并传入自定义规则
        self.linter = Linter(config=self.config, user_rules=self.custom_rules)
        
        # 4. 如果启用热加载，启动监控
        if self.enable_hot_reload:
            self._start_file_monitor()
    
    def _start_file_monitor(self):
        """启动文件监控"""
        if WATCHDOG_AVAILABLE:
            self._start_watchdog_monitor()
        else:
            self._start_polling_monitor()
    
    def _start_watchdog_monitor(self):
        """使用watchdog启动文件监控"""
        try:
            event_handler = RuleFileEventHandler(
                service=self,
                debounce_seconds=self.hot_reload_debounce
            )
            
            self.file_monitor = Observer()
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
            logger.warning("回退到轮询模式")
            self._start_polling_monitor()
    
    def _start_polling_monitor(self):
        """启动轮询模式文件监控"""
        self.polling_monitor = PollingFileMonitor(
            service=self,
            poll_interval=max(1.0, self.hot_reload_debounce * 2)  # 轮询间隔稍长
        )
        self.polling_monitor.start()
    
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
    
    def stop_monitor(self):
        """停止文件监控"""
        if self.file_monitor:
            self.file_monitor.stop()
            self.file_monitor.join()
            logger.info("watchdog文件监控已停止")
        
        if self.polling_monitor:
            self.polling_monitor.stop()
            logger.info("轮询文件监控已停止")
    
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
    
    def __del__(self):
        """析构函数，确保监控线程被正确停止"""
        try:
            self.stop_monitor()
        except:
            # 忽略析构函数中的错误
            pass