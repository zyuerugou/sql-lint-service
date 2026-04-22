#!/usr/bin/env python3
# coding=utf-8
"""
测试多次调用问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot


def test_multiple_calls_issue():
    """测试多次调用问题"""
    # 模拟lint服务的行为：多次调用同一个规则实例
    rule = RuleSs02Sqlglot()
    
    # 完整的SQL（多个语句）
    full_sql = """SELECT * FROM table1;
SELECT * FROM table2;
SELECT * FROM users -- id in ('ncp', 'nad');
SELECT * FROM table3;"""
    
    print("完整的SQL（4个语句）:")
    print(full_sql)
    print()
    
    # 分割SQL语句
    statements = full_sql.split(';')
    statements = [s.strip() for s in statements if s.strip()]
    
    print(f"分割出 {len(statements)} 个语句")
    print()
    
    total_violations = []
    
    # 模拟lint服务：为每个语句调用规则，但传入完整的SQL
    for i in range(len(statements)):
        print(f"调用 {i+1}: 使用完整的SQL")
        
        # 解析第一个语句的AST（实际lint服务会解析对应的语句）
        ast = sqlglot.parse_one(statements[0], read="hive") if statements else None
        
        # 但传入完整的SQL！
        violations = rule.check(ast, full_sql)
        
        print(f"  发现 {len(violations)} 个违规")
        for v in violations:
            print(f"    - 行{v.line}, 列{v.column}: {v.message}")
        
        total_violations.extend(violations)
    
    print(f"\n总计: 发现 {len(total_violations)} 个违规（可能有重复）")
    
    # 检查是否有重复
    positions = [(v.line, v.column, v.message) for v in total_violations]
    unique_positions = set(positions)
    
    print(f"唯一位置数量: {len(unique_positions)}")
    if len(positions) != len(unique_positions):
        print("有重复的违规!")
        for pos in set(positions):
            count = positions.count(pos)
            if count > 1:
                print(f"  位置 {pos} 出现了 {count} 次")
    
    # 现在测试正确的方式：为每个语句传入对应的SQL
    print(f"\n--- 正确的方式：为每个语句传入对应的SQL ---")
    
    correct_violations = []
    
    for i, sql_str in enumerate(statements, 1):
        if sql_str:
            print(f"语句 {i}: '{sql_str}'")
            ast = sqlglot.parse_one(sql_str, read="hive")
            violations = rule.check(ast, sql_str)
            
            print(f"  发现 {len(violations)} 个违规")
            for v in violations:
                print(f"    - 行{v.line}, 列{v.column}: {v.message}")
            
            correct_violations.extend(violations)
    
    print(f"\n正确方式总计: 发现 {len(correct_violations)} 个违规")
    
    return len(total_violations), len(correct_violations)


if __name__ == "__main__":
    wrong_count, correct_count = test_multiple_calls_issue()
    print(f"\n结论:")
    print(f"错误方式（传入完整SQL）: {wrong_count} 个违规")
    print(f"正确方式（传入对应SQL）: {correct_count} 个违规")
    print(f"\n如果lint服务错误地传入完整SQL，可能会导致重复报告!")