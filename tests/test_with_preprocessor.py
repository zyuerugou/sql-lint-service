import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.preprocessor_manager import PreprocessorManager

# 带变量的原始SQL
sql_with_vars = '''INSERT INTO a(id, name, bal, avg) 
SELECT 
  CAST(a.id AS VARCHAR(50)),
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200)), 
  CAST(NVL(a.bal, 0) AS DECIMAL(30,6)), 
  CAST(a.accum_bal /  x.days AS DECIMAL(30,6)) 
FROM 
  (SELECT * FROM a WHERE 1=1 AND a.part_ymd='${batch_date}' AND a.cust_typ=1) a 
  INNER JOIN (  
    SELECT id, min(name) FROM b WHERE start_dt <= '${batch_date}' AND end_dt > '${batch_date}' AND part_ym >= '${batch_yyyymm}'     
    and trim(id) <> '' GROUP BY id) b 
    ON 1=1 AND a.id = b.id AND b.id LIKE 'p%' 
  LEFT JOIN e ON a.id = e.id 
  LEFT JOIN x ON 1=1   AND x.curr_dt = '${batch_date}';'''

print("原始SQL（带变量）:")
print(f"长度: {len(sql_with_vars)} 字符")
print(f"包含变量: ${'{batch_date}'} 和 ${'{batch_yyyymm}'}")

# 使用预处理器
preprocessor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../app", "rules", "preprocessors")
manager = PreprocessorManager(preprocessor_dir)

processed_sql = manager.process(sql_with_vars)

print(f"\n处理后SQL:")
print(f"长度: {len(processed_sql)} 字符")
print(f"是否变化: {'是' if processed_sql != sql_with_vars else '否'}")

# 检查变化
if processed_sql != sql_with_vars:
    # 找到第一个不同点
    for i, (orig, proc) in enumerate(zip(sql_with_vars, processed_sql)):
        if orig != proc:
            print(f"第一个不同点在位置 {i}:")
            print(f"  原始: ...{sql_with_vars[max(0,i-20):i+20]}...")
            print(f"  处理: ...{processed_sql[max(0,i-20):i+20]}...")
            break

# 测试解析
import sqlfluff
from sqlfluff.core import FluffConfig

print(f"\n{'='*60}")
print("测试解析:")

for dialect in ['hive', 'ansi']:
    print(f"\n方言: {dialect}")
    
    # 测试原始SQL（带变量）
    print(f"  原始SQL（带变量）:")
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(sql_with_vars, config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                print(f"    解析错误: {violation.get('description')[:80]}...")
                break
        
        if not has_unparsable:
            print(f"    可以解析")
            
    except Exception as e:
        print(f"    异常: {type(e).__name__}: {e}")
    
    # 测试处理后SQL
    print(f"  处理后SQL:")
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(processed_sql, config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                print(f"    解析错误: {violation.get('description')[:80]}...")
                break
        
        if not has_unparsable:
            print(f"    可以解析，有{len(result)}个问题")
            
    except Exception as e:
        print(f"    异常: {type(e).__name__}: {e}")