#!/usr/bin/env python3
# coding=utf-8
"""
测试分号分隔的多SQL语句
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot


def test_multiple_sql_statements():
    """测试分号分隔的多SQL语句"""
    # 模拟用户的情况：多个SQL语句，其中一个包含注释
    test_sql = """SELECT * FROM table1;
SELECT * FROM table2;
SELECT * FROM users -- id in ('ncp', 'nad');
SELECT * FROM table3;
SELECT * FROM table4;
SELECT * FROM table5;"""
    
    print("测试SQL（6个语句，第3个包含注释）:")
    print(test_sql)
    print()
    
    rule = RuleSs02Sqlglot()
    
    # 分割SQL语句
    print("分割SQL语句...")
    statements = test_sql.split(';')
    statements = [s.strip() for s in statements if s.strip()]
    print(f"分割出 {len(statements)} 个语句")
    
    total_violations = 0
    
    for i, sql_str in enumerate(statements, 1):
        print(f"\n--- 语句 {i} ---")
        print(f"SQL: {sql_str}")
        
        try:
            # 解析单个语句
            ast = sqlglot.parse_one(sql_str, read="hive")
            
            # 检查规则
            violations = rule.check(ast, sql_str)
            
            print(f"违规数量: {len(violations)}")
            for v in violations:
                print(f"  - 行{v.line}, 列{v.column}: {v.message}")
            
            total_violations += len(violations)
        except Exception as e:
            print(f"解析失败: {e}")
    
    print(f"\n总计: 发现 {total_violations} 个违规")
    
    # 分析
    if total_violations > 0:
        print(f"\n分析:")
        print(f"1. 有 {len(statements)} 个SQL语句")
        print(f"2. 只有第3个语句包含注释 '-- id in ('ncp', 'nad')'")
        print(f"3. 发现了 {total_violations} 个违规")
        print(f"4. 如果每个语句都触发了规则，理论上最多 {len(statements)} 个违规")
        print(f"5. 但实际上只有 {total_violations} 个，说明只有包含注释的语句触发了规则")
    
    return total_violations


if __name__ == "__main__":
    violation_count = test_multiple_sql_statements()
    print(f"\n结论: 在多SQL语句场景中发现 {violation_count} 个违规")