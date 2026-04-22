#!/usr/bin/env python3
# coding=utf-8
"""
基于sqlglot的SS04规则：检查表别名使用
"""

from typing import List
import sqlglot.expressions as exp

from app.rules.sqlglot_base import SQLGlotBaseRule, Violation


class RuleSs04Sqlglot(SQLGlotBaseRule):
    """
    规则SS04：检查表别名使用
    
    要求: 当使用表别名时，别名应该有意义且简洁
    """
    
    code = "SS04"
    description = "检查表别名是否使用有意义且简洁的名称"
    groups = ("all", "customer")
    
    def check(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        violations = []
        
        if not ast:
            return violations
        
        # 查找所有表（包括别名）
        tables = list(ast.find_all(exp.Table))
        
        for table in tables:
            alias_name = table.alias
            if alias_name:
                # 检查别名是否太短（小于2个字符）
                if len(alias_name) < 2:
                    line, col = self._get_position(table, sql)
                    violations.append(Violation(
                        rule_id=self.code,
                        message=f'表别名"{alias_name}"太短，建议使用更有意义的名称',
                        line=line,
                        column=col,
                        severity="warning"
                    ))
                
                # 检查别名是否使用无意义的名称（如t1, t2, a, b等）
                meaningless_aliases = ['t1', 't2', 't3', 'a', 'b', 'c', 'x', 'y', 'z']
                if alias_name.lower() in meaningless_aliases:
                    line, col = self._get_position(table, sql)
                    violations.append(Violation(
                        rule_id=self.code,
                        message=f'表别名"{alias_name}"无意义，建议使用描述性名称',
                        line=line,
                        column=col,
                        severity="warning"
                    ))
        
        # 查找所有子查询别名
        subqueries = list(ast.find_all(exp.Subquery))
        
        for subquery in subqueries:
            alias = subquery.alias
            if alias:
                alias_name = alias.alias if isinstance(alias, exp.TableAlias) else alias
                if alias_name:
                    # 检查子查询别名是否使用无意义的名称
                    meaningless_aliases = ['t', 'tmp', 'temp', 'sub', 'sq']
                    if alias_name.lower() in meaningless_aliases:
                        line, col = self._get_position(subquery, sql)
                        violations.append(Violation(
                            rule_id=self.code,
                            message=f'子查询别名"{alias_name}"无意义，建议使用描述性名称',
                            line=line,
                            column=col,
                            severity="warning"
                        ))
        
        return violations


# 兼容性别名，便于动态加载
Rule_Ss04_Sqlglot = RuleSs04Sqlglot


