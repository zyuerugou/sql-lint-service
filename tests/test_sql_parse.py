sql = '''INSERT INTO a(id, name, bal, avg) 
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

import sqlfluff
from sqlfluff.core import FluffConfig

config = FluffConfig(overrides={'dialect': 'hive'})
result = sqlfluff.lint(sql, config=config)
print('SQL检查结果:')
print(f'返回结果类型: {type(result)}')
print(f'返回结果长度: {len(result)}')

# 检查是否有解析错误
has_unparsable = False
for i, violation in enumerate(result):
    desc = violation.get('description', '')
    if 'unparsable' in desc.lower():
        has_unparsable = True
        print(f'发现未解析错误: {desc}')
        print(f'  完整错误: {violation}')

if not has_unparsable:
    print('没有发现"Found unparsable section"错误')
    print('SQL可以正常解析，但有格式和风格问题')
    
# 尝试解析看看是否有异常
try:
    parsed = sqlfluff.parse(sql, config=config)
    print(f'\n解析成功: {parsed}')
except Exception as e:
    print(f'\n解析异常: {e}')