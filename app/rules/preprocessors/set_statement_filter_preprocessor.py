"""
SET语句过滤器预处理器
过滤掉SQLFluff无法解析的Hive SET语句和所有SET配置语句
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
    1. 过滤掉SQLFluff无法解析的Hive SET语句（避免PRS错误）
    2. 过滤掉所有SET配置语句（避免SS02/SS03规则误判）
    
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
            r'^\s*set\s+hivevar\:prompt',
            
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
    
    def process(self, sql: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理SQL，过滤SET语句
        
        Args:
            sql: 原始SQL字符串
            context: 上下文信息（可选）
            
        Returns:
            处理后的SQL字符串
        """
        if not sql:
            return sql
        
        lines = sql.split('\n')
        processed_lines = []
        
        for line in lines:
            # 分割行中的语句（按分号分割）
            statements = line.split(';')
            processed_statements = []
            
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                    
                should_filter = False
                
                # 检查是否匹配需要过滤的模式
                for pattern in self.filter_patterns:
                    if re.search(pattern, stmt, re.IGNORECASE):
                        should_filter = True
                        logger.debug(f"过滤SET语句: {stmt}")
                        break
                
                if not should_filter:
                    processed_statements.append(stmt)
            
            # 重新组合语句
            if processed_statements:
                processed_line = '; '.join(processed_statements)
                if not processed_line.endswith(';') and line.strip().endswith(';'):
                    processed_line += ';'
                processed_lines.append(processed_line)
            else:
                # 如果所有语句都被过滤了，保留空行
                processed_lines.append("")
        
        return '\n'.join(processed_lines)
    
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