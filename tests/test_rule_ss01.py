#!/usr/bin/env python3
# coding=utf-8
"""
测试SS01规则：禁止使用SELECT *
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import sqlglot
from app.rules.rule_ss01_sqlglot import RuleSs01Sqlglot


def test_rule_ss01():
    """测试SS01规则功能"""
    print("=" * 60)
    print("测试SS01规则：禁止使用SELECT *")
    print("=" * 60)
    
    rule = RuleSs01Sqlglot()
    print(f"规则信息: {rule.get_info()}")
    
    # 测试用例
    test_cases = [
        ("SELECT * FROM users", True),  # 应该触发
        ("SELECT id, name FROM users", False),  # 不应该触发
        ("SELECT id FROM (SELECT * FROM users) t", True),  # 子查询应该触发
        ("SELECT COUNT(*) FROM users", True),  # COUNT(*)也应该触发
    ]
    
    all_pass = True
    
    for sql, should_trigger in test_cases:
        print(f"\n测试SQL: {sql}")
        
        try:
            ast = sqlglot.parse_one(sql, read="hive")
            violations = rule.check(ast, sql)
            
            if violations:
                print(f"  触发规则: 是, 违规数: {len(violations)}")
                for v in violations:
                    print(f"    - 行{v.line}: {v.message}")
                
                if should_trigger:
                    print("  结果: [OK] 符合预期")
                else:
                    print("  结果: [ERROR] 不符合预期")
                    all_pass = False
            else:
                print(f"  触发规则: 否")
                
                if not should_trigger:
                    print("  结果: [OK] 符合预期")
                else:
                    print("  结果: [ERROR] 不符合预期")
                    all_pass = False
                    
        except Exception as e:
            print(f"  解析失败: {type(e).__name__}: {e}")
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("[PASS] SS01规则测试通过")
        return True
    else:
        print("[FAIL] SS01规则测试失败")
        return False


if __name__ == "__main__":
    success = test_rule_ss01()
    sys.exit(0 if success else 1)