#!/usr/bin/env python3
# coding=utf-8
"""
位置记录器 - 在解析阶段为AST节点记录位置信息
"""

import re
import sqlglot as sg
import sqlglot.expressions as exp
from typing import List, Tuple, Optional, Dict


class PositionRecorder:
    """
    位置记录器
    
    在SQL解析后，为AST节点记录准确的位置信息（行、列）。
    规则检查时可以直接从节点的meta属性读取位置，无需重新搜索。
    """
    
    @staticmethod
    def parse_with_positions(sql: str, dialect: str = "hive") -> List[exp.Expression]:
        """
        解析SQL并记录位置信息
        
        Args:
            sql: SQL语句
            dialect: SQL方言
            
        Returns:
            带位置信息的AST列表
        """
        if not sql or not sql.strip():
            return []
        
        try:
            # 解析SQL
            asts = sg.parse(sql, read=dialect)
            
            # 为每个AST记录位置
            for i, ast in enumerate(asts):
                # 计算这个AST在SQL中的起始位置
                ast_start_pos = PositionRecorder._find_ast_start_position(ast, sql, i)
                PositionRecorder._add_positions_to_ast(ast, sql, ast_start_pos)
            
            return asts
        except Exception as e:
            # 解析失败，返回空列表
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"SQL解析失败: {type(e).__name__}: {e}")
            return []
    
    @staticmethod
    def _find_ast_start_position(ast: exp.Expression, sql: str, ast_index: int) -> int:
        """
        查找AST在SQL中的起始位置
        
        Args:
            ast: AST
            sql: 原始SQL
            ast_index: AST在列表中的索引
            
        Returns:
            起始字符位置
        """
        # 获取AST的SQL表示
        ast_sql = ast.sql()
        
        # 从索引0开始查找
        start_pos = 0
        for i in range(ast_index + 1):
            # 查找第i个AST的SQL
            pos = sql.find(ast_sql, start_pos)
            if pos == -1:
                # 如果没有找到，尝试大小写不敏感查找
                import re
                pattern = re.escape(ast_sql)
                matches = list(re.finditer(pattern, sql[start_pos:], re.IGNORECASE))
                if matches:
                    pos = start_pos + matches[0].start()
                else:
                    # 仍然没找到，返回0
                    return 0
            
            if i < ast_index:
                # 不是我们要找的AST，继续查找下一个
                start_pos = pos + len(ast_sql)
            else:
                # 找到我们要找的AST
                return pos
        
        return 0
    
    @staticmethod
    def _add_positions_to_ast(ast: exp.Expression, sql: str, start_pos: int = 0):
        """为AST添加位置信息"""
        if not ast:
            return
        
        # 获取token流（从start_pos开始）
        try:
            # 获取完整SQL的token
            all_tokens = list(sg.tokenize(sql))
            
            # 过滤出在start_pos之后的token
            tokens = []
            for token in all_tokens:
                if token.start >= start_pos:
                    tokens.append(token)
        except Exception:
            tokens = []
        
        # 使用token流为节点设置位置
        PositionRecorder._set_positions_from_tokens(ast, tokens, sql)
    
    @staticmethod
    def _set_positions_from_tokens(node: exp.Expression, tokens: List, sql: str, token_idx: int = 0):
        """
        从token流为节点设置位置
        
        使用token的字符位置计算准确的行列号
        
        Args:
            node: 当前节点
            tokens: token列表
            sql: 原始SQL
            token_idx: 当前token索引
            
        Returns:
            下一个token索引
        """
        if not node:
            return token_idx
        
        # 获取节点的文本表示
        node_text = PositionRecorder._get_node_text(node)
        if not node_text:
            # 递归处理子节点
            for child in PositionRecorder._get_children(node):
                token_idx = PositionRecorder._set_positions_from_tokens(child, tokens, sql, token_idx)
            return token_idx
        
        # 查找匹配的token
        found = False
        for i in range(token_idx, len(tokens)):
            token = tokens[i]
            
            # 检查token是否匹配节点文本
            if PositionRecorder._token_matches_node(token, node_text):
                # 使用token的字符位置计算准确的行列号
                line, col = PositionRecorder._calculate_position_from_token(token, sql)
                node._meta = {'line': line, 'col': col}
                token_idx = i + 1
                found = True
                break
        
        if not found:
            # 如果没有找到匹配的token，尝试在SQL中查找
            position = PositionRecorder._find_position_in_sql(node_text, sql)
            if position:
                line, col = position
                node._meta = {'line': line, 'col': col}
        
        # 递归处理子节点
        for child in PositionRecorder._get_children(node):
            token_idx = PositionRecorder._set_positions_from_tokens(child, tokens, sql, token_idx)
        
        return token_idx
    
    @staticmethod
    def _calculate_position_from_token(token, sql: str) -> Tuple[int, int]:
        """
        从token计算准确的行列号
        
        token的col属性可能计算方式不同，我们使用字符位置重新计算
        """
        start_pos = token.start
        
        # 计算行号：统计换行符数量
        lines_before = sql[:start_pos].split('\n')
        line = len(lines_before)
        
        # 计算列号
        if line > 0:
            last_line_start = sql.rfind('\n', 0, start_pos)
            if last_line_start == -1:
                col = start_pos + 1  # 第一行，列从1开始
            else:
                col = start_pos - last_line_start  # 减去上一行换行符的位置
        else:
            col = start_pos + 1
        
        return line, col
    
    @staticmethod
    def _get_node_text(node: exp.Expression) -> Optional[str]:
        """获取节点的文本表示"""
        if isinstance(node, exp.Identifier):
            return node.name
        elif isinstance(node, exp.Column) and hasattr(node, 'name'):
            return node.name
        elif isinstance(node, exp.Table) and hasattr(node, 'name'):
            return node.name
        elif isinstance(node, exp.Alias) and hasattr(node, 'alias'):
            return node.alias
        return None
    
    @staticmethod
    def _get_children(node: exp.Expression) -> List[exp.Expression]:
        """获取节点的子节点"""
        children = []
        
        # 从args获取子表达式
        if hasattr(node, 'args'):
            for arg_value in node.args.values():
                if isinstance(arg_value, exp.Expression):
                    children.append(arg_value)
                elif isinstance(arg_value, list):
                    for item in arg_value:
                        if isinstance(item, exp.Expression):
                            children.append(item)
        
        return children
    
    @staticmethod
    def _token_matches_node(token, node_text: str) -> bool:
        """检查token是否匹配节点文本"""
        if not node_text:
            return False
        
        # 大小写不敏感比较
        return token.text.upper() == node_text.upper()
    
    @staticmethod
    def _find_position_in_sql(text: str, sql: str) -> Optional[Tuple[int, int]]:
        """在SQL中查找文本位置"""
        if not text or not sql:
            return None
        
        # 使用正则查找，考虑单词边界
        pattern = r'\b' + re.escape(text) + r'\b'
        matches = list(re.finditer(pattern, sql, re.IGNORECASE))
        
        if not matches:
            return None
        
        # 取第一个匹配（简化处理，实际应该根据上下文选择）
        match = matches[0]
        start = match.start()
        
        # 计算行和列
        lines_before = sql[:start].split('\n')
        line = len(lines_before)
        
        if line > 0:
            last_line_start = sql.rfind('\n', 0, start)
            if last_line_start == -1:
                col = start + 1
            else:
                col = start - last_line_start
        else:
            col = start + 1
        
        return line, col
    
    @staticmethod
    def get_position(node: exp.Expression, sql: str = "") -> Tuple[int, int]:
        """
        获取节点位置
        
        优先从节点的meta属性读取，如果没有则尝试计算
        
        Args:
            node: AST节点
            sql: 原始SQL（可选，用于回退计算）
            
        Returns:
            (行号, 列号)
        """
        if not node:
            return 1, 1
        
        # 优先从meta读取
        if node.meta and 'line' in node.meta and 'col' in node.meta:
            return node.meta['line'], node.meta['col']
        
        # 如果没有位置信息，尝试计算
        if sql:
            node_text = PositionRecorder._get_node_text(node)
            if node_text:
                position = PositionRecorder._find_position_in_sql(node_text, sql)
                if position:
                    return position
        
        # 默认位置
        return 1, 1