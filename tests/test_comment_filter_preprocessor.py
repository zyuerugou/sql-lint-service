#!/usr/bin/env python3
# coding=utf-8
"""
测试注释过滤器预处理器
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.rules.preprocessors.comment_filter_preprocessor import CommentFilterPreprocessor


def test_comment_filter_preprocessor():
    """测试注释过滤器预处理器"""
    print("=" * 60)
    print("测试注释过滤器预处理器")
    print("=" * 60)
    
    preprocessor = CommentFilterPreprocessor()
    print(f"预处理器信息: {preprocessor.get_info()}")
    
    test_cases = [
        {
            "name": "测试1: 行注释",
            "sql": """SELECT * FROM users -- id in ('ncp', 'nad')
WHERE status = 'active';""",
            "expected": """SELECT * FROM users                        
WHERE status = 'active';"""
        },
        {
            "name": "测试2: 块注释（单行）",
            "sql": """SELECT id /* comment with in keyword */ FROM users
WHERE name = 'test';""",
            "expected": """SELECT id                               FROM users
WHERE name = 'test';"""
        },
        {
            "name": "测试3: 块注释（多行）",
            "sql": """SELECT id FROM users
/*
This is a multi-line comment
with select, from, where, in keywords
*/
WHERE status = 'active';""",
            "expected": """SELECT id FROM users




WHERE status = 'active';"""
        },
        {
            "name": "测试4: 混合注释",
            "sql": """-- 文件头注释
SELECT * FROM users -- 行内注释
WHERE id IN (1, 2, 3) /* 块注释 */ AND status = 'active';""",
            "expected": """ 
SELECT * FROM users        
WHERE id IN (1, 2, 3)           AND status = 'active';"""
        },
        {
            "name": "测试5: 注释在字符串中（不应该被替换）",
            "sql": """SELECT * FROM users
WHERE comment = '-- this is not a comment' 
AND description = '/* not a comment either */';""",
            "expected": """SELECT * FROM users
WHERE comment = '-- this is not a comment' 
AND description = '/* not a comment either */';"""
        },
        {
            "name": "测试6: 空行和空白保持",
            "sql": """-- 注释1

SELECT id FROM users;

-- 注释2
/* 块注释 */
SELECT name FROM customers;""",
            "expected": """ 

SELECT id FROM users;


SELECT name FROM customers;"""
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
            max_lines = max(len(result_lines), len(expected_lines))
            for i in range(max_lines):
                r = result_lines[i] if i < len(result_lines) else ""
                e = expected_lines[i] if i < len(expected_lines) else ""
                if r != e:
                    print(f"  行{i+1}: 预期={repr(e)}, 实际={repr(r)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[PASS] 所有测试通过")
    else:
        print("[FAIL] 部分测试失败")
    
    return all_passed


def test_preserve_line_structure():
    """测试行结构保持"""
    print("\n" + "=" * 60)
    print("测试行结构保持")
    print("=" * 60)
    
    preprocessor = CommentFilterPreprocessor()
    
    # 创建一个SQL，确保行数不变
    sql_lines = [
        "SELECT * FROM users;",
        "-- This is a comment",
        "WHERE id = 1;",
        "",
        "/* Another comment */",
        "ORDER BY name;"
    ]
    
    sql = '\n'.join(sql_lines)
    print(f"原始SQL ({len(sql_lines)} 行):")
    print(sql)
    
    result = preprocessor.process(sql)
    result_lines = result.split('\n')
    
    print(f"\n处理后的SQL ({len(result_lines)} 行):")
    print(result)
    
    # 检查行数是否相同
    if len(result_lines) == len(sql_lines):
        print("[PASS] 行数保持正确")
    else:
        print(f"[FAIL] 行数不匹配: 原始={len(sql_lines)}, 处理后={len(result_lines)}")
    
    # 检查每行长度是否相同
    all_lengths_match = True
    for i, (orig, proc) in enumerate(zip(sql_lines, result_lines)):
        if len(orig) != len(proc):
            print(f"[FAIL] 行{i+1}长度不匹配: 原始={len(orig)}, 处理后={len(proc)}")
            all_lengths_match = False
    
    if all_lengths_match:
        print("[PASS] 所有行长度保持正确")


def test_integration_with_ss02():
    """测试与SS02规则的集成"""
    print("\n" + "=" * 60)
    print("测试与SS02规则的集成")
    print("=" * 60)
    
    from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot
    import sqlglot
    
    preprocessor = CommentFilterPreprocessor()
    rule = RuleSs02Sqlglot()
    
    test_cases = [
        {
            "name": "注释中的in关键字",
            "sql": "SELECT * FROM users -- id in ('ncp', 'nad')",
            "should_trigger": False
        },
        {
            "name": "实际SQL中的小写关键字",
            "sql": "select id from users where status in ('active')",
            "should_trigger": True
        },
        {
            "name": "块注释中的关键字",
            "sql": "SELECT id /* comment with in keyword */ FROM users",
            "should_trigger": False
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"原始SQL: {test_case['sql']}")
        
        # 先预处理
        processed_sql = preprocessor.process(test_case['sql'])
        print(f"预处理后: {processed_sql}")
        
        try:
            ast = sqlglot.parse_one(test_case['sql'], read="hive")
            # 注意：规则检查使用预处理后的SQL
            violations = rule.check(ast, processed_sql)
            
            if violations:
                print(f"  触发SS02规则: 是, 违规数: {len(violations)}")
                for v in violations:
                    print(f"    - {v.message}")
                
                if test_case['should_trigger']:
                    print("  结果: [OK] 符合预期")
                else:
                    print("  结果: [ERROR] 不符合预期")
            else:
                print(f"  触发SS02规则: 否")
                
                if not test_case['should_trigger']:
                    print("  结果: [OK] 符合预期")
                else:
                    print("  结果: [ERROR] 不符合预期")
                    
        except Exception as e:
            print(f"  解析失败: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test1_passed = test_comment_filter_preprocessor()
    test_preserve_line_structure()
    test_integration_with_ss02()
    
    if test1_passed:
        print("\n[PASS] 注释过滤器预处理器功能正常")
    else:
        print("\n[FAIL] 注释过滤器预处理器测试失败")
        sys.exit(1)