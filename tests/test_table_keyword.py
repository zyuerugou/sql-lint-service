import sqlfluff
from sqlfluff.core import FluffConfig

# 测试不同的表名
test_cases = [
    {
        "name": "使用'table'作为表名",
        "sql": "SELECT id FROM table",
    },
    {
        "name": "使用'mytable'作为表名",
        "sql": "SELECT id FROM mytable",
    },
    {
        "name": "使用带引号的'table'",
        "sql": "SELECT id FROM `table`",
    },
    {
        "name": "使用'tbl'作为表名",
        "sql": "SELECT id FROM tbl",
    },
    {
        "name": "使用'users'作为表名",
        "sql": "SELECT id FROM users",
    }
]

config = FluffConfig(overrides={'dialect': 'hive'})

for test in test_cases:
    print(f"\n测试: {test['name']}")
    print(f"SQL: {test['sql']}")
    
    try:
        result = sqlfluff.lint(test['sql'], config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                print(f"  解析错误: {violation.get('description')}")
                break
        
        if not has_unparsable:
            print(f"  可以解析")
            if result:
                print(f"  有{len(result)}个问题")
                
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")

# 测试原始问题SQL
print(f"\n{'='*60}")
print("测试原始问题SQL（使用不同表名）:")

original_sql_template = '''SELECT 
  CAST(a.id AS VARCHAR(50)),
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200)), 
  CAST(NVL(a.bal, 0) AS DECIMAL(30,6)), 
  CAST(a.accum_bal / x.days AS DECIMAL(30,6)) 
FROM {table_name}'''

table_names = ['mytable', 'tbl', 'users', '`table`']

for table_name in table_names:
    sql = original_sql_template.format(table_name=table_name)
    print(f"\n表名: {table_name}")
    print(f"SQL: {sql[:80]}...")
    
    try:
        result = sqlfluff.lint(sql, config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                print(f"  解析错误: {violation.get('description')[:80]}...")
                break
        
        if not has_unparsable:
            print(f"  可以解析")
            
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")