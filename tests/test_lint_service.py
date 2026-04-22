#!/usr/bin/env python3
# coding=utf-8
"""
测试LintService功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService


def test_lint_service():
    """测试LintService功能"""
    print("=" * 60)
    print("测试LintService功能")
    print("=" * 60)
    
    # 创建服务
    service = LintService(enable_hot_reload=False)
    
    print(f"服务初始化完成")
    print(f"加载规则: {service.get_loaded_rules()}")
    print(f"加载预处理器: {service.get_loaded_preprocessors()}")
    
    # 测试用例
    test_cases = [
        {
            "sql": "SELECT * FROM users",
            "expected": "应该触发SS01规则"
        },
        {
            "sql": "SELECT id, name FROM users",
            "expected": "不应该触发任何规则"
        },
        {
            "sql": "select id, name from users",
            "expected": "应该触发SS02规则"
        },
        {
            "sql": "SELECT UserID FROM UserTable",
            "expected": "应该触发SS03规则"
        },
        {
            "sql": "SELECT * FROM users u",
            "expected": "应该触发SS04规则"
        }
    ]
    
    all_pass = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['expected']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 显示结果
        if result:
            print("结果:")
            for item in result:
                print(f"  - {item['rule_id']}: {item['message']}")
        else:
            print("结果: 无")
        
        # 简单验证
        if test_case['sql'] == "SELECT * FROM users":
            has_ss01 = any(item['rule_id'] == 'SS01' for item in result)
            if has_ss01:
                print("  [OK] 正确触发了SS01规则")
            else:
                print("  [ERROR] 未触发SS01规则")
                all_pass = False
        elif test_case['sql'] == "select id, name from users":
            has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
            if has_ss02:
                print("  [OK] 正确触发了SS02规则")
            else:
                print("  [ERROR] 未触发SS02规则")
                all_pass = False
        elif test_case['sql'] == "SELECT UserID FROM UserTable":
            has_ss03 = any(item['rule_id'] == 'SS03' for item in result)
            if has_ss03:
                print("  [OK] 正确触发了SS03规则")
            else:
                print("  [ERROR] 未触发SS03规则")
                all_pass = False
        elif test_case['sql'] == "SELECT * FROM users u":
            has_ss04 = any(item['rule_id'] == 'SS04' for item in result)
            if has_ss04:
                print("  [OK] 正确触发了SS04规则")
            else:
                print("  [ERROR] 未触发SS04规则")
                all_pass = False
    
    # 测试服务信息
    print(f"\n测试服务信息:")
    info = service.get_service_info()
    print(f"  服务类型: {info.get('service_type')}")
    print(f"  SQL方言: {info.get('dialect')}")
    print(f"  缓存大小: {info.get('cache_size')}")
    
    # 测试规则重新加载
    print(f"\n测试规则重新加载:")
    success = service.reload_rules()
    print(f"  重新加载结果: {'成功' if success else '失败'}")
    print(f"  当前加载规则: {service.get_loaded_rules()}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("[PASS] LintService测试通过")
        return True
    else:
        print("[FAIL] LintService测试失败")
        return False


if __name__ == "__main__":
    success = test_lint_service()
    sys.exit(0 if success else 1)