#!/usr/bin/env python3
"""
SS01规则测试 - 禁止使用 SELECT *
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_rule_ss01():
    """测试SS01规则：禁止使用 SELECT *"""
    print("=" * 60)
    print("SS01规则测试 - 禁止使用 SELECT *")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 测试用例
    test_cases = [
        {
            "sql": "SELECT * FROM users",
            "description": "应该触发SS01规则（使用SELECT *）",
            "expected_rule": "SS01",
            "should_trigger": True
        },
        {
            "sql": "select * from users",
            "description": "应该触发SS01规则（使用SELECT *，关键字小写）",
            "expected_rule": "SS01",
            "should_trigger": True
        },
        {
            "sql": "SELECT id, name FROM users",
            "description": "不应该触发SS01规则（没有使用SELECT *）",
            "expected_rule": "SS01",
            "should_trigger": False
        },
        {
            "sql": "select id, name from users",
            "description": "不应该触发SS01规则（没有使用SELECT *，关键字小写）",
            "expected_rule": "SS01",
            "should_trigger": False
        },
        {
            "sql": "SELECT * FROM orders WHERE status = 'active'",
            "description": "应该触发SS01规则（使用SELECT *，带WHERE条件）",
            "expected_rule": "SS01",
            "should_trigger": True
        },
        {
            "sql": "SELECT id, * FROM users",
            "description": "应该触发SS01规则（混合使用，包含*）",
            "expected_rule": "SS01",
            "should_trigger": True
        },
        {
            "sql": "SELECT COUNT(*) FROM users",
            "description": "应该触发SS01规则（COUNT(*)包含*）",
            "expected_rule": "SS01",
            "should_trigger": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了SS01规则
        has_ss01 = any(item['rule_id'] == 'SS01' for item in result)
        
        if has_ss01 == test_case['should_trigger']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发SS01: {'是' if has_ss01 else '否'}")
        print(f"预期触发: {'是' if test_case['should_trigger'] else '否'}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == 'SS01':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("[PASS] 所有SS01规则测试通过")
        return True
    else:
        print("[FAIL] 部分SS01规则测试失败")
        return False

def test_rule_ss01_edge_cases():
    """测试SS01规则边界情况"""
    print("\n" + "=" * 60)
    print("SS01规则边界情况测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    edge_cases = [
        {
            "sql": "SELECT *",
            "description": "只有SELECT *，没有FROM子句"
        },
        {
            "sql": "SELECT * FROM (SELECT * FROM users) AS subquery",
            "description": "子查询中使用SELECT *"
        },
        {
            "sql": "INSERT INTO users SELECT * FROM old_users",
            "description": "INSERT ... SELECT中使用SELECT *"
        },
        {
            "sql": "CREATE TABLE new_table AS SELECT * FROM old_table",
            "description": "CREATE TABLE AS中使用SELECT *"
        }
    ]
    
    for case in edge_cases:
        print(f"\n边界测试: {case['description']}")
        print(f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        has_ss01 = any(item['rule_id'] == 'SS01' for item in result)
        
        print(f"触发SS01: {'是' if has_ss01 else '否'}")
        
        if has_ss01:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == 'SS01':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print("SS01规则边界情况测试完成")

if __name__ == "__main__":
    # 运行SS01规则测试
    success = test_rule_ss01()
    
    # 运行边界情况测试
    test_rule_ss01_edge_cases()
    
    # 返回退出码
    sys.exit(0 if success else 1)