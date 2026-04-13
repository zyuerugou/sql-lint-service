#!/usr/bin/env python3
# coding=utf-8
"""
简单测试热加载功能
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def test_simple():
    """简单测试，返回是否通过"""
    passed = True
    from app.services.lint_service import LintService
    
    print("创建LintService实例（启用热加载）...")
    service = LintService(enable_hot_reload=True)
    
    # 获取初始规则
    rules = service.get_loaded_rules()
    print(f"初始规则: {rules}")
    
    # 测试SQL
    sql = "SELECT * FROM users"
    print(f"\n测试SQL: {sql}")
    result = service.lint_sql(sql)
    
    # 只显示自定义规则
    custom_rules = [r for r in result if r['rule_id'] in ['SS01', 'SS02']]
    if custom_rules:
        print("触发自定义规则:")
        for r in custom_rules:
            print(f"  {r['rule_id']}: {r['message']}")
    else:
        print("未触发自定义规则")
    
    # 创建新规则
    print("\n创建新规则文件...")
    new_rule = '''# coding=utf-8
from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler

class Rule_TE02(BaseRule):
    """测试规则"""
    
    groups = ("all", "customer")
    code = "TE02"
    description = "测试规则"
    crawl_behaviour = SegmentSeekerCrawler({"select_statement"})
    
    def _eval(self, context: RuleContext):
        return LintResult(
            anchor=context.segment,
            description="这是一个测试规则"
        )
'''
    
    rule_path = os.path.join("..", "app", "rules", "rule_te02.py")
    with open(rule_path, 'w', encoding='utf-8') as f:
        f.write(new_rule)
    
    print(f"新规则文件已创建: {rule_path}")
    
    # 手动重新加载
    print("\n手动重新加载规则...")
    service.manual_reload()
    
    # 检查新规则
    new_rules = service.get_loaded_rules()
    print(f"重新加载后的规则: {new_rules}")
    
    if "TE02" in new_rules:
        print("[PASS] 新规则TE02已加载")
    else:
        print("[FAIL] 新规则TE02未加载")
        passed = False
    
    # 清理
    if os.path.exists(rule_path):
        os.remove(rule_path)
        print(f"\n已删除测试文件: {rule_path}")
    
    # 再次重新加载
    service.manual_reload()
    final_rules = service.get_loaded_rules()
    print(f"最终规则: {final_rules}")
    
    if "TE02" not in final_rules:
        print("[PASS] 规则TE02已成功移除")
    else:
        print("[FAIL] 规则TE02仍然存在")
        passed = False
    
    return passed

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)