#!/usr/bin/env python3
# coding=utf-8
"""
测试规则功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def test_rules_functionality():
    """测试规则功能"""
    from app.services.lint_service import LintService
    
    print("=" * 60)
    print("测试规则功能")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 获取加载的规则
    rules = service.get_loaded_rules()
    print(f"加载的规则: {rules}")
    
    # 测试用例
    test_cases = [
        {
            "sql": "SELECT * FROM users",
            "description": "应该触发SS01（禁止SELECT *），但不触发SS02（关键字已大写）",
            "expected_rules": ["SS01"]
        },
        {
            "sql": "select * from users",
            "description": "应该触发SS01（禁止SELECT *）和SS02（关键字小写）",
            "expected_rules": ["SS01", "SS02"]
        },
        {
            "sql": "SELECT id, name FROM users",
            "description": "不应该触发SS01（没有*），也不触发SS02（关键字已大写）",
            "expected_rules": []
        },
        {
            "sql": "select id, name from users",
            "description": "应该触发SS02（关键字小写），但不触发SS01（没有*）",
            "expected_rules": ["SS02"]
        },
        {
            "sql": "SELECT * FROM orders WHERE status = 'active'",
            "description": "应该触发SS01（禁止SELECT *），但不触发SS02（关键字已大写）",
            "expected_rules": ["SS01"]
        },
        {
            "sql": "UPDATE users SET name = 'test' WHERE id = 1",
            "description": "不应该触发SS02（关键字已大写）",
            "expected_rules": []
        },
        {
            "sql": "DELETE FROM users WHERE id = 1",
            "description": "不应该触发SS02（关键字已大写）",
            "expected_rules": []
        },
        {
            "sql": "update users set name = 'test' where id = 1",
            "description": "应该触发SS02（关键字小写）",
            "expected_rules": ["SS02"]
        },
        {
            "sql": "delete from users where id = 1",
            "description": "应该触发SS02（关键字小写）",
            "expected_rules": ["SS02"]
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 提取自定义规则
        triggered_rules = []
        for item in result:
            if item['rule_id'] in ['SS01', 'SS02']:
                triggered_rules.append(item['rule_id'])
        
        # 去重并排序
        triggered_rules = sorted(list(set(triggered_rules)))
        expected_rules = sorted(test_case['expected_rules'])
        
        print(f"预期规则: {expected_rules}")
        print(f"触发规则: {triggered_rules}")
        
        if triggered_rules == expected_rules:
            print("[PASS] 规则触发符合预期")
        else:
            print("[FAIL] 规则触发不符合预期")
            all_passed = False
        
        # 显示详细结果
        if triggered_rules:
            print("详细结果:")
            for item in result:
                if item['rule_id'] in ['SS01', 'SS02']:
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败！")
    print("=" * 60)
    
    return all_passed

def test_rule_details():
    """测试规则详细信息"""
    print("\n" + "=" * 60)
    print("测试规则详细信息")
    print("=" * 60)
    
    from app.services.lint_service import LintService
    
    service = LintService(enable_hot_reload=False)
    
    # 测试SS01规则详细信息
    print("\n测试SS01规则（禁止SELECT *）:")
    sql_with_star = "SELECT * FROM users"
    sql_without_star = "SELECT id, name FROM users"
    
    result_with_star = service.lint_sql(sql_with_star)
    result_without_star = service.lint_sql(sql_without_star)
    
    ss01_in_with_star = any(item['rule_id'] == 'SS01' for item in result_with_star)
    ss01_in_without_star = any(item['rule_id'] == 'SS01' for item in result_without_star)
    
    print(f"SQL: {sql_with_star}")
    print(f"触发SS01: {'是' if ss01_in_with_star else '否'}")
    
    print(f"\nSQL: {sql_without_star}")
    print(f"触发SS01: {'是' if ss01_in_without_star else '否'}")
    
    # 测试SS02规则详细信息
    print("\n测试SS02规则（SQL关键字必须大写）:")
    sql_uppercase = "SELECT * FROM users"
    sql_lowercase = "select * from users"
    sql_mixed = "Select * From users"
    
    result_uppercase = service.lint_sql(sql_uppercase)
    result_lowercase = service.lint_sql(sql_lowercase)
    result_mixed = service.lint_sql(sql_mixed)
    
    ss02_in_uppercase = any(item['rule_id'] == 'SS02' for item in result_uppercase)
    ss02_in_lowercase = any(item['rule_id'] == 'SS02' for item in result_lowercase)
    ss02_in_mixed = any(item['rule_id'] == 'SS02' for item in result_mixed)
    
    print(f"SQL: {sql_uppercase}")
    print(f"触发SS02: {'是' if ss02_in_uppercase else '否'} (预期: 否，因为关键字已大写)")
    
    print(f"\nSQL: {sql_lowercase}")
    print(f"触发SS02: {'是' if ss02_in_lowercase else '否'} (预期: 是，因为关键字小写)")
    
    print(f"\nSQL: {sql_mixed}")
    print(f"触发SS02: {'是' if ss02_in_mixed else '否'} (预期: 是，因为关键字不是全大写)")

if __name__ == "__main__":
    # 测试规则功能
    test_rules_functionality()
    
    # 测试规则详细信息
    test_rule_details()