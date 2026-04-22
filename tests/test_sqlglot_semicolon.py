#!/usr/bin/env python3
# coding=utf-8
"""
测试sqlglot是否支持分号
"""

import sqlglot


def test_sqlglot_semicolon():
    """测试sqlglot是否支持分号"""
    test_cases = [
        ("SELECT 1", "简单SQL"),
        ("SELECT 1;", "带分号的SQL"),
        ("SELECT 1; SELECT 2", "两个语句用分号分隔"),
        ("SELECT 1;\nSELECT 2", "两个语句用分号和换行分隔"),
        ("SELECT 1;\nSELECT 2;\nSELECT 3", "三个语句"),
    ]
    
    for sql, description in test_cases:
        print(f"\n测试: {description}")
        print(f"SQL: {sql!r}")
        
        try:
            asts = sqlglot.parse(sql, read="hive")
            print(f"  成功! 解析出 {len(asts)} 个语句")
            for i, ast in enumerate(asts, 1):
                print(f"    语句 {i}: {ast.sql()}")
        except Exception as e:
            print(f"  失败: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_sqlglot_semicolon()