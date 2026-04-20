import sqlfluff
from sqlfluff.core import FluffConfig

# 测试Hive支持的语法
test_cases = [
    {
        "name": "使用COALESCE代替NVL",
        "sql": "SELECT CAST(COALESCE(a.bal, 0) AS DECIMAL(30,6)) FROM table",
    },
    {
        "name": "使用DECIMAL无参数",
        "sql": "SELECT CAST(amount AS DECIMAL) FROM table",
    },
    {
        "name": "使用DECIMAL带参数（可能不支持）",
        "sql": "SELECT CAST(amount AS DECIMAL(30,6)) FROM table",
    },
    {
        "name": "使用STRING代替VARCHAR",
        "sql": "SELECT CAST(id AS STRING) FROM table",
    },
    {
        "name": "完整测试（使用Hive语法）",
        "sql": '''SELECT 
  CAST(a.id AS STRING),
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS STRING), 
  CAST(COALESCE(a.bal, 0) AS DOUBLE), 
  CAST(a.accum_bal / x.days AS DOUBLE) 
FROM table''',
    }
]

config = FluffConfig(overrides={'dialect': 'hive'})

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"测试: {test['name']}")
    print(f"SQL: {test['sql'][:100]}..." if len(test['sql']) > 100 else f"SQL: {test['sql']}")
    
    try:
        result = sqlfluff.lint(test['sql'], config=config)
        
        # 检查是否有解析错误
        has_unparsable = False
        for violation in result:
            desc = violation.get('description', '')
            if 'unparsable' in desc.lower():
                has_unparsable = True
                print(f"  解析错误: {desc}")
                break
        
        if not has_unparsable:
            print(f"  可以正常解析")
            if result:
                print(f"  有{len(result)}个格式/风格问题")
                for i, v in enumerate(result[:3], 1):
                    print(f"    {i}. {v.get('code')}: {v.get('description')}")
                if len(result) > 3:
                    print(f"    ...还有{len(result)-3}个问题")
            else:
                print(f"  无问题")
                
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")