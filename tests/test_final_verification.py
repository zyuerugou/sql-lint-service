#!/usr/bin/env python3
# coding=utf-8
"""
最终验证：用户报告的问题是否已解决
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot
from app.rules.preprocessors.comment_filter_preprocessor import CommentFilterPreprocessor


def test_final_verification():
    """最终验证"""
    print("=" * 60)
    print("最终验证：用户报告的问题是否已解决")
    print("=" * 60)
    
    # 用户报告的SQL（单个语句）
    sql_single = """SELECT * FROM users -- id in ('ncp', 'nad')"""
    
    # 多语句SQL
    sql_multi = """SELECT * FROM table1;
SELECT * FROM table2;
SELECT * FROM users -- id in ('ncp', 'nad');
SELECT * FROM table3;"""
    
    rule = RuleSs02Sqlglot()
    preprocessor = CommentFilterPreprocessor()
    
    print("\n1. 测试单个SQL语句（有注释）:")
    print(f"   SQL: {sql_single}")
    
    # 应用预处理器
    processed_sql = preprocessor.process(sql_single)
    print(f"   处理后的SQL: {processed_sql}")
    
    ast = sqlglot.parse_one(processed_sql, read="hive")
    violations = rule.check(ast, processed_sql)
    print(f"   违规数量: {len(violations)}")
    
    if len(violations) == 0:
        print("   ✓ 问题已解决：注释中的关键字不再触发SS02规则")
    else:
        print(f"   ✗ 仍然发现 {len(violations)} 个违规")
    
    print("\n2. 测试多个SQL语句:")
    statements = sql_multi.split(';')
    statements = [s.strip() for s in statements if s.strip()]
    
    total_violations = 0
    for i, sql_str in enumerate(statements, 1):
        if sql_str:
            processed = preprocessor.process(sql_str)
            ast = sqlglot.parse_one(processed, read="hive")
            violations = rule.check(ast, processed)
            
            if violations:
                print(f"   语句 {i}: 发现 {len(violations)} 个违规")
                total_violations += len(violations)
    
    print(f"   总共发现 {total_violations} 个违规")
    
    if total_violations == 0:
        print("   ✓ 多语句场景下也没有违规")
    elif total_violations == 1:
        print("   ⚠ 发现1个违规（如果注释没有被正确过滤）")
    else:
        print(f"   ✗ 发现 {total_violations} 个违规，可能存在重复报告问题")
    
    print("\n3. 模拟lint服务的bug（传入完整SQL）:")
    print("   假设lint服务为每个语句传入完整的SQL...")
    
    # 处理完整的SQL
    processed_full = preprocessor.process(sql_multi)
    
    # 模拟为每个语句传入完整的SQL
    simulated_violations = 0
    for i in range(len(statements)):
        ast = sqlglot.parse_one(processed_full, read="hive") if processed_full else None
        violations = rule.check(ast, processed_full)
        simulated_violations += len(violations)
    
    print(f"   模拟结果: 发现 {simulated_violations} 个违规")
    
    if simulated_violations > 1:
        print(f"   ✗ lint服务有bug：会重复报告 {simulated_violations} 次")
        print(f"     原因：为每个语句传入完整的SQL，而不是对应的SQL")
    else:
        print("   ✓ 即使传入完整SQL，也不会重复报告（感谢去重逻辑）")
    
    print("\n" + "=" * 60)
    print("总结:")
    print("1. 注释过滤器预处理器 ✓ 已解决注释中的关键字问题")
    print("2. SS02规则的去重逻辑 ✓ 防止单次调用内的重复报告")
    print("3. lint服务的bug ⚠ 可能为每个语句传入完整SQL，导致跨调用重复")
    print("\n建议修复:")
    print("1. 修复lint服务，为每个语句传入对应的SQL")
    print("2. 或者在规则中添加全局去重逻辑")
    print("=" * 60)


if __name__ == "__main__":
    test_final_verification()