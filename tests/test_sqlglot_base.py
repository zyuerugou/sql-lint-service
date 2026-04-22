#!/usr/bin/env python3
# coding=utf-8
"""
测试sqlglot规则基类
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.rules.sqlglot_base import SQLGlotBaseRule, Violation


def test_base_rule():
    """测试基类功能"""
    print("=" * 60)
    print("测试sqlglot规则基类")
    print("=" * 60)
    
    class TestRule(SQLGlotBaseRule):
        code = "TEST01"
        description = "测试规则"
        
        def check(self, ast, sql=""):
            return []
    
    rule = TestRule()
    print(f"规则信息: {rule.get_info()}")
    print(f"规则字符串: {rule}")
    
    # 测试Violation类
    print(f"\n测试Violation类:")
    violation = Violation(
        rule_id="TEST01",
        message="测试违规",
        line=10,
        column=5,
        severity="warning"
    )
    
    violation_dict = violation.to_dict()
    print(f"违规字典: {violation_dict}")
    
    expected_dict = {
        "rule_id": "TEST01",
        "message": "测试违规",
        "severity": "warning",
        "line": 10,
        "column": 5
    }
    
    if violation_dict == expected_dict:
        print("  [OK] Violation类测试通过")
        return True
    else:
        print(f"  [ERROR] Violation类测试失败")
        print(f"  期望: {expected_dict}")
        print(f"  实际: {violation_dict}")
        return False


if __name__ == "__main__":
    success = test_base_rule()
    sys.exit(0 if success else 1)