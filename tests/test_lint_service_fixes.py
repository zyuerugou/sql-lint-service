"""
lint_service.py 修复项 + 变量回写 + 拆句 专项测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.lint_service import LintService


def test_fix_sql_safety():
    """fix_sql: 异常/边缘场景返回空列表"""
    service = LintService(enable_hot_reload=False)

    # 空SQL → []
    results = service.fix_sql("")
    assert isinstance(results, list), "空SQL应返回列表"
    assert len(results) == 0, "空SQL应返回空列表"
    print("✓ 空SQL → []")

    # 空白SQL → []
    results = service.fix_sql("   ")
    assert isinstance(results, list), "空白SQL应返回列表"
    assert len(results) == 0, "空白SQL应返回空列表"
    print("✓ 空白SQL → []")

    # 正常SQL（回归验证）
    results = service.fix_sql("select id from users")
    assert len(results) == 1, "正常SQL应返回一条结果"
    fixed = results[0]["fixed"]
    assert "SELECT" in fixed, "关键字应大写"
    print(f"✓ 正常SQL → {len(results)} 条")

    print("fix_sql 安全性测试通过")


def test_variable_restoration():
    """fix_sql: ${...} 变量在修复后保留"""
    service = LintService(enable_hot_reload=False)

    # 单变量
    sql = "select id from t where dt = '${batch_date}'"
    results = service.fix_sql(sql)
    assert len(results) == 1
    fixed = results[0]["fixed"]
    assert "${batch_date}" in fixed, \
        f"变量 ${batch_date} 应保留在输出中，实际: {repr(fixed)}"
    print(f"✓ 单变量保留 → {repr(fixed)}")

    # 多变量
    sql = "SELECT * FROM t WHERE dt = '${batch_date}' AND ym = '${batch_yyyymm}'"
    results = service.fix_sql(sql)
    fixed = results[0]["fixed"]
    assert "${batch_date}" in fixed, "batch_date 应保留"
    assert "${batch_yyyymm}" in fixed, "batch_yyyymm 应保留"
    print(f"✓ 多变量保留 → {repr(fixed)}")

    # 同一变量多次出现
    sql = "select id from t where dt = '${batch_date}' and end_dt = '${batch_date}'"
    results = service.fix_sql(sql)
    fixed = results[0]["fixed"]
    assert fixed.count("${batch_date}") == 2, "同一变量多次出现应全部还原"
    print(f"✓ 同一变量多次出现 → {repr(fixed)}")

    print("变量回写测试通过")


def test_multi_statement():
    """fix_sql: 多语句拆句返回数组"""
    service = LintService(enable_hot_reload=False)

    # 两条简单语句
    sql = "select id from t1;select name from t2"
    results = service.fix_sql(sql)
    assert len(results) == 2, f"应返回2条结果，实际: {len(results)}"
    assert "SELECT" in results[0]["fixed"]
    assert "SELECT" in results[1]["fixed"]
    print(f"✓ 多语句 → {len(results)} 条: {[r['fixed'] for r in results]}")

    # 含变量的多语句
    sql = "select dt from t where day = '${batch_date}';select id from t2"
    results = service.fix_sql(sql)
    assert len(results) == 2, f"应返回2条结果"
    assert "${batch_date}" in results[0]["fixed"], "变量应保留"
    print(f"✓ 多语句+变量 → {[r['fixed'][:40] + '...' for r in results]}")

    print("多语句拆句测试通过")


def test_format_result_dynamic_whitelist():
    """_format_result 动态白名单"""
    service = LintService(enable_hot_reload=False)
    loaded_codes = {r.code for r in service.custom_rules}

    sql = "SELECT * FROM Users"
    results = service.lint_sql(sql)
    for r in results:
        assert r["rule_id"] in loaded_codes

    for code in ("SS01", "SS02", "SS03"):
        assert code in loaded_codes

    print(f"✓ 规则白名单: {sorted(loaded_codes)}")
    print("_format_result 测试通过")


def test_load_rules_all_three():
    """load_rules_from_files 加载全部3个规则"""
    service = LintService(enable_hot_reload=False)
    codes = sorted([r.code for r in service.custom_rules])
    assert codes == ["SS01", "SS02", "SS03"]
    print(f"✓ 已加载规则: {codes}")


if __name__ == "__main__":
    print("=" * 60)
    print("lint_service.py 专项测试")
    print("=" * 60)

    test_fix_sql_safety()
    print()
    test_variable_restoration()
    print()
    test_multi_statement()
    print()
    test_format_result_dynamic_whitelist()
    print()
    test_load_rules_all_three()

    print()
    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)
