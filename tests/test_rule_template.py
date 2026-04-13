#!/usr/bin/env python3
"""
规则测试模板 - 用于创建新的规则测试文件

使用方法：
1. 复制此文件为 test_rule_<rule_code>.py（如 test_rule_ss03.py）
2. 修改规则代码、描述和测试用例
3. 运行测试：python test_rule_<rule_code>.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_rule_<RULE_CODE>():
    """测试<RULE_CODE>规则：<规则描述>"""
    print("=" * 60)
    print("<RULE_CODE>规则测试 - <规则描述>")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 测试用例
    test_cases = [
        {
            "sql": "<应该触发规则的SQL示例>",
            "description": "应该触发<RULE_CODE>规则（<原因>）",
            "expected_rule": "<RULE_CODE>",
            "should_trigger": True
        },
        {
            "sql": "<不应该触发规则的SQL示例>",
            "description": "不应该触发<RULE_CODE>规则（<原因>）",
            "expected_rule": "<RULE_CODE>",
            "should_trigger": False
        },
        # 添加更多测试用例...
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了<RULE_CODE>规则
        has_rule = any(item['rule_id'] == '<RULE_CODE>' for item in result)
        
        if has_rule == test_case['should_trigger']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发<RULE_CODE>: {'是' if has_rule else '否'}")
        print(f"预期触发: {'是' if test_case['should_trigger'] else '否'}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == '<RULE_CODE>':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("[PASS] 所有<RULE_CODE>规则测试通过")
        return True
    else:
        print("[FAIL] 部分<RULE_CODE>规则测试失败")
        return False

def test_rule_<RULE_CODE>_edge_cases():
    """测试<RULE_CODE>规则边界情况"""
    print("\n" + "=" * 60)
    print("<RULE_CODE>规则边界情况测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    edge_cases = [
        {
            "sql": "<边界情况SQL 1>",
            "description": "<边界情况描述 1>"
        },
        {
            "sql": "<边界情况SQL 2>",
            "description": "<边界情况描述 2>"
        },
        # 添加更多边界情况...
    ]
    
    for case in edge_cases:
        print(f"\n边界测试: {case['description']}")
        print(f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        has_rule = any(item['rule_id'] == '<RULE_CODE>' for item in result)
        
        print(f"触发<RULE_CODE>: {'是' if has_rule else '否'}")
        
        if has_rule:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == '<RULE_CODE>':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print("<RULE_CODE>规则边界情况测试完成")

if __name__ == "__main__":
    # 运行<RULE_CODE>规则测试
    success = test_rule_<RULE_CODE>()
    
    # 运行边界情况测试
    test_rule_<RULE_CODE>_edge_cases()
    
    # 返回退出码
    sys.exit(0 if success else 1)