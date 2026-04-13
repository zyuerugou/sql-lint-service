#!/usr/bin/env python3
# coding=utf-8
"""
SET语句测试 - 验证SS02和SS03规则不检查SET配置语句
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_set_statements_ss02():
    """测试SS02规则不检查SET语句中的关键字"""
    print("=" * 60)
    print("SS02规则SET语句测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "sql": "set hive.exec.dynamic.partition=true;",
            "description": "SET配置语句（小写set）",
            "expected_rule": "SS02",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "SET hive.exec.dynamic.partition=true;",
            "description": "SET配置语句（大写SET）",
            "expected_rule": "SS02",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "Set hive.exec.dynamic.partition=true;",
            "description": "SET配置语句（首字母大写Set）",
            "expected_rule": "SS02",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "select * from users;",
            "description": "普通查询（小写select）",
            "expected_rule": "SS02",
            "should_trigger": True  # 应该触发，因为不是SET语句
        },
        {
            "sql": "SELECT * FROM users;",
            "description": "普通查询（大写SELECT）",
            "expected_rule": "SS02",
            "should_trigger": False  # 不应该触发，因为关键字都是大写
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
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"SS02 SET语句测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

def test_set_statements_ss03():
    """测试SS03规则不检查SET语句中的标识符"""
    print("\n" + "=" * 60)
    print("SS03规则SET语句测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "sql": "set hive.exec.dynamic.partition=true;",
            "description": "SET配置语句（参数包含大写）",
            "expected_rule": "SS03",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "set hivevar:prompt=1;",
            "description": "SET配置语句（变量赋值）",
            "expected_rule": "SS03",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "set character.literal.as.string=true;",
            "description": "SET配置语句（参数包含大写）",
            "expected_rule": "SS03",
            "should_trigger": False  # 不应该触发，因为这是SET配置语句
        },
        {
            "sql": "SELECT UserID FROM UserTable;",
            "description": "普通查询（标识符包含大写）",
            "expected_rule": "SS03",
            "should_trigger": True  # 应该触发，因为不是SET语句
        },
        {
            "sql": "SELECT userid FROM usertable;",
            "description": "普通查询（标识符小写）",
            "expected_rule": "SS03",
            "should_trigger": False  # 不应该触发，因为标识符都是小写
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了SS03规则
        has_ss03 = any(item['rule_id'] == 'SS03' for item in result)
        
        if has_ss03 == test_case['should_trigger']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发SS03: {'是' if has_ss03 else '否'}")
        print(f"预期触发: {'是' if test_case['should_trigger'] else '否'}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"SS03 SET语句测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

def test_mixed_set_and_query():
    """测试混合SET语句和查询语句"""
    print("\n" + "=" * 60)
    print("混合SET语句和查询语句测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    test_cases = [
        {
            "sql": """set hive.exec.dynamic.partition=true;
set hivevar:prompt=1;
select * from users;""",
            "description": "多个SET语句后跟查询",
            "expected_ss02": True,   # 查询中的小写关键字应该触发SS02
            "expected_ss03": False   # SET语句不应该触发SS03
        },
        {
            "sql": """set hive.exec.dynamic.partition=true;
SELECT UserID FROM UserTable;""",
            "description": "SET语句后跟包含大写标识符的查询",
            "expected_ss02": False,  # SET语句不应该触发SS02
            "expected_ss03": True    # 查询应该触发SS03
        },
        {
            "sql": """set character.literal.as.string=true;
select userid from usertable;""",
            "description": "SET语句后跟小写查询",
            "expected_ss02": True,   # 查询中的select小写应该触发SS02
            "expected_ss03": False   # 查询标识符小写不应该触发SS03
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql'][:50]}..." if len(test_case['sql']) > 50 else f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了规则
        has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
        has_ss03 = any(item['rule_id'] == 'SS03' for item in result)
        
        ss02_correct = has_ss02 == test_case['expected_ss02']
        ss03_correct = has_ss03 == test_case['expected_ss03']
        
        if ss02_correct and ss03_correct:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发SS02: {'是' if has_ss02 else '否'} (预期: {'是' if test_case['expected_ss02'] else '否'})")
        print(f"触发SS03: {'是' if has_ss03 else '否'} (预期: {'是' if test_case['expected_ss03'] else '否'})")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"混合语句测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    return failed == 0

if __name__ == "__main__":
    # 运行所有SET语句测试
    ss02_success = test_set_statements_ss02()
    ss03_success = test_set_statements_ss03()
    mixed_success = test_mixed_set_and_query()
    
    print("\n" + "=" * 60)
    print("SET语句测试总结")
    print("=" * 60)
    print(f"SS02规则测试: {'通过' if ss02_success else '失败'}")
    print(f"SS03规则测试: {'通过' if ss03_success else '失败'}")
    print(f"混合语句测试: {'通过' if mixed_success else '失败'}")
    
    overall_success = ss02_success and ss03_success and mixed_success
    print(f"\n总体结果: {'所有测试通过' if overall_success else '有测试失败'}")
    
    # 返回退出码
    sys.exit(0 if overall_success else 1)