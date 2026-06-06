"""
集成测试：通过 HTTP 请求验证 /fix 和 /lint 端点
服务需已启动在 http://localhost:5000
"""
import requests

BASE = "http://localhost:5000"

def test(msg, ok):
    tag = "✅" if ok else "❌"
    print(f"  {tag} {msg}")
    return ok

def run_all():
    passed = 0
    total = 0

    print("=" * 60)
    print("1. /fix — 变量回写")
    print("=" * 60)

    # 1.1 单语句 + 单变量
    total += 1
    r = requests.post(f"{BASE}/fix", json={"sql": "select id from t where dt = '${batch_date}'"})
    data = r.json()
    ok = test("单语句+变量 /fix 返回200", r.status_code == 200)
    ok &= test("返回 statements 数组", isinstance(data.get("statements"), list))
    ok &= test("数组长度 1", len(data["statements"]) == 1)
    ok &= test("${batch_date} 保留", "${batch_date}" in data["statements"][0]["fixed"])
    ok &= test("关键字大写", "SELECT" in data["statements"][0]["fixed"])
    if ok: passed += 1

    # 1.2 多语句 + 多变量
    total += 1
    sql = "select id from t1 where dt = '${batch_date}';select name from t2 where ym = '${batch_yyyymm}'"
    r = requests.post(f"{BASE}/fix", json={"sql": sql})
    data = r.json()
    ok = test("多语句+变量 /fix 返回200", r.status_code == 200)
    ok &= test("数组长度 2", len(data["statements"]) == 2)
    ok &= test("第一句 ${batch_date} 保留", "${batch_date}" in data["statements"][0]["fixed"])
    ok &= test("第二句 ${batch_yyyymm} 保留", "${batch_yyyymm}" in data["statements"][1]["fixed"])
    if ok: passed += 1

    # 1.3 含 SET 语句
    total += 1
    sql = "set hive.exec.dynamic.partition=true;\nselect * from t where dt = '${batch_date}'"
    r = requests.post(f"{BASE}/fix", json={"sql": sql})
    data = r.json()
    ok = test("含SET /fix 返回200", r.status_code == 200)
    ok &= test("SET被过滤，只有1条结果", len(data["statements"]) == 1)
    ok &= test("${batch_date} 保留", "${batch_date}" in data["statements"][0]["fixed"])
    if ok: passed += 1

    # 1.4 同一变量多次出现
    total += 1
    sql = "select id from t where start_dt = '${batch_date}' and end_dt = '${batch_date}'"
    r = requests.post(f"{BASE}/fix", json={"sql": sql})
    data = r.json()
    ok = test("同一变量多次出现 /fix 返回200", r.status_code == 200)
    ok &= test("两个 ${batch_date} 都保留", data["statements"][0]["fixed"].count("${batch_date}") == 2)
    if ok: passed += 1

    # 1.5 空SQL
    total += 1
    r = requests.post(f"{BASE}/fix", json={"sql": ""})
    data = r.json()
    ok = test("空SQL /fix 返回200", r.status_code == 200)
    ok &= test("返回空数组", data.get("statements") == [])
    if ok: passed += 1

    print()
    print("=" * 60)
    print("2. /lint — lint 检查")
    print("=" * 60)

    # 2.1 SELECT * 触发 SS01
    total += 1
    r = requests.post(f"{BASE}/lint", json={"sql": "select * from t where dt = '${batch_date}'"})
    data = r.json()
    ok = test("SELECT * /lint 返回200", r.status_code == 200)
    codes = [v["rule_id"] for v in data.get("result", [])]
    ok &= test("命中 SS01", "SS01" in codes)
    ok &= test("命中 SS02", "SS02" in codes)
    if ok: passed += 1

    # 2.2 合规SQL（无违规）
    total += 1
    r = requests.post(f"{BASE}/lint", json={"sql": "SELECT id FROM t WHERE dt = '20251231'"})
    data = r.json()
    ok = test("合规SQL /lint 返回200", r.status_code == 200)
    ok &= test("无违规结果", len(data.get("result", [])) == 0)
    if ok: passed += 1

    # 2.3 大小写混合触发 SS02 + SS03
    total += 1
    r = requests.post(f"{BASE}/lint", json={"sql": "SELECT * FROM USERS"})
    data = r.json()
    ok = test("大小写混合 /lint 返回200", r.status_code == 200)
    codes = [v["rule_id"] for v in data.get("result", [])]
    ok &= test("命中 SS01", "SS01" in codes)
    ok &= test("命中 SS03", "SS03" in codes)
    if ok: passed += 1

    print()
    print("=" * 60)
    print("3. /health — 健康检查")
    print("=" * 60)

    total += 1
    r = requests.get(f"{BASE}/health")
    data = r.json()
    ok = test("/health 返回200", r.status_code == 200)
    ok &= test("状态 healthy", data.get("status") == "healthy")
    ok &= test("规则数量 3", data.get("rules_loaded") == 3)
    if ok: passed += 1

    print()
    print("=" * 60)
    print(f"结果: {passed}/{total} 通过")
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = run_all()
    exit(0 if success else 1)
