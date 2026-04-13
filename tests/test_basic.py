#!/usr/bin/env python3
# coding=utf-8
"""
基础功能测试 - 快速验证服务基本功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("基础功能测试 - 快速验证服务基本功能")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    print("1. 测试服务初始化...")
    rules = service.get_loaded_rules()
    print(f"   加载的规则: {rules}")
    
    if len(rules) >= 2:
        print("   [PASS] 服务初始化成功，规则已加载")
    else:
        print("   [FAIL] 服务初始化失败，规则未正确加载")
        return False
    
    print("\n2. 测试基本lint功能...")
    
    # 简单测试用例
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
        }
    ]
    
    all_pass = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   测试 {i}: {test_case['expected']}")
        print(f"   SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 显示结果
        if result:
            print("   结果:")
            for item in result:
                print(f"     - {item['rule_id']}: {item['message']}")
        else:
            print("   结果: 无")
        
        # 简单验证
        if test_case['sql'] == "SELECT * FROM users":
            has_ss01 = any(item['rule_id'] == 'SS01' for item in result)
            if has_ss01:
                print("   [PASS] 正确触发了SS01规则")
            else:
                print("   [FAIL] 未触发SS01规则")
                all_pass = False
        elif test_case['sql'] == "select id, name from users":
            has_ss02 = any(item['rule_id'] == 'SS02' for item in result)
            if has_ss02:
                print("   [PASS] 正确触发了SS02规则")
            else:
                print("   [FAIL] 未触发SS02规则")
                all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("[PASS] 基础功能测试通过")
        return True
    else:
        print("[FAIL] 基础功能测试失败")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
