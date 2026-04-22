#!/usr/bin/env python3
# coding=utf-8
"""
测试SetStatementFilterPreprocessor功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.rules.preprocessors.set_statement_filter_preprocessor import SetStatementFilterPreprocessor


def test_set_statement_filter():
    """测试SET语句过滤器预处理器"""
    print("=" * 60)
    print("测试SetStatementFilterPreprocessor功能")
    print("=" * 60)
    
    preprocessor = SetStatementFilterPreprocessor()
    
    test_cases = [
        {
            "name": "测试1: 简单SET语句过滤",
            "sql": """SELECT * FROM users;
set hivevar:prompt;
SELECT id FROM orders;""",
            "expected": """SELECT * FROM users;

SELECT id FROM orders;"""
        },
        {
            "name": "测试2: 多种SET语句过滤",
            "sql": """-- 注释行
set hive.exec.dynamic.partition.mode=nonstrict;
SELECT * FROM table1;
set tez.queue.name=default;
INSERT INTO table2 SELECT * FROM table1;""",
            "expected": """-- 注释行

SELECT * FROM table1;

INSERT INTO table2 SELECT * FROM table1;"""
        },
        {
            "name": "测试3: SET语句带分号",
            "sql": """SELECT 1;
set hivevar:prompt;
SELECT 2;""",
            "expected": """SELECT 1;

SELECT 2;"""
        },
        {
            "name": "测试4: SET语句带尾随注释",
            "sql": """SELECT * FROM a;
set hivevar:prompt; -- 设置提示
SELECT * FROM b;""",
            "expected": """SELECT * FROM a;

SELECT * FROM b;"""
        },
        {
            "name": "测试5: 非SET语句保持不变",
            "sql": """SELECT * FROM users;
UPDATE users SET name='test' WHERE id=1;
INSERT INTO logs VALUES (1, 'test');""",
            "expected": """SELECT * FROM users;
UPDATE users SET name='test' WHERE id=1;
INSERT INTO logs VALUES (1, 'test');"""
        },
        {
            "name": "测试6: 空行和注释保持",
            "sql": "-- 文件头注释\n\nSELECT * FROM users;\n\nset hivevar:prompt;\n\n-- 中间注释\nSELECT id FROM orders;",
            "expected": "-- 文件头注释\n\nSELECT * FROM users;\n\n\n\n-- 中间注释\nSELECT id FROM orders;"
        },
        {
            "name": "测试7: 大小写混合SET语句",
            "sql": """SELECT 1;
SET hivevar:prompt;
Set tez.queue.name=default;
sEt hive.exec.parallel=true;
SELECT 2;""",
            "expected": """SELECT 1;



SELECT 2;"""
        },
        {
            "name": "测试8: 包含特定值的SET语句",
            "sql": """SELECT * FROM a;
set hive.exec.dynamic.partition.mode=nonstrict;
set hive.cbo.enable=true;
set unknown.param=none;
SELECT * FROM b;""",
            "expected": """SELECT * FROM a;



SELECT * FROM b;"""
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print(f"输入SQL:\n{test_case['sql']}")
        
        result = preprocessor.process(test_case['sql'])
        expected = test_case['expected']
        
        print(f"预期输出:\n{expected}")
        print(f"实际输出:\n{result}")
        
        if result == expected:
            print("[PASS] 测试通过")
        else:
            print("[FAIL] 测试失败")
            print(f"差异:")
            # 显示行差异
            result_lines = result.split('\n')
            expected_lines = expected.split('\n')
            for i, (r, e) in enumerate(zip(result_lines, expected_lines)):
                if r != e:
                    print(f"  行{i+1}: 预期={repr(e)}, 实际={repr(r)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[PASS] 所有测试通过")
    else:
        print("[FAIL] 部分测试失败")
    
    return all_passed


def test_line_number_preservation():
    """测试行号保持功能"""
    print("\n" + "=" * 60)
    print("测试行号保持功能")
    print("=" * 60)
    
    preprocessor = SetStatementFilterPreprocessor()
    
    # 创建一个SQL，SET语句在行首（符合实际场景）
    sql_lines = [
        "SELECT * FROM users;",
        "set hivevar:prompt;",
        "SELECT id FROM orders;",
        "",
        "-- 注释",
        "set tez.queue.name=default;",
        "INSERT INTO logs VALUES (1);"
    ]
    
    sql = '\n'.join(sql_lines)
    print(f"原始SQL:\n{sql}")
    
    result = preprocessor.process(sql)
    result_lines = result.split('\n')
    
    print(f"\n处理后的SQL:\n{result}")
    
    # 检查行数是否相同
    if len(result_lines) == len(sql_lines):
        print("[PASS] 行数保持正确")
    else:
        print(f"[FAIL] 行数不匹配: 原始={len(sql_lines)}, 处理后={len(result_lines)}")
    
    # 检查SET语句行是否为空
    expected_empty_lines = {1, 5}  # 第2行和第6行应该是空行（0-based索引）
    for i, line in enumerate(result_lines):
        if i in expected_empty_lines:
            if line.strip() == "":
                print(f"[PASS] 行{i+1}正确替换为空行")
            else:
                print(f"[FAIL] 行{i+1}应该为空行，实际为: {repr(line)}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试边界情况")
    print("=" * 60)
    
    preprocessor = SetStatementFilterPreprocessor()
    
    edge_cases = [
        {
            "name": "空SQL",
            "sql": "",
            "expected": ""
        },
        {
            "name": "只有SET语句",
            "sql": "set hivevar:prompt;",
            "expected": ""
        },
        {
            "name": "只有SET语句带换行",
            "sql": "set hivevar:prompt;\n",
            "expected": "\n"
        },
        {
            "name": "SET语句在行中间（不应该匹配）",
            "sql": "SELECT set_column FROM table;",
            "expected": "SELECT set_column FROM table;"
        },
        {
            "name": "UPDATE语句中的SET子句（不应该匹配）",
            "sql": "UPDATE users SET name='test' WHERE id=1;",
            "expected": "UPDATE users SET name='test' WHERE id=1;"
        }
    ]
    
    for case in edge_cases:
        print(f"\n{case['name']}")
        result = preprocessor.process(case['sql'])
        
        if result == case['expected']:
            print(f"[PASS] 通过: 输入={repr(case['sql'])}, 输出={repr(result)}")
        else:
            print(f"[FAIL] 失败: 输入={repr(case['sql'])}, 预期={repr(case['expected'])}, 实际={repr(result)}")


if __name__ == "__main__":
    test1_passed = test_set_statement_filter()
    test_line_number_preservation()
    test_edge_cases()
    
    if test1_passed:
        print("\n[PASS] SetStatementFilterPreprocessor简化完成，功能正常")
    else:
        print("\n[FAIL] SetStatementFilterPreprocessor测试失败，需要修复")
        sys.exit(1)