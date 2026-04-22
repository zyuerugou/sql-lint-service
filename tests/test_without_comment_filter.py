#!/usr/bin/env python3
# coding=utf-8
"""
测试没有注释过滤器的情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot


def test_without_comment_filter():
    """测试没有注释过滤器的情况"""
    # 模拟旧的SS02规则（没有注释处理）
    class OldRuleSs02Sqlglot(RuleSs02Sqlglot):
        """旧的SS02规则，没有注释处理"""
        
        def check(self, ast, sql: str = ""):
            # 复制旧的逻辑
            import re
            from app.rules.sqlglot_base import Violation
            
            violations = []
            
            if not ast or not sql:
                return violations
            
            # 将SQL按行分割
            lines = sql.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 查找小写关键字 - 使用IGNORECASE
                for match in re.finditer(r'\b([a-z][a-z_]+)\b', line, re.IGNORECASE):
                    word = match.group(1).lower()
                    
                    # 检查是否是SQL关键字
                    if word in self.SQL_KEYWORDS:
                        # 检查是否真的是小写
                        original_word = match.group(1)
                        if original_word.islower():
                            violations.append(Violation(
                                rule_id=self.code,
                                message=f"{self.description} 发现小写关键字: {original_word}",
                                line=line_num,
                                column=match.start() + 1,
                                severity="error"
                            ))
            
            return violations
    
    # 测试SQL
    test_sql = """SELECT * FROM users -- id in ('ncp', 'nad')"""
    
    print("测试旧的SS02规则（没有注释过滤器）:")
    print(f"SQL: {test_sql}")
    print()
    
    old_rule = OldRuleSs02Sqlglot()
    new_rule = RuleSs02Sqlglot()
    
    # 解析SQL
    ast = sqlglot.parse_one(test_sql, read="hive")
    
    # 检查规则
    old_violations = old_rule.check(ast, test_sql)
    new_violations = new_rule.check(ast, test_sql)
    
    print(f"旧的规则发现 {len(old_violations)} 个违规")
    for i, v in enumerate(old_violations, 1):
        print(f"  违规 {i}: 行{v.line}, 列{v.column}, 消息: {v.message}")
    
    print(f"\n新的规则发现 {len(new_violations)} 个违规")
    for i, v in enumerate(new_violations, 1):
        print(f"  违规 {i}: 行{v.line}, 列{v.column}, 消息: {v.message}")
    
    # 分析差异
    print(f"\n分析:")
    print(f"1. 旧的规则使用 re.IGNORECASE，会匹配 'SELECT', 'FROM' 等")
    print(f"2. 但检查 original_word.islower()，所以不会触发（因为 'SELECT' 不是小写）")
    print(f"3. 只会触发 'in'，因为它是小写的")
    print(f"4. 所以旧的规则也应该只触发1次，而不是4次")
    
    # 测试多个SQL语句
    print(f"\n--- 测试多个SQL语句 ---")
    multi_sql = """SELECT * FROM table1;
SELECT * FROM table2;
SELECT * FROM users -- id in ('ncp', 'nad');
SELECT * FROM table3;"""
    
    statements = multi_sql.split(';')
    statements = [s.strip() for s in statements if s.strip()]
    
    total_old_violations = 0
    total_new_violations = 0
    
    for i, sql_str in enumerate(statements, 1):
        if sql_str:
            ast = sqlglot.parse_one(sql_str, read="hive")
            old_v = old_rule.check(ast, sql_str)
            new_v = new_rule.check(ast, sql_str)
            
            total_old_violations += len(old_v)
            total_new_violations += len(new_v)
    
    print(f"多个SQL语句:")
    print(f"  旧的规则总共发现 {total_old_violations} 个违规")
    print(f"  新的规则总共发现 {total_new_violations} 个违规")
    
    return len(old_violations), len(new_violations)


if __name__ == "__main__":
    old_count, new_count = test_without_comment_filter()
    print(f"\n结论: 旧的规则发现 {old_count} 个违规，新的规则发现 {new_count} 个违规")