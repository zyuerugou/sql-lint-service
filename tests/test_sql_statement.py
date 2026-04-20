#!/usr/bin/env python3
"""
测试SQL语句处理
"""

import sys
sys.path.insert(0, '..')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor
from app.rules.preprocessors.set_statement_filter_preprocessor import SetStatementFilterPreprocessor
from app.services.preprocessor_manager import PreprocessorManager
from app.services.lint_service import LintService


def test_sql_statement():
    """测试提供的SQL语句"""
    print("=" * 80)
    print("测试SQL语句处理")
    print("=" * 80)
    
    # 提供的SQL语句
    sql = """
DROP TABLE IF EXISTS test.test_${batch_date};
CREATE TABLE test.test_${batch_date} STORED AS HOLODESC AS
SELECT id, name FROM test.test WHERE part_ymd = '${batch_date}';
INSERT INTO test.test PARTITION(part_ymd='${batch_date}') (id, name)
SELECT id, name FROM test.test_${batch_date};
DROP TABLE IF EXISTS test.test_${batch_date};
"""
    
    print("原始SQL语句:")
    print(sql)
    print("-" * 80)
    
    # 1. 测试DateVariablePreprocessor单独处理
    print("\n1. DateVariablePreprocessor处理结果:")
    date_preprocessor = DateVariablePreprocessor()
    result_date = date_preprocessor.process(sql)
    print(result_date)
    
    # 2. 测试SetStatementFilterPreprocessor单独处理
    print("\n2. SetStatementFilterPreprocessor处理结果:")
    set_preprocessor = SetStatementFilterPreprocessor()
    result_set = set_preprocessor.process(sql)
    print(result_set)
    
    # 3. 测试预处理器管理器处理
    print("\n3. PreprocessorManager处理结果:")
    from pathlib import Path
    preprocessors_dir = str(Path(__file__).parent / "app" / "rules" / "preprocessors")
    manager = PreprocessorManager(preprocessors_dir)
    result_manager = manager.process(sql)
    print(result_manager)
    
    # 4. 验证变量替换
    print("\n4. 变量替换验证:")
    expected_variables = ["batch_date"]
    for var in expected_variables:
        if f"${{{var}}}" in sql:
            print(f"  - ${{{var}}} 在原始SQL中")
        if "20251231" in result_date:
            print(f"  - ${{{var}}} 被替换为: 20251231")
    
    # 5. 测试LintService处理
    print("\n5. LintService处理结果:")
    lint_service = LintService(enable_hot_reload=False)
    lint_result = lint_service.lint_sql(sql)
    
    print(f"发现 {len(lint_result)} 个lint问题:")
    for i, violation in enumerate(lint_result, 1):
        print(f"  {i}. [{violation['rule_id']}] {violation['message']}")
        if 'line_no' in violation:
            print(f"     位置: 行{violation['line_no']}, 列{violation.get('line_pos', 'N/A')}")
    
    # 6. 详细分析每个语句
    print("\n6. 语句详细分析:")
    lines = sql.strip().split('\n')
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line:
            print(f"  语句 {i}: {line}")
            
            # 检查是否包含变量
            if "${batch_date}" in line:
                print(f"    - 包含变量: ${{batch_date}}")
                
            # 检查语句类型
            if line.upper().startswith("DROP TABLE"):
                print(f"    - 类型: DROP TABLE语句")
            elif line.upper().startswith("CREATE TABLE"):
                print(f"    - 类型: CREATE TABLE语句")
            elif line.upper().startswith("SELECT"):
                print(f"    - 类型: SELECT语句")
            elif line.upper().startswith("INSERT INTO"):
                print(f"    - 类型: INSERT语句")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


def test_variable_replacement_details():
    """测试变量替换的详细信息"""
    print("\n" + "=" * 80)
    print("变量替换详细信息")
    print("=" * 80)
    
    # 测试每个语句单独处理
    statements = [
        "DROP TABLE IF EXISTS test.test_${batch_date};",
        "CREATE TABLE test.test_${batch_date} STORED AS HOLODESC AS",
        "SELECT id, name FROM test.test WHERE part_ymd = '${batch_date}';",
        "INSERT INTO test.test PARTITION(part_ymd='${batch_date}') (id, name)",
        "SELECT id, name FROM test.test_${batch_date};",
        "DROP TABLE IF EXISTS test.test_${batch_date};"
    ]
    
    preprocessor = DateVariablePreprocessor()
    
    for i, stmt in enumerate(statements, 1):
        print(f"\n语句 {i}:")
        print(f"  原始: {stmt}")
        result = preprocessor.process(stmt)
        print(f"  处理后: {result}")
        
        # 检查替换情况
        if "${batch_date}" in stmt:
            if "20251231" in result:
                print(f"  [OK] ${{batch_date}} 被正确替换为 20251231")
            else:
                print(f"  [ERROR] ${{batch_date}} 替换失败")
        else:
            print(f"  - 不包含变量")
    
    print("\n" + "=" * 80)
    print("变量替换测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    test_sql_statement()
    test_variable_replacement_details()