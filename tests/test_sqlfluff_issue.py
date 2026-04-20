import sqlfluff
from sqlfluff.core import FluffConfig

# 测试最简单的SQL
simple_sql = "SELECT 1"

print("测试最简单的SQL:")
print(f"SQL: '{simple_sql}'")

# 测试不同方言
dialects = ['hive', 'ansi', 'mysql', 'postgres']

for dialect in dialects:
    print(f"\n方言: {dialect}")
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(simple_sql, config=config)
        
        has_unparsable = False
        for violation in result:
            if 'unparsable' in violation.get('description', '').lower():
                has_unparsable = True
                print(f"  解析错误: {violation.get('description')}")
                break
        
        if not has_unparsable:
            print(f"  可以解析")
            
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")

# 测试带FROM的
print(f"\n{'='*60}")
print("测试带FROM的SQL:")
sql_with_from = "SELECT id FROM mytable"

for dialect in dialects:
    print(f"\n方言: {dialect}")
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(sql_with_from, config=config)
        
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

# 检查sqlfluff版本
print(f"\n{'='*60}")
print("sqlfluff信息:")
print(f"版本: {sqlfluff.__version__ if hasattr(sqlfluff, '__version__') else '未知'}")

# 尝试直接使用Linter类
print(f"\n{'='*60}")
print("直接使用Linter类测试:")
from sqlfluff.core import Linter

sql = "SELECT id FROM mytable"
print(f"SQL: {sql}")

for dialect in dialects:
    print(f"\n方言: {dialect}")
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        linter = Linter(config=config)
        result = linter.lint_string(sql)
        
        print(f"  解析成功，有{len(result.violations)}个问题")
        for v in result.violations[:2]:
            print(f"    {v.rule_code()}: {v.desc()}")
        if len(result.violations) > 2:
            print(f"    ...还有{len(result.violations)-2}个问题")
            
    except Exception as e:
        print(f"  异常: {type(e).__name__}: {e}")