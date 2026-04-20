"""
预处理器抽象基类
定义所有预处理器的统一接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BasePreprocessor(ABC):
    """
    预处理器抽象基类
    
    所有预处理器必须继承此类并实现process方法
    通过order属性控制执行顺序（数值越小越先执行）
    """
    
    # 默认执行顺序（类属性）
    order: int = 100
    
    @abstractmethod
    def process(self, sql: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理SQL字符串
        
        Args:
            sql: 原始SQL字符串
            context: 上下文信息，可用于传递变量、配置等
            
        Returns:
            处理后的SQL字符串
            
        Raises:
            子类可以抛出特定异常，但建议捕获并记录日志后返回原始SQL
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取预处理器信息
        
        Returns:
            包含预处理器信息的字典
        """
        return {
            "name": self.__class__.__name__,
            "description": str(self),
            "order": self.order,
            "abstract_base": True
        }
    
    def __str__(self) -> str:
        """返回预处理器描述"""
        return self.__class__.__name__
    
    def __repr__(self) -> str:
        """返回预处理器表示"""
        return f"{self.__class__.__name__}(order={self.order})"
    
    @classmethod
    def validate_implementation(cls, preprocessor_class) -> bool:
        """
        验证预处理器类是否正确实现了抽象基类
        
        Args:
            preprocessor_class: 要验证的预处理器类
            
        Returns:
            是否有效实现
        """
        if not isinstance(preprocessor_class, type):
            return False
        
        # 检查是否继承自BasePreprocessor
        if not issubclass(preprocessor_class, BasePreprocessor):
            return False
        
        # 检查是否实现了抽象方法
        if not hasattr(preprocessor_class, 'process'):
            return False
        
        # 检查process方法是否可调用
        if not callable(getattr(preprocessor_class, 'process', None)):
            return False
        
        # 检查order属性是否存在且为整数
        if not hasattr(preprocessor_class, 'order'):
            return False
        
        order_value = getattr(preprocessor_class, 'order')
        if not isinstance(order_value, int):
            return False
        
        return True