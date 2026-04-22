#!/usr/bin/env python3
# coding=utf-8
"""
基于sqlglot的SS03规则：标识符应当为小写
"""

from typing import List, Tuple
import sqlglot.expressions as exp

from app.rules.sqlglot_base import SQLGlotBaseRule, Violation


class RuleSs03Sqlglot(SQLGlotBaseRule):
    """
    规则SS03：除了关键字、双引号、引号内的内容以外，表名和字段名应当为小写
    
    基于sqlglot实现，检查标识符是否包含大写字母
    """
    
    code = "SS03"
    description = "标识符应当为小写。"
    groups = ("all", "customer")
    
    def check(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        violations = []
        
        if not ast:
            return violations
        
        # 获取所有标识符
        identifiers = self._extract_identifiers(ast, sql)
        
        # 使用集合记录已处理的标识符位置，避免重复
        processed_positions = set()
        
        for name, line, col, ident_type in identifiers:
            # 跳过已经是小写的标识符
            if name.islower():
                continue
            
            # 跳过数字
            if name.replace('.', '').isdigit():
                continue
            
            # 跳过布尔值和NULL
            if name.upper() in ['TRUE', 'FALSE', 'NULL']:
                continue
            
            # 检查是否在关键字上下文中（简化实现）
            if self._is_in_keyword_context(ast, line, col):
                continue
            
            # 检查是否已经处理过相同位置和名称的标识符
            # 使用更严格的位置检查：同一行，列号相同
            position_key = (line, col, name)
            if position_key in processed_positions:
                continue
            processed_positions.add(position_key)
            
            # 调试：打印检测到的大写标识符
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"SS03检测到大写标识符: {name} (类型: {ident_type}, 位置: 行{line}, 列{col})")
            
            violations.append(Violation(
                rule_id=self.code,
                message=f"标识符应当为小写: {name}",
                line=line,
                column=col,
                severity="error"
            ))
        
        return violations
    
    def _extract_identifiers(self, ast: exp.Expression, sql: str = "") -> List[Tuple[str, int, int, str]]:
        """从AST提取标识符"""
        identifiers = []
        
        # 表名
        for table in ast.find_all(exp.Table):
            name = table.name
            line, col = self._get_position(table, sql)
            identifiers.append((name, line, col, "table"))
            
            # 表别名
            if table.alias:
                line, col = self._get_position(table.args.get("alias"), sql)
                identifiers.append((table.alias, line, col, "alias"))
        
        # 列名
        for column in ast.find_all(exp.Column):
            name = column.name
            
            # 对于Column节点，直接使用_get_position获取位置
            # _get_position方法已经处理了SELECT中的Column节点
            line, col = self._get_position(column, sql)
            
            identifiers.append((name, line, col, "column"))
            
            # 表名部分
            if column.table:
                line, col = self._get_position(column.args.get("table"), sql)
                identifiers.append((column.table, line, col, "table"))
        
        # 别名
        for alias in ast.find_all(exp.Alias):
            name = alias.alias
            line, col = self._get_position(alias, sql)
            identifiers.append((name, line, col, "alias"))
        
        # 通用标识符（包括INSERT语句中的字段名）
        for identifier in ast.find_all(exp.Identifier):
            name = identifier.name
            line, col = self._get_position(identifier, sql)
            
            # 检查父节点类型，确定标识符类型
            ident_type = "identifier"
            parent = identifier.parent
            if parent:
                if isinstance(parent, exp.Schema):
                    # INSERT语句中的字段
                    ident_type = "insert_field"
                elif isinstance(parent, exp.Column):
                    # SELECT语句中的列 - 跳过，因为Column节点已经处理了
                    continue
                elif isinstance(parent, exp.Table):
                    # 表名 - 跳过，因为Table节点已经处理了
                    continue
            
            # 避免重复添加
            # 如果已经有相同名称、相似位置（±5列内）的标识符，跳过
            is_duplicate = False
            for ident in identifiers:
                if ident[0] == name:
                    # 检查位置是否相似（同一行，列号相差不超过5）
                    if ident[1] == line and abs(ident[2] - col) <= 5:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                identifiers.append((name, line, col, ident_type))
        
        return identifiers
    
    def _is_in_keyword_context(self, ast: exp.Expression, line: int, col: int) -> bool:
        """
        检查标识符是否在关键字上下文中
        
        简化实现：在实际使用中可能需要更复杂的逻辑
        这里我们检查标识符是否可能是函数名或类型名
        """
        # 查找附近的表达式
        # 这里简化处理，实际可能需要检查父节点类型
        return False


# 兼容性别名，便于动态加载
Rule_Ss03_Sqlglot = RuleSs03Sqlglot


