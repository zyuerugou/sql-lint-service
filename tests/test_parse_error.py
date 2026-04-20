import sqlfluff
from sqlfluff.core import FluffConfig

# 测试一些可能导致解析错误的SQL
test_cases = [
    {
        "name": "语法错误SQL",
        "sql": "SELECT * FROM table WHERE id = 'test' AND",  # 不完整的SQL
    },
    {
        "name": "无效语法",
        "sql": "SELECT * FROM WHERE id = 1",  # 缺少表名
    },
    {
        "name": "无效函数",
        "sql": "SELECT FOO() FROM table",  # 可能不存在的函数
    },
    {
        "name": "复杂嵌套CASE",
        "sql": '''SELECT 
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200))
FROM table''',
    },
    {
        "name": "带NVL函数",
        "sql": "SELECT CAST(NVL(a.bal, 0) AS DECIMAL(30,6)) FROM table",
    },
    {
        "name": "DECIMAL类型",
        "sql": "SELECT CAST(amount AS DECIMAL(30,6)) FROM table",
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
                print(f"发现未解析错误: {desc}")
                print(f"  完整错误: {violation}")
                break
        
        if not has_unparsable:
            print("可以正常解析")
            if result:
                print(f"有{len(result)}个格式/风格问题")
                for i, v in enumerate(result[:3], 1):
                    print(f"  {i}. {v.get('code')}: {v.get('description')}")
                if len(result) > 3:
                    print(f"  ...还有{len(result)-3}个问题")
            else:
                print("无问题")
                
    except Exception as e:
        print(f"解析异常: {type(e).__name__}: {e}")