import sqlfluff
from sqlfluff.core import FluffConfig

# 测试Hive的CAST语法
test_cases = [
    {
        "name": "Hive CAST标准语法",
        "sql": "SELECT CAST(amount AS DECIMAL(10,2)) FROM table",
    },
    {
        "name": "不带参数的CAST",
        "sql": "SELECT CAST(amount AS INT) FROM table",
    },
    {
        "name": "直接使用类型转换函数",
        "sql": "SELECT DECIMAL(amount, 10, 2) FROM table",
    },
    {
        "name": "使用CONVERT函数",
        "sql": "SELECT CONVERT(amount, DECIMAL(10,2)) FROM table",
    },
    {
        "name": "简单查询测试",
        "sql": "SELECT id, name FROM table",
    },
    {
        "name": "带WHERE的简单查询",
        "sql": "SELECT * FROM table WHERE id = 1",
    }
]

config = FluffConfig(overrides={'dialect': 'hive'})

for test in test_cases:
    print(f"\n{'='*60}")
    print(f"测试: {test['name']}")
    print(f"SQL: {test['sql']}")
    
    try:
        # 先尝试解析
        parsed = sqlfluff.parse(test['sql'], config=config)
        print(f"  解析成功")
        
        # 再检查lint
        result = sqlfluff.lint(test['sql'], config=config)
        
        # 检查是否有解析错误
        has_unparsable = False
        for violation in result:
            desc = violation.get('description', '')
            if 'unparsable' in desc.lower():
                has_unparsable = True
                print(f"  但有解析错误: {desc}")
                break
        
        if not has_unparsable:
            if result:
                print(f"  有{len(result)}个格式/风格问题")
            else:
                print(f"  无问题")
                
    except Exception as e:
        print(f"  解析异常: {type(e).__name__}: {e}")

# 测试原始SQL在ansi方言下
print(f"\n{'='*60}")
print("在ansi方言下测试原始SQL:")
original_sql = "SELECT CAST(NVL(a.bal, 0) AS DECIMAL(30,6)) FROM table"
print(f"SQL: {original_sql}")

ansi_config = FluffConfig(overrides={'dialect': 'ansi'})
try:
    result = sqlfluff.lint(original_sql, config=ansi_config)
    has_unparsable = False
    for violation in result:
        if 'unparsable' in violation.get('description', '').lower():
            has_unparsable = True
            print(f"  ansi方言: 解析错误")
            break
    
    if not has_unparsable:
        print(f"  ansi方言: 可以解析，有{len(result)}个问题")
        
except Exception as e:
    print(f"  ansi方言异常: {e}")