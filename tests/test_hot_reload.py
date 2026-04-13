#!/usr/bin/env python3
"""
测试规则热加载功能
"""

import sys
import os
import time
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

def test_hot_reload():
    """测试热加载功能"""
    
    # 导入LintService
    from app.services.lint_service import LintService
    
    print("=" * 60)
    print("测试规则热加载功能")
    print("=" * 60)
    
    # 创建LintService实例，启用热加载
    print("\n1. 创建LintService实例（启用热加载）...")
    service = LintService(enable_hot_reload=True)
    
    # 获取初始加载的规则
    initial_rules = service.get_loaded_rules()
    print(f"初始加载的规则: {initial_rules}")
    
    # 测试初始规则
    print("\n2. 测试初始规则...")
    test_sql = "SELECT * FROM users"
    result = service.lint_sql(test_sql)
    print(f"SQL: {test_sql}")
    print("Lint结果:")
    for item in result:
        print(f"  - {item['rule_id']}: {item['message']}")
    
    # 创建新规则文件
    print("\n3. 创建新规则文件 rule_ss03.py...")
    new_rule_content = '''from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler


class Rule_SS03(BaseRule):
    """检查表名是否使用下划线命名法。"""

    groups = ("all",)
    code = "SS03"
    description = "表名应使用下划线命名法（snake_case）。"
    crawl_behaviour = SegmentSeekerCrawler({"from_expression"})
    config_keywords = []

    def _eval(self, context: RuleContext):
        """检查表名是否使用下划线命名法"""
        segment = context.segment
        
        if segment.is_type("from_expression"):
            # 这里简化处理，实际应该解析表名
            # 对于演示目的，我们只是添加一个规则
            pass
        return None
'''
    
    new_rule_path = os.path.join("..", "app", "rules", "rule_ss03.py")
    with open(new_rule_path, 'w', encoding='utf-8') as f:
        f.write(new_rule_content)
    
    print(f"新规则文件已创建: {new_rule_path}")
    
    # 等待文件监控检测到变化
    print("\n4. 等待文件监控检测变化（3秒）...")
    time.sleep(3)
    
    # 手动触发重新加载
    print("\n5. 手动触发规则重新加载...")
    success = service.manual_reload()
    print(f"重新加载结果: {'成功' if success else '失败'}")
    
    # 获取重新加载后的规则
    reloaded_rules = service.get_loaded_rules()
    print(f"重新加载后的规则: {reloaded_rules}")
    
    # 验证新规则是否加载
    if "SS03" in reloaded_rules:
        print("[PASS] 新规则 SS03 已成功加载")
    else:
        print("[FAIL] 新规则 SS03 未加载")
    
    # 测试API端点（如果服务正在运行）
    print("\n6. 测试API端点...")
    try:
        # 尝试连接本地API
        response = requests.get("http://localhost:5000/rules", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"API响应: {data}")
        else:
            print(f"API不可用 (状态码: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("API服务未运行，跳过API测试")
    
    # 清理：删除测试规则文件
    print("\n7. 清理测试文件...")
    if os.path.exists(new_rule_path):
        os.remove(new_rule_path)
        print(f"已删除测试文件: {new_rule_path}")
    
    # 再次重新加载以验证删除
    print("\n8. 重新加载以验证规则删除...")
    service.manual_reload()
    final_rules = service.get_loaded_rules()
    print(f"最终规则列表: {final_rules}")
    
    if "SS03" not in final_rules:
        print("[PASS] 规则 SS03 已成功移除")
    else:
        print("[FAIL] 规则 SS03 仍然存在")
    
    print("\n" + "=" * 60)
    print("热加载测试完成")
    print("=" * 60)

def test_without_hot_reload():
    """测试不启用热加载的情况"""
    
    print("\n" + "=" * 60)
    print("测试不启用热加载的情况")
    print("=" * 60)
    
    from app.services.lint_service import LintService
    
    # 创建不启用热加载的实例
    service = LintService(enable_hot_reload=False)
    
    rules = service.get_loaded_rules()
    print(f"加载的规则: {rules}")
    
    # 创建新规则文件
    new_rule_path = os.path.join("..", "app", "rules", "rule_test_temp.py")
    with open(new_rule_path, 'w', encoding='utf-8') as f:
        f.write('''from sqlfluff.core.rules import BaseRule

class Rule_TEMP(BaseRule):
    """临时测试规则"""
    groups = ("all",)
    code = "TEMP"
    description = "临时测试规则"
''')
    
    print(f"\n创建临时规则文件: {new_rule_path}")
    print("注意：由于热加载未启用，文件变化不会被自动检测")
    
    # 清理
    if os.path.exists(new_rule_path):
        os.remove(new_rule_path)
        print(f"已删除临时文件: {new_rule_path}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # 测试启用热加载
    test_hot_reload()
    
    # 测试不启用热加载
    test_without_hot_reload()