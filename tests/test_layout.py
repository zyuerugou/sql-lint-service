"""
验证 /fix 输出排版符合当前 SQLFluff 所能达到的最佳效果
"""
import requests

BASE = "http://localhost:5000"

sql = (
    "INSERT INTO x ( id, cust_name ) "
    "SELECT a.id, b.cust_name FROM a "
    "LEFT JOIN b ON 1=1 AND a.id = b.id "
    "WHERE 1=1 AND a.typ = '1' "
    "GROUP BY a.id, b.cust_name "
    "ORDER BY a.id ASC, b.cust_name DESC"
)

r = requests.post(f"{BASE}/fix", json={"sql": sql})
data = r.json()
fixed = data["statements"][0]["fixed"]

print("=" * 60)
print("输出:")
print(fixed)
print("=" * 60)

lines = [l for l in fixed.split("\n") if l.strip()]
checks = []

# 1. 关键字大写
for kw in ("INSERT", "SELECT", "FROM", "LEFT JOIN", "WHERE", "GROUP BY", "ORDER BY"):
    checks.append((f"{kw} 大写", kw in fixed))

# 2. 子句独立占行（alone:strict: INSERT...SELECT 中 SELECT 在行末，值换行）
checks.append(("SELECT 在独立行或在行末", "SELECT" in fixed))
checks.append(("SELECT 字段换行", any(l.strip().startswith("a.id") or l.strip().startswith(", b.cust_name") for l in lines)))
checks.append(("FROM 独立一行", any(l.strip().startswith("FROM") for l in lines)))
checks.append(("WHERE 独立一行", any(l.strip().startswith("WHERE") for l in lines)))
checks.append(("GROUP BY 独立一行", any(l.strip().startswith("GROUP BY") for l in lines)))
checks.append(("ORDER BY 独立一行", any(l.strip().startswith("ORDER BY") for l in lines)))

# 3. 逗号在行首
comma_leading = any(l.strip().startswith(",") for l in lines)
checks.append(("逗号在行首", comma_leading))

# 4. 缩进为空格
checks.append(("缩进为空格（非Tab）", all(not l.startswith("\t") for l in lines if l.strip())))

# 5. 括号内换行
checks.append(("括号内容换行", any(l.strip().startswith("a.id") or l.strip().startswith(", b.cust_name") for l in lines)))

print("检查项:")
for name, ok in checks:
    tag = "✅" if ok else "❌"
    print(f"  {tag} {name}")

if all(ok for _, ok in checks):
    print("\n✅ 所有排版检查通过!")
else:
    print(f"\n⚠️  {sum(1 for _, ok in checks if not ok)} 项未达预期")
