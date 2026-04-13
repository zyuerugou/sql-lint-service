#!/usr/bin/env python3
"""
SS02规则测试 - SQL关键字必须大写
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_rule_ss02():
    """测试SS02规则：SQL关键字必须大写"""
    print("=" * 60)
    print("SS02规则测试 - SQL关键字必须大写")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 测试用例
    test_cases = [
        {
            "sql": "SELECT id, name FROM users",
            "description": "不应该触发SS02规则（关键字已大写）",
            "expected_rule": "SS02",
            "should_trigger": False
        },
        {
            "sql": "select id, name from users",
            "description": "应该触发SS02规则（关键字小写）",
            "expected_rule": "SS02",
            "should_trigger": True
        },
        {
            "sql": "Select id, name From users",
            "description": "应该触发SS02规则（关键字首字母大写）",
            "expected_rule": "SS02",
            "should_trigger": True
        },
        {
            "sql": "SELECT * FROM users WHERE id = 1",
            "description": "不应该触发SS02规则（所有关键字大写）",
            "expected_rule": "SS02",
            "should_trigger": False
        },
        {
            "sql": "select * from users where id = 1",
            "description": "应该触发SS02规则（所有关键字小写）",
            "expected_rule": "SS02",
            "should_trigger": True
        },
        {
            "sql": "UPDATE users SET name = 'test' WHERE id = 1",
            "description": "不应该触发SS02规则（UPDATE语句关键字大写）",
            "expected_rule": "SS02",
            "should_trigger": False
        },
        {
            "sql": "update users set name = 'test' where id = 1",
            "description": "应该触发SS02规则（UPDATE语句关键字小写）",
            "expected_rule": "SS02",
            "should_trigger": True
        },
        {
            "sql": "DELETE FROM users WHERE id = 1",
            "description": "不应该触发SS02规则（DELETE语句关键字大写）",
            "expected_rule": "SS02",
            "should_trigger": False
        },
        {
            "sql": "delete from users where id = 1",
            "description": "应该触发SS02规则（DELETE语句关键字小写）",
            "expected_rule": "SS02",
            "should_trigger": True
        },
        {
            "sql": "INSERT INTO users (id, name) VALUES (1, 'test')",
            "description": "不应该触发SS02规则（INSERT语句关键字大写）",
            "expected_rule": "SS02",
            "should_trigger": False
        },
        {
            "sql": "insert into users (id, name) values (1, 'test')",
            "description": "应该触发SS02规则（INSERT语句关键字小写）",
            "expected_rule": "SS02",
            "should_trigger": True
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了SS02规则
        has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
        
        if has_ss02 == test_case['should_trigger']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发SS02: {'是' if has_ss02 else '否'}")
        print(f"预期触发: {'是' if test_case['should_trigger'] else '否'}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result and has_ss02:
            print("详细结果:")
            ss02_items = [item for item in result if item['rule_id'] == 'SS02']
            for item in ss02_items:
                print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("[PASS] 所有SS02规则测试通过")
        return True
    else:
        print("[FAIL] 部分SS02规则测试失败")
        return False

def test_rule_ss02_keyword_details():
    """测试SS02规则关键字详细情况"""
    print("\n" + "=" * 60)
    print("SS02规则关键字详细测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    # 测试各种SQL关键字
    keywords_test = [
        ("SELECT", "SELECT关键字大写"),
        ("select", "SELECT关键字小写"),
        ("Select", "SELECT关键字首字母大写"),
        ("FROM", "FROM关键字大写"),
        ("from", "FROM关键字小写"),
        ("From", "FROM关键字首字母大写"),
        ("WHERE", "WHERE关键字大写"),
        ("where", "WHERE关键字小写"),
        ("Where", "WHERE关键字首字母大写"),
        ("AND", "AND关键字大写"),
        ("and", "AND关键字小写"),
        ("And", "AND关键字首字母大写"),
        ("OR", "OR关键字大写"),
        ("or", "OR关键字小写"),
        ("Or", "OR关键字首字母大写"),
        ("ORDER BY", "ORDER BY关键字大写"),
        ("order by", "ORDER BY关键字小写"),
        ("Order By", "ORDER BY关键字首字母大写"),
        ("GROUP BY", "GROUP BY关键字大写"),
        ("group by", "GROUP BY关键字小写"),
        ("Group By", "GROUP BY关键字首字母大写")
    ]
    
    for keyword, description in keywords_test:
        sql = f"{keyword} * FROM users" if keyword in ["SELECT", "select", "Select"] else f"SELECT * FROM users {keyword} id"
        
        print(f"\n关键字测试: {description}")
        print(f"SQL: {sql}")
        
        result = service.lint_sql(sql)
        has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
        
        # 判断是否应该触发（只有全大写不触发）
        should_trigger = not keyword.isupper()
        
        status = "PASS" if has_ss02 == should_trigger else "FAIL"
        print(f"触发SS02: {'是' if has_ss02 else '否'}")
        print(f"预期触发: {'是' if should_trigger else '否'}")
        print(f"[{status}]")
    
    print("\n" + "=" * 60)
    print("SS02规则关键字详细测试完成")

def test_rule_ss02_mixed_cases():
    """测试SS02规则混合大小写情况"""
    print("\n" + "=" * 60)
    print("SS02规则混合大小写测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    mixed_cases = [
        {
            "sql": "SeLeCt * FrOm UsErS WhErE iD = 1",
            "description": "混合大小写关键字"
        },
        {
            "sql": "sElEcT * fRoM uSeRs wHeRe iD = 1",
            "description": "混合大小写关键字（主要小写）"
        },
        {
            "sql": "SELECT id, name FROM users WHERE status = 'active' ORDER BY created_at DESC",
            "description": "所有关键字大写（长查询）"
        },
        {
            "sql": "select id, name from users where status = 'active' order by created_at desc",
            "description": "所有关键字小写（长查询）"
        },
        {
            "sql": "Select id, name From users Where status = 'active' Order By created_at Desc",
            "description": "所有关键字首字母大写（长查询）"
        }
    ]
    
    for case in mixed_cases:
        print(f"\n混合大小写测试: {case['description']}")
        print(f"SQL: {case['sql'][:50]}..." if len(case['sql']) > 50 else f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
        
        # 判断是否应该触发（检查是否所有关键字都是大写）
        # 简化判断：如果SQL包含小写字母且不是值部分，则可能触发
        sql_lower = case['sql'].lower()
        sql_upper = case['sql'].upper()
        
        # 简单判断：如果SQL不等于全大写版本，则可能触发
        should_trigger = case['sql'] != sql_upper
        
        status = "PASS" if has_ss02 == should_trigger else "FAIL"
        print(f"触发SS02: {'是' if has_ss02 else '否'}")
        print(f"预期触发: {'是' if should_trigger else '否'}")
        print(f"[{status}]")
        
        if has_ss02:
            ss02_items = [item for item in result if item['rule_id'] == 'SS02']
            print(f"触发次数: {len(ss02_items)}")
    
    print("\n" + "=" * 60)
    print("SS02规则混合大小写测试完成")

if __name__ == "__main__":
    # 运行SS02规则测试
    success = test_rule_ss02()
    
    # 运行关键字详细测试
    test_rule_ss02_keyword_details()
    
    # 运行混合大小写测试
    test_rule_ss02_mixed_cases()
    
    # 返回退出码
    sys.exit(0 if success else 1)