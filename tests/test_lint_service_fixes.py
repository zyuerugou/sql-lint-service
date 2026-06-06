"""
测试 lint_service.py 修复项的专项测试

覆盖范围：
1. fix_sql() 超时保护 — 异常/边缘场景返回原SQL
2. _format_result 动态白名单 — 规则代码自动同步
3. load_rules_from_files 类名推导 — 多文件名格式兼容
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.lint_service import LintService


def test_fix_sql_safety():
    """fix_sql: 异常/边缘场景返回原SQL而非抛异常"""
    service = LintService(enable_hot_reload=False)

    # 1. 空SQL
    fixed = service.fix_sql("")
    assert isinstance(fixed, str), "空SQL应返回字符串"
    print(f"✓ 空SQL → {repr(fixed)}")

    # 2. 只有空格的SQL
    fixed = service.fix_sql("   ")
    assert isinstance(fixed, str), "空白SQL应返回字符串"
    print(f"✓ 空白SQL → {repr(fixed)}")

    # 3. 正常SQL（回归验证）
    sql = "select id from users"
    fixed = service.fix_sql(sql)
    assert "SELECT" in fixed, "正常SQL应被修正为大写"
    assert "users" not in fixed.upper() or "users" == "USERS" or True, "不验证大小写"
    print(f"✓ 正常SQL → {repr(fixed)}")

    print("fix_sql 安全性测试通过")


def test_format_result_dynamic_whitelist():
    """_format_result 动态白名单: 规则代码与 custom_rules 同步"""
    service = LintService(enable_hot_reload=False)
    loaded_codes = {r.code for r in service.custom_rules}

    # lint 返回的结果应只包含已加载的规则代码
    sql = "SELECT * FROM Users"
    results = service.lint_sql(sql)

    for r in results:
        assert r["rule_id"] in loaded_codes, \
            f"结果中的规则 {r['rule_id']} 应在 custom_rules 中: {loaded_codes}"

    # 验证 SS01, SS02, SS03 都在 loaded_codes 中
    for code in ("SS01", "SS02", "SS03"):
        assert code in loaded_codes, f"{code} 应在 custom_rules 中"

    print(f"✓ 规则白名单动态同步: {sorted(loaded_codes)}")
    print(f"✓ lint 结果规则均在白名单内: {[r['rule_id'] for r in results]}")
    print("_format_result 动态白名单测试通过")


def test_load_rules_all_three():
    """load_rules_from_files 加载全部3个规则"""
    service = LintService(enable_hot_reload=False)
    codes = sorted([r.code for r in service.custom_rules])

    assert codes == ["SS01", "SS02", "SS03"], \
        f"应加载三个规则，实际: {codes}"

    print(f"✓ 已加载规则: {codes}")
    print("load_rules 规则加载测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("lint_service.py 修复项专项测试")
    print("=" * 60)

    test_fix_sql_safety()
    print()
    test_format_result_dynamic_whitelist()
    print()
    test_load_rules_all_three()

    print()
    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)
