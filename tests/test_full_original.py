import sqlfluff
from sqlfluff.core import FluffConfig

# 完整的原始SQL
original_sql = '''INSERT INTO a(id, name, bal, avg) 
SELECT 
  CAST(a.id AS VARCHAR(50)),
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200)), 
  CAST(NVL(a.bal, 0) AS DECIMAL(30,6)), 
  CAST(a.accum_bal /  x.days AS DECIMAL(30,6)) 
FROM 
  (SELECT * FROM a WHERE 1=1 AND a.part_ymd='20251231' AND a.cust_typ=1) a 
  INNER JOIN (  
    SELECT id, min(name) FROM b WHERE start_dt <= '20251231' AND end_dt > '20251231' AND part_ym >= '202512'     
    and trim(id) <> '' GROUP BY id) b 
    ON 1=1 AND a.id = b.id AND b.id LIKE 'p%' 
  LEFT JOIN e ON a.id = e.id 
  LEFT JOIN x ON 1=1   AND x.curr_dt = '20251231';'''

print("测试完整的原始SQL:")
print(f"SQL长度: {len(original_sql)} 字符")
print(f"SQL前200字符: {original_sql[:200]}...")

# 测试不同方言
dialects = ['hive', 'ansi']

for dialect in dialects:
    print(f"\n{'='*60}")
    print(f"方言: {dialect}")
    
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(original_sql, config=config)
        
        # 检查解析错误
        unparsable_errors = []
        other_errors = []
        
        for violation in result:
            desc = violation.get('description', '')
            if 'unparsable' in desc.lower():
                unparsable_errors.append(violation)
            else:
                other_errors.append(violation)
        
        if unparsable_errors:
            print(f"  发现 {len(unparsable_errors)} 个解析错误:")
            for i, err in enumerate(unparsable_errors[:3], 1):
                print(f"    {i}. {err.get('description')}")
            if len(unparsable_errors) > 3:
                print(f"    ...还有{len(unparsable_errors)-3}个解析错误")
        else:
            print(f"  无解析错误")
            
        if other_errors:
            print(f"  有 {len(other_errors)} 个格式/风格问题")
            
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")

# 测试修改后的SQL（修复可能的问题）
print(f"\n{'='*60}")
print("测试修改后的SQL（使用COALESCE代替NVL）:")

modified_sql = original_sql.replace('NVL(', 'COALESCE(')
print(f"修改: NVL -> COALESCE")

for dialect in dialects:
    print(f"\n方言: {dialect}")
    
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(modified_sql, config=config)
        
        unparsable_errors = []
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                unparsable_errors.append(violation)
        
        if unparsable_errors:
            print(f"  仍有解析错误: {unparsable_errors[0].get('description')[:100]}...")
        else:
            print(f"  无解析错误，有{len(result)}个其他问题")
            
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")