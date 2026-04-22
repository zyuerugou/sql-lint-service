#!/usr/bin/env python3
# coding=utf-8
"""
测试如何获取每个语句的SQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot


def test_get_statement_sql():
    """测试如何获取每个语句的SQL"""
    # 多语句SQL
    sql = """SELECT * FROM table1;
SELECT * FROM table2;
SELECT * FROM users -- id in ('ncp', 'nad');
SELECT * FROM table3;"""
    
    print("原始SQL:")
    print(sql)
    print()
    
    # 方法1：使用sqlglot.parse
    print("方法1：使用sqlglot.parse")
    try:
        asts = sqlglot.parse(sql, read="hive")
        print(f"解析出 {len(asts)} 个AST")
        for i, ast in enumerate(asts, 1):
            sql_str = ast.sql()
            print(f"  AST {i}: {sql_str}")
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n方法2：手动分割")
    statements = sql.split(';')
    statements = [s.strip() for s in statements if s.strip()]
    print(f"分割出 {len(statements)} 个语句")
    for i, stmt in enumerate(statements, 1):
        print(f"  语句 {i}: {stmt}")
    
    print("\n方法3：使用sqlglot分割")
    try:
        # sqlglot可以分割SQL语句
        from sqlglot import expressions as exp
        parsed = sqlglot.parse(sql, read="hive")
        print(f"解析出 {len(parsed)} 个语句")
    except Exception as e:
        print(f"  失败: {e}")
    
    print("\n方法4：获取AST的原始SQL位置")
    # 尝试解析单个语句
    single_sql = "SELECT * FROM users -- id in ('ncp', 'nad')"
    ast = sqlglot.parse_one(single_sql, read="hive")
    print(f"单个语句: {single_sql}")
    print(f"AST的SQL: {ast.sql()}")
    print(f"注意：sqlglot将行注释 -- 转换成了块注释 /* */")


if __name__ == "__main__":
    test_get_statement_sql()