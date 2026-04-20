import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.lint_service import LintService

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

# 创建LintService实例
service = LintService(enable_hot_reload=False, timeout_seconds=10)

print("开始检查SQL...")
result = service.lint_sql(sql)

print(f"\n检查结果: {len(result)} 个问题")
for i, violation in enumerate(result, 1):
    print(f"{i}. [{violation.get('severity')}] {violation.get('rule_id')}: {violation.get('message')} (行{violation.get('line')})")
    
# 检查是否有解析错误
has_unparsable = False
for violation in result:
    message = violation.get('message', '')
    if 'unparsable' in message.lower():
        has_unparsable = True
        print(f"\n发现未解析错误: {message}")
        
if not has_unparsable:
    print("\n没有发现'Found unparsable section'错误")