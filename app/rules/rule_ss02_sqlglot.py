#!/usr/bin/env python3
# coding=utf-8
"""
基于sqlglot的SS02规则：SQL关键字必须大写

使用sqlglot的tokenize方法，通过token_type判断关键字，避免维护手动关键字列表。
"""

import re
from typing import List
import sqlglot
import sqlglot.expressions as exp

from app.rules.sqlglot_base import SQLGlotBaseRule, Violation


class RuleSs02Sqlglot(SQLGlotBaseRule):
    """
    规则SS02：SQL关键字必须大写
    
    基于sqlglot的tokenize方法实现，通过token_type判断SQL关键字是否使用大写形式。
    相比正则表达式方法，此方法能：
    1. 准确识别SQL关键字（通过token_type）
    2. 避免误判注释和字符串中的内容
    3. 提供精确的行列位置信息
    4. 支持不同SQL方言
    """
    
    code = "SS02"
    description = "SQL关键字必须使用大写形式。"
    groups = ("all", "customer")
    
    # 非关键字token类型（这些不会被检查）
    NON_KEYWORD_TOKEN_TYPES = {
        # 标识符和变量
        'IDENTIFIER', 'VAR',
        # 字面量
        'STRING', 'NUMBER', 'TRUE', 'FALSE', 'NULL',
        # 注释
        'COMMENT', 'BLOCK_COMMENT',
        # 空白和分隔符
        'WHITESPACE', 'SEMICOLON', 'COMMA', 'DOT',
        # 括号
        'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
        # 操作符
        'EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE', 'PLUS', 'MINUS', 'STAR', 'SLASH',
        'MOD', 'AMPERSAND', 'PIPE', 'CARET', 'TILDE', 'BANG',
        # 其他
        'COLON', 'DOUBLE_COLON', 'QUESTION', 'AT', 'DOLLAR', 'PERCENT',
        'BACKSLASH', 'UNDERSCORE', 'HASH',
    }
    
    def check(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        """
        检查SQL中的小写关键字
        
        使用sqlglot的tokenize方法将SQL分解为token，
        通过token_type判断是否是关键字，然后从原始SQL中提取文本检查是否小写。
        
        注意：sqlglot的tokenizer会规范化关键字文本（如'order by'变成'ORDER BY'），
        所以我们需要从原始SQL中提取文本，而不是使用token.text。
        
        Args:
            ast: sqlglot AST（未使用，保持接口兼容）
            sql: 要检查的SQL字符串
            
        Returns:
            违规列表
        """
        violations = []
        
        if not sql:
            return violations
        
        try:
            # 使用sqlglot的tokenize方法
            # 默认使用hive方言，可以根据需要调整
            tokens = sqlglot.tokenize(sql, dialect="hive")
            
            # 使用集合记录已经报告过的位置，避免重复报告
            # 格式: (line, column, start, end) - 使用位置而不是文本
            reported_positions = set()
            
            for token in tokens:
                # 判断是否是关键字token
                if self._is_keyword_token(token):
                    # 从原始SQL中提取文本
                    # token.end是独占的，所以需要+1来包含最后一个字符
                    end_index = token.end + 1 if token.end < len(sql) else token.end
                    original_text = sql[token.start:end_index]
                    
                    # 检查关键字是否不是全大写（包含小写字母）
                    if self._is_keyword_not_uppercase(original_text, token):
                        position_key = (token.line, token.col, token.start)
                        
                        # 检查是否已经报告过这个位置的关键字
                        if position_key not in reported_positions:
                            reported_positions.add(position_key)
                            violations.append(Violation(
                                rule_id=self.code,
                                message=f"{self.description} 关键字必须全大写，发现: {original_text}",
                                line=token.line,
                                column=token.col,
                                severity="error"
                            ))
                            
        except Exception as e:
            # 如果tokenize失败，回退到原来的正则表达式方法
            # 这可以处理sqlglot不支持的语法或边缘情况
            return self._fallback_check(sql)
        
        return violations
    
    def _is_keyword_token(self, token) -> bool:
        """
        判断token是否是SQL关键字
        
        通过token_type判断，排除已知的非关键字类型。
        关键字token通常具有大写的token_type名称。
        
        Args:
            token: sqlglot Token对象
            
        Returns:
            True如果是关键字，否则False
        """
        # 获取token_type的名称
        token_type_name = token.token_type.name
        
        # 排除已知的非关键字类型
        if token_type_name in self.NON_KEYWORD_TOKEN_TYPES:
            return False
        
        # 关键字token_type通常是大写的
        # 检查token_type是否是常见的SQL关键字类型
        common_keyword_types = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING', 'ORDER',
            'INSERT', 'INTO', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'VIEW', 'INDEX', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL',
            'OUTER', 'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE',
            'IS', 'NULL', 'TRUE', 'FALSE', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'CAST', 'DISTINCT', 'UNION', 'ALL', 'INTERSECT', 'EXCEPT', 'WITH',
            'VALUES', 'SET', 'DESC', 'ASC', 'LIMIT', 'OFFSET', 'FETCH', 'NEXT',
            'ONLY', 'OVER', 'PARTITION', 'ROWS', 'RANGE', 'PRECEDING',
            'FOLLOWING', 'CURRENT', 'ROW', 'FIRST', 'LAST', 'DEFAULT',
            'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE', 'SIMILAR', 'TO',
            'ANY', 'SOME', 'ALL', 'UNIQUE', 'PRIMARY', 'FOREIGN', 'KEY',
            'REFERENCES', 'CHECK', 'CONSTRAINT', 'DEFAULT', 'AUTO_INCREMENT',
            'SEQUENCE', 'TRIGGER', 'PROCEDURE', 'FUNCTION', 'RETURNS',
            'BEGIN', 'DECLARE', 'END', 'IF', 'ELSE', 'ELSIF', 'THEN',
            'LOOP', 'WHILE', 'FOR', 'FOREACH', 'EXIT', 'CONTINUE',
            'RETURN', 'RAISE', 'EXCEPTION', 'WHEN', 'CASE',
            # 复合关键字
            'ORDER_BY', 'GROUP_BY', 'UNION_ALL', 'LEFT_JOIN', 'RIGHT_JOIN',
            'FULL_JOIN', 'INNER_JOIN', 'CROSS_JOIN', 'NATURAL_JOIN',
            'IS_NOT', 'IS_NULL', 'IS_NOT_NULL', 'NOT_IN', 'NOT_BETWEEN',
            'NOT_LIKE', 'NOT_EXISTS'
        }
        
        return token_type_name in common_keyword_types
    
    def _is_keyword_not_uppercase(self, original_text: str, token) -> bool:
        """
        检查关键字是否不是全大写
        
        新需求：关键字必须全大写，只要有一个小写字母就违规。
        例如：WHeRE、SeLeCt、WHERE（正确）、WHERE（正确）
        
        Args:
            original_text: 从原始SQL中提取的文本
            token: sqlglot Token对象（用于获取token_type信息）
            
        Returns:
            True如果关键字不是全大写（包含小写字母），否则False
        """
        token_type_name = token.token_type.name
        
        # 对于复合关键字（如ORDER_BY、GROUP_BY）
        if '_' in token_type_name:
            # 复合关键字可能包含多个单词
            # 检查每个单词是否全大写
            words = original_text.split()
            return not all(word.isupper() for word in words)
        else:
            # 简单关键字，检查是否全大写
            return not original_text.isupper()
    
    def _fallback_check(self, sql: str) -> List[Violation]:
        """
        回退检查方法（使用正则表达式）
        
        当tokenize方法失败时使用，保持向后兼容。
        
        Args:
            sql: 要检查的SQL字符串
            
        Returns:
            违规列表
        """
        violations = []
        
        # 将SQL按行分割
        lines = sql.split('\n')
        
        # 使用集合记录已经报告过的位置，避免重复报告
        reported_positions = set()
        
        # 回退使用的关键字列表（简化版）
        fallback_keywords = {
            'select', 'from', 'where', 'group', 'by', 'having', 'order',
            'insert', 'into', 'update', 'delete', 'create', 'drop', 'alter',
            'table', 'view', 'index', 'join', 'inner', 'left', 'right', 'full',
            'outer', 'on', 'as', 'and', 'or', 'not', 'in', 'between', 'like',
            'is', 'null', 'true', 'false', 'case', 'when', 'then', 'else', 'end',
            'cast', 'distinct', 'union', 'all', 'intersect', 'except', 'with',
            'values', 'set', 'desc', 'asc', 'limit', 'offset'
        }
        
        for line_num, line in enumerate(lines, 1):
            # 查找所有单词（不区分大小写）
            for match in re.finditer(r'\b([a-zA-Z][a-zA-Z_]*)\b', line):
                word = match.group(1)
                word_lower = word.lower()
                
                # 检查是否是SQL关键字
                if word_lower in fallback_keywords:
                    # 检查是否不是全大写
                    if not word.isupper():
                        position_key = (line_num, match.start() + 1, word)
                        
                        # 检查是否已经报告过这个位置的关键字
                        if position_key not in reported_positions:
                            reported_positions.add(position_key)
                            violations.append(Violation(
                                rule_id=self.code,
                                message=f"{self.description} 关键字必须全大写，发现: {word}",
                                line=line_num,
                                column=match.start() + 1,
                                severity="error"
                            ))
        
        return violations


# 兼容性别名，便于动态加载
Rule_Ss02_Sqlglot = RuleSs02Sqlglot


