import sqlfluff
from sqlfluff.core import FluffConfig

# 测试没有分号分隔的多语句SQL
sql = """SELECT * FROM users
SELECT id, name FROM users"""

print("测试SQL:")
print(sql)
print(f"\nSQL长度: {len(sql)} 字符")

# 测试不同配置
configs = [
    {"name": "默认配置（all规则）", "overrides": {"dialect": "ansi", "rules": "all"}},
    {"name": "只使用customer规则", "overrides": {"dialect": "ansi", "rules": "customer"}},
    {"name": "空规则", "overrides": {"dialect": "ansi", "rules": ""}},
]

for cfg in configs:
    print(f"\n{'='*60}")
    print(f"配置: {cfg['name']}")
    
    try:
        config = FluffConfig(overrides=cfg['overrides'])
        result = sqlfluff.lint(sql, config=config)
        
        print(f"发现 {len(result)} 个问题:")
        for i, violation in enumerate(result, 1):
            print(f"  {i}. [{violation.get('code')}] 行{violation.get('start_line_no')}: {violation.get('description')}")
            
    except Exception as e:
        print(f"异常: {type(e).__name__}: {e}")

# 测试单个语句
print(f"\n{'='*60}")
print("测试单个语句（没有分号）:")
single_sql = "SELECT * FROM users"
print(f"SQL: {single_sql}")

config = FluffConfig(overrides={"dialect": "ansi", "rules": "customer"})
result = sqlfluff.lint(single_sql, config=config)
print(f"结果: {len(result)} 个问题")
for v in result:
    print(f"  [{v.get('code')}]: {v.get('description')}")