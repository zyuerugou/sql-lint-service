#!/usr/bin/env python3
# coding=utf-8
"""
基于sqlglot的SS01规则：禁止使用SELECT *
"""

from typing import List
import sqlglot.expressions as exp

from app.rules.sqlglot_base import SQLGlotBaseRule, Violation


class RuleSs01Sqlglot(SQLGlotBaseRule):
    """
    规则SS01：禁止使用SELECT *
    
    基于sqlglot实现，检查所有SELECT语句（包括子查询）是否包含通配符(*)
    """
    
    code = "SS01"
    description = "禁止使用 SELECT *，请明确列出所有字段。"
    groups = ("all", "customer")
    
    def check(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        violations = []
        
        if not ast:
            return violations
        
        # 查找所有SELECT语句
        select_statements = list(ast.find_all(exp.Select))
        
        for select_stmt in select_statements:
            # 检查是否包含通配符(*)
            stars = list(select_stmt.find_all(exp.Star))
            
            if stars:
                # 为每个通配符创建违规
                for star in stars:
                    line, col = self._get_position(star, sql)
                    violations.append(Violation(
                        rule_id=self.code,
                        message=self.description,
                        line=line,
                        column=col,
                        severity="error"
                    ))
        
        return violations


# 兼容性别名，便于动态加载
Rule_Ss01_Sqlglot = RuleSs01Sqlglot


