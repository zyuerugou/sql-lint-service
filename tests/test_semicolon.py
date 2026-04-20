import sqlfluff
from sqlfluff.core import FluffConfig

# 测试只有分号的SQL
sql = ';;;'
print(f'测试SQL: "{sql}"')

# 测试不同方言
for dialect in ['ansi', 'hive']:
    print(f'\n方言: {dialect}')
    try:
        config = FluffConfig(overrides={'dialect': dialect})
        result = sqlfluff.lint(sql, config=config)
        
        if result:
            for violation in result:
                print(f'  {violation.get("code")}: {violation.get("description")}')
        else:
            print('  无错误')
            
    except Exception as e:
        print(f'  异常: {e}')