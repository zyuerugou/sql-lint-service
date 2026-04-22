#!/usr/bin/env python3
# coding=utf-8
"""
注释过滤器预处理器

将SQL中的注释替换为空格，保持行结构不变
这样规则检查时就不会误报注释中的关键字
"""

import re
from typing import Dict, Any, Optional

from .base_preprocessor import BasePreprocessor


class CommentFilterPreprocessor(BasePreprocessor):
    """
    注释过滤器预处理器
    
    将SQL中的注释替换为空格，保持行结构不变
    这样规则检查时就不会误报注释中的关键字
    """
    
    def __init__(self):
        super().__init__()
        self.name = "CommentFilterPreprocessor"
        self.description = "将SQL中的注释替换为空格，保持行结构不变"
        self.order = 10  # 最优先执行，先移除注释避免其他预处理器误判
    
    def process(self, sql: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理SQL，将注释替换为空格或空行
        
        Args:
            sql: 原始SQL
            context: 上下文信息（未使用，为兼容性保留）
            
        Returns:
            处理后的SQL：
            - 行注释：整行替换为一个空格
            - 块注释：每行替换为空行
            - 混合行（代码+注释）：保持代码部分，注释部分替换为空格
        """
        if not sql:
            return sql
        
        lines = sql.split('\n')
        processed_lines = []
        
        # 处理块注释状态
        in_block_comment = False
        
        for line_num, line in enumerate(lines, 1):
            # 如果整行都在块注释中
            if in_block_comment:
                # 检查块注释是否在本行结束
                if '*/' in line:
                    # 块注释结束，本行替换为空行
                    processed_lines.append('')
                    in_block_comment = False
                else:
                    # 整行都在块注释中，替换为空行
                    processed_lines.append('')
                continue
            
            # 检查是否整行都是行注释（以--开头，忽略前导空格）
            stripped = line.lstrip()
            if stripped.startswith('--'):
                # 整行都是行注释，替换为一个空格
                processed_lines.append(' ')
                continue
            
            # 检查是否整行都是块注释（以/*开头，以*/结尾，忽略前导空格）
            stripped = line.strip()
            if stripped.startswith('/*') and stripped.endswith('*/'):
                # 整行都是块注释，替换为空行
                processed_lines.append('')
                continue
            
            # 处理混合行（可能包含行注释或块注释）
            result_line, new_in_block_comment = self._process_mixed_line(line)
            
            if new_in_block_comment:
                # 块注释开始但未结束
                in_block_comment = True
                # 将整行替换为空行
                processed_lines.append('')
            else:
                processed_lines.append(result_line)
        
        return '\n'.join(processed_lines)
    
    def _process_mixed_line(self, line: str):
        """
        处理混合行（可能包含注释的代码行）
        
        Args:
            line: 原始行
            
        Returns:
            tuple: (处理后的行, 是否开始块注释但未结束)
        """
        if not line:
            return line, False
        
        # 转换为字符列表以便修改
        chars = list(line)
        i = 0
        in_string = False
        string_char = None
        block_comment_started = False
        
        while i < len(chars):
            char = chars[i]
            
            # 处理字符串
            if char in ("'", '"'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    # 检查是否转义
                    if i > 0 and chars[i-1] == '\\':
                        pass  # 转义引号，继续字符串
                    else:
                        in_string = False
                        string_char = None
            
            # 只有在不在字符串中时才处理注释
            if not in_string:
                # 检查行注释
                if char == '-' and i + 1 < len(chars) and chars[i+1] == '-':
                    # 找到行注释开始，将剩余部分替换为空格
                    for j in range(i, len(chars)):
                        chars[j] = ' '
                    break  # 行注释之后没有需要处理的内容
                
                # 检查块注释开始
                if char == '/' and i + 1 < len(chars) and chars[i+1] == '*':
                    # 找到块注释开始
                    # 查找块注释结束
                    comment_end = line.find('*/', i)
                    if comment_end != -1:
                        # 块注释在同一行内结束
                        # 将块注释部分替换为空格
                        for j in range(i, comment_end + 2):
                            chars[j] = ' '
                        i = comment_end + 1  # 跳过已处理的部分
                    else:
                        # 块注释跨行，将当前行剩余部分替换为空格
                        for j in range(i, len(chars)):
                            chars[j] = ' '
                        block_comment_started = True
                        break  # 行尾之后没有需要处理的内容
            
            i += 1
        
        return ''.join(chars), block_comment_started
    
    def get_info(self) -> Dict[str, Any]:
        """获取预处理器信息"""
        return {
            "name": self.name,
            "description": self.description,
            "order": self.order
        }
