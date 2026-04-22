# coding=utf-8
"""
SET语句过滤器预处理器
过滤掉SQL解析器无法解析的Hive SET语句和所有SET配置语句
"""

import re
import logging
from typing import Dict, Any, Optional

from .base_preprocessor import BasePreprocessor

logger = logging.getLogger(__name__)


class SetStatementFilterPreprocessor(BasePreprocessor):
    """
    SET语句过滤器预处理器
    
    功能：
    1. 过滤掉SQL解析器无法解析的Hive SET语句（避免解析错误）
    2. 过滤掉所有SET配置语句（避免规则误判）
    
    这些语句会被替换为空行，保留原始行号
    因为它们会导致解析错误或规则误判，且不影响业务逻辑
    """
    
    # 预处理器执行顺序
    order = 100
    
    def __init__(self):
        """初始化SET语句过滤器预处理器"""
        # 需要完全过滤的语句模式
        self.filter_patterns = [
            # 1. SQLFluff无法解析的Hive SET语句（避免PRS错误）
            r'^\s*set\s+hive\.exec.*\s*=',
            r'^\s*set\s+tez\.queue\.name\s*=',
            r'^\s*set\s+hive\.vectorized\.execution\.enabled\s*=',
            r'^\s*set\s+hive\.vectorized\.execution\.reduce\.enabled\s*=',
            r'^\s*set\s+hive\.cbo\.enable\s*=',
            r'^\s*set\s+hive\.compute\.query\.using\.stats\s*=',
            r'^\s*set\s+hive\.stats\.fetch\.column\.stats\s*=',
            r'^\s*set\s+hive\.stats\.fetch\.partition\.stats\s*=',
            r'^\s*set\s+hive\.default\.fileformat.*',
            r'^\s*set\s+hive\.enforce\.bucketing.*',
            r'^\s*set\s+hivevar\:prompt',
            r'^\s*set\s+character\.literal\.as\..*',
            r'^\s*set\s+ngmr\.partition\..*',
            
            # 包含特定值的SET语句
            r'^\s*set\s+.*=.*nonstrict',
            r'^\s*set\s+.*=.*default',
            r'^\s*set\s+.*=.*none',
            
            # 其他已知有问题的模式
            r'^\s*set\s+.*\.mode\s*=',
            r'^\s*set\s+.*\.name\s*=',
            r'^\s*set\s+.*\.enabled\s*=',
            
            # 2. 所有SET配置语句（避免SS02/SS03规则误判）
            # 注意：移除了宽泛模式，只保留具体的Hive SET模式
            # 原宽泛模式：r'^\s*set\s+[a-zA-Z0-9_.:$]+\s*=',
            # 这会错误过滤UPDATE语句中的SET子句，所以移除
        ]
    
    def process(self, sql: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理SQL，过滤SET语句
        
        Args:
            sql: 原始SQL字符串
            context: 上下文信息（可选）
            
        Returns:
            处理后的SQL字符串（保持原始行结构）
        """
        if not sql:
            return sql
        
        # 简单逐行处理：SET语句单独成行，直接替换为空行
        lines = sql.split('\n')
        processed_lines = []
        
        for line in lines:
            # 检查是否匹配SET语句模式
            if self._should_filter(line):
                # 替换为空行（保持行号）
                processed_lines.append("")
            else:
                # 保持原样
                processed_lines.append(line)
        
        # 返回处理后的SQL，保持原始行结构
        return '\n'.join(processed_lines)
    
    def _should_filter(self, statement: str) -> bool:
        """
        检查语句是否应该被过滤
        
        Args:
            statement: SQL语句
            
        Returns:
            True如果应该过滤，否则False
        """
        # 检查是否匹配需要过滤的模式
        for pattern in self.filter_patterns:
            if re.search(pattern, statement, re.IGNORECASE):
                logger.debug(f"过滤SET语句: {statement}")
                return True
        return False
    

    
    def __str__(self):
        """返回预处理器描述"""
        return "SetStatementFilterPreprocessor"
    
    def get_info(self) -> Dict[str, Any]:
        """获取预处理器信息"""
        info = super().get_info()
        info.update({
            "description": "SET语句过滤器预处理器",
            "patterns_count": len(self.filter_patterns),
            "abstract_base": False
        })
        return info