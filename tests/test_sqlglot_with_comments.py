#!/usr/bin/env python3
# coding=utf-8
"""
测试sqlglot处理带注释的SQL
"""

import sqlglot


def test_sqlglot_with_comments():
    """测试sqlglot处理带注释的SQL"""
    test_cases = [
        ("SELECT * FROM users -- id in ('ncp', 'nad')", "单行注释"),
        ("SELECT * FROM users -- id in ('ncp', 'nad');", "单行注释带分号"),
        ("SELECT 1;\nSELECT * FROM users -- id in ('ncp', 'nad');\nSELECT 3", "多语句带注释"),
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
            # 打印详细错误
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_sqlglot_with_comments()