#!/usr/bin/env python3
# coding=utf-8
"""
测试SS02规则：SQL关键字必须大写
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot


def test_rule_ss02():
    """测试SS02规则功能"""
    print("=" * 60)
    print("测试SS02规则：SQL关键字必须大写")
    print("=" * 60)
    
    rule = RuleSs02Sqlglot()
    print(f"规则信息: {rule.get_info()}")
    
    # 测试用例
    test_cases = [
        ("select id from users", True),  # 应该触发（select小写）
        ("SELECT id FROM users", False),  # 不应该触发
        ("Select id From users", False),  # 首字母大写，不触发
        ("select id, name from users where id = 1", True),  # 多个小写关键字
    ]
    
    all_pass = True
    
    for sql, should_trigger in test_cases:
        print(f"\n测试SQL: {sql}")
        
        try:
            ast = sqlglot.parse_one(sql, read="hive")
            violations = rule.check(ast, sql)
            
            if violations:
                print(f"  触发规则: 是, 违规数: {len(violations)}")
                for v in violations[:3]:  # 只显示前3个
                    print(f"    - 行{v.line}列{v.column}: {v.message}")
                if len(violations) > 3:
                    print(f"    ...还有{len(violations)-3}个违规")
                
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
        print("[PASS] SS02规则测试通过")
        return True
    else:
        print("[FAIL] SS02规则测试失败")
        return False


if __name__ == "__main__":
    success = test_rule_ss02()
    sys.exit(0 if success else 1)