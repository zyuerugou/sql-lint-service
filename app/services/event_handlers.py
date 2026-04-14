# coding=utf-8
"""
事件处理器模块
包含watchdog文件监控相关的事件处理器类
"""

import logging
import os
import threading
import time
from typing import List, Set

# 导入watchdog事件处理器
from watchdog.events import FileSystemEventHandler, FileSystemEvent

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
        # 确保src_path是字符串类型
        src_path = event.src_path.decode('utf-8') if isinstance(event.src_path, bytes) else event.src_path
        
        if not event.is_directory and src_path.endswith('.py'):
            filename = os.path.basename(src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                with self.lock:
                    self.pending_changes.add(filename)
                    current_time = time.time()
                    
                    # 防抖处理：避免短时间内多次触发
                    if current_time - self.last_reload_time >= self.debounce_seconds:
                        self._schedule_reload()
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件处理"""
        # 确保src_path是字符串类型
        src_path = event.src_path.decode('utf-8') if isinstance(event.src_path, bytes) else event.src_path
        
        if not event.is_directory and src_path.endswith('.py'):
            filename = os.path.basename(src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                with self.lock:
                    self.pending_changes.add(filename)
                    current_time = time.time()
                    
                    if current_time - self.last_reload_time >= self.debounce_seconds:
                        self._schedule_reload()
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件处理"""
        # 确保src_path是字符串类型
        src_path = event.src_path.decode('utf-8') if isinstance(event.src_path, bytes) else event.src_path
        
        if not event.is_directory and src_path.endswith('.py'):
            filename = os.path.basename(src_path)
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


