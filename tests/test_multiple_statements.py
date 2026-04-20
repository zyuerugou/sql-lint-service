#!/usr/bin/env python3
# coding=utf-8
"""
多语句SQL测试 - 测试多个SQL语句（分号分隔）一次性传入的效果
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_multiple_statements_basic():
    """测试基本的多语句SQL"""
    print("=" * 60)
    print("多语句SQL测试 - 基本功能")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "description": "两个查询语句，都触发SS01规则",
            "sql": """SELECT * FROM users;
SELECT * FROM orders;""",
            "expected_rules": ["SS01", "SS01"],
            "expected_line_numbers": [1, 2]
        },
        {
            "description": "混合大小写查询语句",
            "sql": """SELECT id, name FROM users;
select * from orders;""",
            "expected_rules": ["SS02", "SS01", "SS02"],  # select触发SS02，*触发SS01，from触发SS02
            "expected_line_numbers": [2, 2, 2]  # 都在第二行
        },
        {
            "description": "正确查询和错误查询混合",
            "sql": """SELECT id, name FROM users;
SELECT * FROM orders;
select id, name from customers;""",
            "expected_rules": ["SS01", "SS02", "SS02"],  # 第二行SS01，第三行两个SS02
            "expected_line_numbers": [2, 3, 3]
        },
        {
            "description": "包含SET语句的混合语句",
            "sql": """set hive.exec.dynamic.partition=true;
SELECT * FROM users;
set tez.queue.name=default;
select id, name from orders;""",
            "expected_rules": ["SS01", "SS02", "SS02"],  # 第二行SS01，第四行两个SS02
            "expected_line_numbers": [2, 4, 4]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL:\n{test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 获取触发的规则和行号
        triggered_rules = [item['rule_id'] for item in result]
        line_numbers = [item['line'] for item in result]
        
        # 检查规则触发情况
        rules_match = sorted(triggered_rules) == sorted(test_case['expected_rules'])
        
        # 检查行号（允许顺序不同）
        lines_match = sorted(line_numbers) == sorted(test_case['expected_line_numbers'])
        
        if rules_match and lines_match:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发规则: {triggered_rules} (预期: {test_case['expected_rules']})")
        print(f"触发行号: {line_numbers} (预期: {test_case['expected_line_numbers']})")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - 行{item['line']}: {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"基本多语句测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

def test_multiple_statements_complex():
    """测试复杂的多语句SQL"""
    print("\n" + "=" * 60)
    print("多语句SQL测试 - 复杂场景")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "description": "包含空行和注释的多语句",
            "sql": """-- 这是一个注释
SELECT * FROM users;

-- 另一个注释
SELECT id, name FROM users;

select * from orders;""",
            "expected_rules": ["SS01", "SS02", "SS01", "SS02"],  # 第二行SS01，第七行SS02、SS01、SS02
            "expected_line_numbers": [2, 7, 7, 7]
        },
        {
            "description": "不同语句类型混合",
            "sql": """CREATE TABLE users (id INT, name VARCHAR(100));
INSERT INTO users VALUES (1, 'Alice');
SELECT * FROM users;
UPDATE users SET name = 'Bob' WHERE id = 1;
DELETE FROM users WHERE id = 1;""",
            "expected_rules": ["SS01"],
            "expected_line_numbers": [3]  # 只有SELECT *触发规则
        },
        {
            "description": "包含SS03规则的多语句",
            "sql": """SELECT UserID, UserName FROM UserTable;
select userid, username from usertable;
SELECT userid, username FROM usertable;""",
            "expected_rules": ["SS03", "SS03", "SS03", "SS02", "SS02"],  # 第一行三个SS03，第二行两个SS02
            "expected_line_numbers": [1, 1, 1, 2, 2]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL (前50字符): {test_case['sql'][:50]}..." if len(test_case['sql']) > 50 else f"SQL:\n{test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 获取触发的规则和行号
        triggered_rules = [item['rule_id'] for item in result]
        line_numbers = [item['line'] for item in result]
        
        # 检查规则触发情况
        rules_match = sorted(triggered_rules) == sorted(test_case['expected_rules'])
        
        # 检查行号（允许顺序不同）
        lines_match = sorted(line_numbers) == sorted(test_case['expected_line_numbers'])
        
        if rules_match and lines_match:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发规则: {triggered_rules} (预期: {test_case['expected_rules']})")
        print(f"触发行号: {line_numbers} (预期: {test_case['expected_line_numbers']})")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - 行{item['line']}: {item['rule_id']}: {item['message']}")
        else:
            print("详细结果: 无")
    
    print("\n" + "=" * 60)
    print(f"复杂多语句测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

def test_multiple_statements_edge_cases():
    """测试边界情况的多语句SQL"""
    print("\n" + "=" * 60)
    print("多语句SQL测试 - 边界情况")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "description": "只有分号没有语句",
            "sql": ";;;",
            "expected_rules": [],  # 不期望PRS（系统规则）
            "expected_line_numbers": []
        },
        {
            "description": "空语句",
            "sql": "",
            "expected_rules": [],
            "expected_line_numbers": []
        },
        {
            "description": "只有注释",
            "sql": """-- 注释1
-- 注释2
/* 多行注释 */""",
            "expected_rules": [],
            "expected_line_numbers": []
        },
        {
            "description": "语句末尾没有分号",
            "sql": """SELECT * FROM users
SELECT id, name FROM users""",
            "expected_rules": ["SS01"],  # 只期望SS01
            "expected_line_numbers": [1]
        },
        {
            "description": "混合分号使用",
            "sql": """SELECT * FROM users;
SELECT id, name FROM users
select * from orders;""",
            "expected_rules": ["SS01"],  # 只期望SS01
            "expected_line_numbers": [1]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL:\n{repr(test_case['sql'])}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 获取触发的规则和行号
        triggered_rules = [item['rule_id'] for item in result]
        line_numbers = [item['line'] for item in result]
        
        # 检查规则触发情况
        rules_match = sorted(triggered_rules) == sorted(test_case['expected_rules'])
        
        # 检查行号（允许顺序不同）
        lines_match = sorted(line_numbers) == sorted(test_case['expected_line_numbers'])
        
        if rules_match and lines_match:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发规则: {triggered_rules} (预期: {test_case['expected_rules']})")
        print(f"触发行号: {line_numbers} (预期: {test_case['expected_line_numbers']})")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - 行{item['line']}: {item['rule_id']}: {item['message']}")
        else:
            print("详细结果: 无")
    
    print("\n" + "=" * 60)
    print(f"边界情况测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

def test_line_number_preservation():
    """测试行号保持功能（特别是SET语句过滤后）"""
    print("\n" + "=" * 60)
    print("多语句SQL测试 - 行号保持功能")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    # 测试SET语句过滤后行号是否正确
    sql = """set hive.exec.dynamic.partition=true;
set hive.exec.dynamic.partition.mode=nonstrict;
SELECT * FROM users;
set tez.queue.name=default;
select id, name from orders;"""
    
    print("测试SQL:")
    lines = sql.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"  行{i}: {line}")
    
    result = service.lint_sql(sql)
    
    print(f"\nlint结果:")
    if result:
        for item in result:
            print(f"  - 行{item['line']}: {item['rule_id']}: {item['message']}")
        
        # 检查行号是否正确
        expected_lines = [3, 5, 5]  # 第3行SELECT *，第5行select小写（两个SS02）
        actual_lines = sorted([item['line'] for item in result])
        
        if actual_lines == expected_lines:
            print(f"\n[PASS] 行号保持正确: {actual_lines} (预期: {expected_lines})")
            return True
        else:
            print(f"\n[FAIL] 行号不正确: {actual_lines} (预期: {expected_lines})")
            return False
    else:
        print("  无结果")
        return False

if __name__ == "__main__":
    # 运行所有多语句测试
    basic_success = test_multiple_statements_basic()
    complex_success = test_multiple_statements_complex()
    edge_success = test_multiple_statements_edge_cases()
    line_success = test_line_number_preservation()
    
    print("\n" + "=" * 60)
    print("多语句SQL测试总结")
    print("=" * 60)
    print(f"基本功能测试: {'通过' if basic_success else '失败'}")
    print(f"复杂场景测试: {'通过' if complex_success else '失败'}")
    print(f"边界情况测试: {'通过' if edge_success else '失败'}")
    print(f"行号保持测试: {'通过' if line_success else '失败'}")
    
    overall_success = basic_success and complex_success and edge_success and line_success
    print(f"\n总体结果: {'所有测试通过' if overall_success else '有测试失败'}")
    
    # 返回退出码
    sys.exit(0 if overall_success else 1)