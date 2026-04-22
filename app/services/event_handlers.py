# coding=utf-8
"""
事件处理器模块
包含watchdog文件监控相关的事件处理器类
"""

import logging
import os
import threading
import time
from typing import List, Set, Dict, Optional

# 导入watchdog事件处理器
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class MultiDirectoryEventHandler(FileSystemEventHandler):
    """
    多目录文件事件处理器
    支持监控多个目录，区分规则和预处理器变化
    """
    
    def __init__(self, service, directories: Dict[str, str], debounce_seconds: float = 0.5):
        """
        初始化多目录事件处理器
        
        Args:
            service: LintService实例
            directories: 目录映射，格式为 {"类型": "目录路径"}
            debounce_seconds: 防抖间隔（秒）
        """
        self.service = service
        self.directories = directories
        self.debounce_seconds = debounce_seconds
        
        # 记录每个目录的最后重载时间
        self.last_reload_times: Dict[str, float] = {dir_type: 0 for dir_type in directories}
        
        # 待处理的变化文件
        self.pending_changes: Dict[str, Set[str]] = {dir_type: set() for dir_type in directories}
        
        self.lock = threading.Lock()
    
    def _get_directory_type(self, filepath: str) -> Optional[str]:
        """根据文件路径确定所属目录类型"""
        for dir_type, dir_path in self.directories.items():
            if filepath.startswith(dir_path):
                return dir_type
        return None
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件处理"""
        self._handle_file_event(event, "修改")
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件处理"""
        self._handle_file_event(event, "创建")
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件处理"""
        self._handle_file_event(event, "删除")
    
    def _handle_file_event(self, event: FileSystemEvent, event_type: str):
        """处理文件事件"""
        # 确保src_path是字符串类型
        src_path = event.src_path.decode('utf-8') if isinstance(event.src_path, bytes) else event.src_path
        
        if not event.is_directory and src_path.endswith('.py'):
            filename = os.path.basename(src_path)
            if not filename.startswith('_') and not filename.endswith('.disabled'):
                
                # 确定文件所属目录类型
                dir_type = self._get_directory_type(src_path)
                if not dir_type:
                    logger.debug(f"文件不属于监控目录: {src_path}")
                    return
                
                with self.lock:
                    self.pending_changes[dir_type].add(filename)
                    current_time = time.time()
                    last_reload_time = self.last_reload_times[dir_type]
                    
                    # 防抖处理：避免短时间内多次触发
                    if current_time - last_reload_time >= self.debounce_seconds:
                        self._schedule_reload(dir_type)
                    
                    logger.debug(f"文件{event_type}: {filename} (目录类型: {dir_type})")
    
    def _schedule_reload(self, dir_type: str):
        """调度重新加载"""
        if self.pending_changes[dir_type]:
            changed_files = list(self.pending_changes[dir_type])
            self.pending_changes[dir_type].clear()
            self.last_reload_times[dir_type] = time.time()
            
            # 在单独的线程中执行重新加载，避免阻塞事件处理
            reload_thread = threading.Thread(
                target=self._execute_reload,
                args=(dir_type, changed_files),
                daemon=True
            )
            reload_thread.start()
    
    def _execute_reload(self, dir_type: str, changed_files: List[str]):
        """执行重新加载"""
        try:
            logger.info(f"检测到{dir_type}目录文件变化，触发重新加载: {changed_files}")
            
            if dir_type == "rules":
                # 重新加载规则
                self.service.reload_rules(changed_files)
            elif dir_type == "preprocessors":
                # 重新加载预处理器
                if hasattr(self.service, 'preprocessor_manager'):
                    self.service.preprocessor_manager.reload(changed_files)
                else:
                    logger.warning("服务没有预处理器管理器，无法重新加载预处理器")
            else:
                logger.warning(f"未知的目录类型: {dir_type}")
                
        except Exception as e:
            logger.error(f"{dir_type}重新加载失败: {e}")


# 向后兼容：保留旧的RuleFileEventHandler
class RuleFileEventHandler(MultiDirectoryEventHandler):
    """规则文件事件处理器（向后兼容）"""
    
    def __init__(self, service, debounce_seconds: float = 0.5):
        # 只监控规则目录
        directories = {"rules": service.rules_dir}
        super().__init__(service, directories, debounce_seconds)


