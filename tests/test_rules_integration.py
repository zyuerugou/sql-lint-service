#!/usr/bin/env python3
"""
规则集成测试 - 测试多个规则的交互
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_rules_integration():
    """测试多个规则的集成和交互"""
    print("=" * 60)
    print("规则集成测试 - 测试多个规则的交互")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 集成测试用例
    test_cases = [
        {
            "sql": "SELECT * FROM users",
            "description": "应该触发SS01，不触发SS02（关键字大写）",
            "expected_rules": ["SS01"]
        },
        {
            "sql": "select * from users",
            "description": "应该触发SS01和SS02（关键字小写）",
            "expected_rules": ["SS01", "SS02"]
        },
        {
            "sql": "SELECT id, name FROM users",
            "description": "不应该触发任何规则",
            "expected_rules": []
        },
        {
            "sql": "select id, name from users",
            "description": "应该触发SS02，不触发SS01",
            "expected_rules": ["SS02"]
        },
        {
            "sql": "Select * From users",
            "description": "应该触发SS01和SS02（关键字不是全大写）",
            "expected_rules": ["SS01", "SS02"]
        },
        {
            "sql": "SELECT * FROM orders WHERE status = 'active'",
            "description": "应该触发SS01，不触发SS02",
            "expected_rules": ["SS01"]
        },
        {
            "sql": "select * from orders where status = 'active'",
            "description": "应该触发SS01和SS02",
            "expected_rules": ["SS01", "SS02"]
        },
        {
            "sql": "UPDATE users SET name = 'test' WHERE id = 1",
            "description": "不应该触发任何规则",
            "expected_rules": []
        },
        {
            "sql": "update users set name = 'test' where id = 1",
            "description": "应该触发SS02",
            "expected_rules": ["SS02"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n集成测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 提取触发的自定义规则
        triggered_rules = []
        for item in result:
            if item['rule_id'] in ['SS01', 'SS02']:
                triggered_rules.append(item['rule_id'])
        
        # 去重并排序
        triggered_rules = sorted(list(set(triggered_rules)))
        expected_rules = sorted(test_case['expected_rules'])
        
        if triggered_rules == expected_rules:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发规则: {triggered_rules}")
        print(f"预期规则: {expected_rules}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if triggered_rules:
            print("详细结果:")
            for item in result:
                if item['rule_id'] in ['SS01', 'SS02']:
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"集成测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("[PASS] 所有集成测试通过")
        return True
    else:
        print("[FAIL] 部分集成测试失败")
        return False

def test_rule_priority():
    """测试规则优先级（如果有多个规则触发）"""
    print("\n" + "=" * 60)
    print("规则优先级测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    priority_cases = [
        {
            "sql": "select * from users",
            "description": "同时触发SS01和SS02",
            "expected_count": 3  # select, *, from 三个问题
        }
    ]
    
    for case in priority_cases:
        print(f"\n优先级测试: {case['description']}")
        print(f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        
        # 统计规则触发情况
        ss01_count = sum(1 for item in result if item['rule_id'] == 'SS01')
        ss02_count = sum(1 for item in result if item['rule_id'] == 'SS02')
        total_custom = ss01_count + ss02_count
        
        print(f"SS01触发次数: {ss01_count}")
        print(f"SS02触发次数: {ss02_count}")
        print(f"自定义规则总触发次数: {total_custom}")
        
        # 显示所有结果
        if result:
            print("所有触发结果:")
            for item in result:
                print(f"  - {item['rule_id']}: {item['message']} (行: {item['line']}, 列: {item['column']})")
    
    print("\n" + "=" * 60)
    print("规则优先级测试完成")

def test_no_rules_scenario():
    """测试没有规则触发的场景"""
    print("\n" + "=" * 60)
    print("无规则触发场景测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    no_rules_cases = [
        {
            "sql": "SELECT id, name FROM users",
            "description": "标准SELECT查询，没有*，关键字大写"
        },
        {
            "sql": "UPDATE users SET name = 'test' WHERE id = 1",
            "description": "标准UPDATE查询，关键字大写"
        },
        {
            "sql": "DELETE FROM users WHERE id = 1",
            "description": "标准DELETE查询，关键字大写"
        },
        {
            "sql": "INSERT INTO users (id, name) VALUES (1, 'test')",
            "description": "标准INSERT查询，关键字大写"
        },
        {
            "sql": "CREATE TABLE test (id INT, name VARCHAR(100))",
            "description": "CREATE TABLE语句，关键字大写"
        },
        {
            "sql": "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            "description": "ALTER TABLE语句，关键字大写"
        }
    ]
    
    all_pass = True
    
    for case in no_rules_cases:
        print(f"\n无规则测试: {case['description']}")
        print(f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        
        # 检查是否触发了任何自定义规则
        has_custom_rules = any(item['rule_id'] in ['SS01', 'SS02'] for item in result)
        
        if not has_custom_rules:
            status = "PASS"
            print(f"[{status}] 没有触发自定义规则（正确）")
        else:
            status = "FAIL"
            all_pass = False
            print(f"[{status}] 触发了自定义规则（错误）")
            
            # 显示触发的规则
            custom_items = [item for item in result if item['rule_id'] in ['SS01', 'SS02']]
            for item in custom_items:
                print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("[PASS] 所有无规则场景测试通过")
    else:
        print("[FAIL] 部分无规则场景测试失败")
    
    return all_pass

if __name__ == "__main__":
    # 运行集成测试
    integration_success = test_rules_integration()
    
    # 运行规则优先级测试
    test_rule_priority()
    
    # 运行无规则场景测试
    no_rules_success = test_no_rules_scenario()
    
    # 返回退出码
    overall_success = integration_success and no_rules_success
    sys.exit(0 if overall_success else 1)