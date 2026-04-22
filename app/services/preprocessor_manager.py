"""
预处理器管理器
管理所有SQL预处理器，按顺序执行预处理，支持热部署
"""

import os
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.rules.preprocessors.base_preprocessor import BasePreprocessor

logger = logging.getLogger(__name__)


class PreprocessorManager:
    """
    预处理器管理器
    
    功能：
    1. 动态加载预处理器
    2. 按order属性排序执行
    3. 提供预处理SQL的接口
    4. 支持热重载
    """
    
    def __init__(self, preprocessors_dir: str):
        """
        初始化预处理器管理器
        
        Args:
            preprocessors_dir: 预处理器目录路径
        """
        self.preprocessors_dir = preprocessors_dir
        self.preprocessors: List[Any] = []
        self._load_preprocessors()
    
    def _clear_module_cache(self, changed_files=None):
        """
        清理发生变动的预处理器模块缓存
        
        Args:
            changed_files: 发生变动的文件列表（可选），如果为None则清理所有
        """
        import sys
        
        # 预处理器相关模块前缀（包含父包）
        module_prefixes = ["app.rules.preprocessors", "app.rules"]
        
        modules_to_delete = []
        
        # 收集所有需要清理的模块
        for module_name in list(sys.modules.keys()):
            for prefix in module_prefixes:
                if module_name == prefix or module_name.startswith(f"{prefix}."):
                    if changed_files is None:
                        modules_to_delete.append(module_name)
                    else:
                        # 只清理变动文件对应的模块
                        file_name = module_name
                        if file_name.startswith("app.rules.preprocessors."):
                            file_name = file_name[len("app.rules.preprocessors."):]
                        elif file_name.startswith("app.rules."):
                            file_name = file_name[len("app.rules."):]
                        for file_path in changed_files:
                            if Path(file_path).stem == file_name:
                                modules_to_delete.append(module_name)
                                break
                    break
        
        # 删除模块
        for module_name in modules_to_delete:
            try:
                del sys.modules[module_name]
                logger.debug(f"已清理模块缓存: {module_name}")
            except Exception as e:
                logger.warning(f"清理模块缓存失败 {module_name}: {e}")
    
    def _load_preprocessors(self):
        """加载所有预处理器"""
        self.preprocessors.clear()
        
        try:
            # 确保目录存在
            preprocessors_path = Path(self.preprocessors_dir)
            if not preprocessors_path.exists():
                logger.warning(f"预处理器目录不存在: {self.preprocessors_dir}")
                return
            
            # 获取所有Python文件（排除__init__.py和以_开头的文件）
            py_files = [
                f for f in preprocessors_path.iterdir()
                if f.is_file() and f.suffix == '.py' 
                and f.name != '__init__.py' and not f.name.startswith('_')
            ]
            
            if not py_files:
                logger.info("未找到预处理器文件")
                return
            
            # 动态导入预处理器
            for py_file in py_files:
                try:
                    # 构建模块路径
                    module_name = f"app.rules.preprocessors.{py_file.stem}"
                    
                    # 导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找预处理器类（继承自BasePreprocessor的类）
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name != 'BasePreprocessor':
                            # 使用BasePreprocessor验证实现
                            if BasePreprocessor.validate_implementation(attr):
                                # 实例化预处理器
                                preprocessor = attr()
                                self.preprocessors.append(preprocessor)
                                logger.info(f"加载预处理器: {attr_name} (order={preprocessor.order})")
                            elif attr_name.endswith('Preprocessor'):
                                logger.warning(f"跳过无效预处理器类: {attr_name} (未正确实现BasePreprocessor)")
                            
                except Exception as e:
                    logger.error(f"加载预处理器 {py_file.name} 失败: {e}")
            
            # 按order属性排序（所有预处理器都有order属性）
            self.preprocessors.sort(key=lambda p: p.order)
            
            logger.info(f"共加载 {len(self.preprocessors)} 个预处理器")
            
        except Exception as e:
            logger.error(f"加载预处理器失败: {e}")
    
    def process(self, sql: str, context: Dict[str, Any] = None) -> str:
        """
        使用所有预处理器处理SQL
        
        Args:
            sql: 原始SQL字符串
            context: 上下文信息（可选）
            
        Returns:
            处理后的SQL字符串
        """
        if not sql:
            return sql
        
        processed_sql = sql
        
        # 按顺序执行所有预处理器
        for preprocessor in self.preprocessors:
            try:
                processed_sql = preprocessor.process(processed_sql, context)
            except Exception as e:
                logger.error(f"预处理器 {preprocessor.__class__.__name__} 执行失败: {e}")
                # 继续执行其他预处理器
        
        return processed_sql
    
    def get_preprocessors_info(self) -> List[Dict[str, Any]]:
        """
        获取所有预处理器的信息
        
        Returns:
            预处理器信息列表
        """
        info_list = []
        
        for preprocessor in self.preprocessors:
            try:
                # 所有预处理器都有get_info方法（来自BasePreprocessor）
                info = preprocessor.get_info()
                info_list.append(info)
            except Exception as e:
                logger.error(f"获取预处理器信息失败: {e}")
        
        return info_list
    
    def reload(self, changed_files=None):
        """
        重新加载预处理器
        
        Args:
            changed_files: 发生变动的文件列表（可选）
            
        Returns:
            加载后的预处理器数量
        """
        logger.info("重新加载预处理器...")
        
        # 清理发生变动的模块缓存
        self._clear_module_cache(changed_files)
        
        old_count = len(self.preprocessors)
        self._load_preprocessors()
        new_count = len(self.preprocessors)
        logger.info(f"预处理器重载完成: {old_count} -> {new_count}")
        return new_count
    
    def __len__(self):
        """返回预处理器数量"""
        return len(self.preprocessors)
    
    def __str__(self):
        """返回管理器描述"""
        return f"PreprocessorManager ({len(self)} preprocessors)"