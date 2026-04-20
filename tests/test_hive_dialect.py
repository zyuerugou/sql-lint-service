import sqlfluff
from sqlfluff.core import FluffConfig

# 测试不同方言
dialects = ['hive', 'ansi', 'mysql', 'postgres', 'bigquery']

test_sql = "SELECT CAST(NVL(a.bal, 0) AS DECIMAL(30,6)) FROM table"

print(f"测试SQL: {test_sql}")
print()

for dialect in dialects:
    print(f"{'='*60}")
    print(f"方言: {dialect}")
    
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(test_sql, config=config)
        
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
            else:
                print(f"  无问题")
                
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")

print(f"\n{'='*60}")
print("测试DECIMAL语法:")
test_decimal = "SELECT CAST(amount AS DECIMAL(30,6)) FROM table"
print(f"SQL: {test_decimal}")

for dialect in dialects:
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(test_decimal, config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                break
        
        print(f"  {dialect}: {'解析错误' if has_unparsable else '正常'}")
        
    except Exception as e:
        print(f"  {dialect}: 异常")