# coding=utf-8
"""
事件处理器模块
包含文件监控相关的事件处理器类
"""

import logging
import os
import threading
import time
from typing import List, Set

# 尝试导入watchdog，如果不可用则回退到轮询模式
try:
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # 创建虚拟类以便代码可以编译
    class FileSystemEventHandler:
        pass
    class FileSystemEvent:
        pass

logger = logging.getLogger(__name__)


class RuleFileEventHandler(FileSystemEventHandler):
    """规则文件事件处理器"""
    
    def __init__(self, service, debounce_seconds: float = 0.5):
        self.service = service
        self.debounce_seconds = debounce_seconds
        self.last_reload_time = 0
        self.pending_changes: Set[str] = set()
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
    """轮询文件监控器（watchdog不可用时的回退方案）"""
    
    def __init__(self, service, poll_interval: float = 1.0):
        self.service = service
        self.poll_interval = poll_interval
        self.running = False
        self.monitor_thread = None
        self.last_check_time = 0
        self.file_timestamps = {}
        
    def start(self):
        """启动轮询监控"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("轮询文件监控已启动")
    
    def stop(self):
        """停止轮询监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("轮询文件监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_for_changes()
            except Exception as e:
                logger.error(f"轮询监控出错: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_for_changes(self):
        """检查文件变化"""
        rules_dir = self.service.rules_dir
        if not os.path.exists(rules_dir):
            return
        
        current_time = time.time()
        changed_files = []
        
        # 扫描规则目录
        for filename in os.listdir(rules_dir):
            if filename.endswith('.py') and not filename.startswith('_') and not filename.endswith('.disabled'):
                filepath = os.path.join(rules_dir, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    
                    if filename in self.file_timestamps:
                        if mtime > self.file_timestamps[filename]:
                            changed_files.append(filename)
                            self.file_timestamps[filename] = mtime
                    else:
                        # 新文件
                        changed_files.append(filename)
                        self.file_timestamps[filename] = mtime
                except OSError:
                    # 文件可能被删除或无法访问
                    if filename in self.file_timestamps:
                        del self.file_timestamps[filename]
                        changed_files.append(filename)
        
        # 如果有变化，触发重新加载
        if changed_files and current_time - self.last_check_time >= 1.0:
            self.last_check_time = current_time
            if changed_files:
                logger.info(f"轮询检测到文件变化，触发重新加载: {changed_files}")
                self.service.reload_rules()