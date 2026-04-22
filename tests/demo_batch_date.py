#!/usr/bin/env python3
"""
演示脚本：验证batch_date默认值设置为20251231
"""

import sys
sys.path.insert(0, '.')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor
from app.services.preprocessor_manager import PreprocessorManager
from app.services.lint_service import LintService


def demo_date_variable_preprocessor():
    """演示日期变量预处理器"""
    print("=" * 60)
    print("演示：DateVariablePreprocessor默认batch_date值")
    print("=" * 60)
    
    # 1. 创建预处理器实例
    preprocessor = DateVariablePreprocessor()
    print(f"1. DateVariablePreprocessor默认batch_date: {preprocessor.default_variables['batch_date']}")
    print(f"   默认batch_yyyymm: {preprocessor.default_variables['batch_yyyymm']}")
    print(f"   默认next_date: {preprocessor.default_variables['next_date']}")
    print(f"   默认last_date: {preprocessor.default_variables['last_date']}")
    
    # 2. 测试SQL处理
    test_sql = """
    SELECT 
        user_id,
        user_name,
        create_date
    FROM users
    WHERE 
        create_date = '${batch_date}'
        AND update_date = '${batch_yyyymm}'
        AND status = '${unknown_var}'
    """
    
    print(f"\n2. 测试SQL处理（无上下文）:")
    print(f"   原始SQL: {test_sql.strip()}")
    
    result = preprocessor.process(test_sql)
    print(f"   处理后SQL: {result.strip()}")
    
    # 3. 测试忽略上下文的情况
    print(f"\n3. 测试SQL处理（忽略上下文）:")
    context = {"batch_date": "20250101"}
    result_with_context = preprocessor.process(test_sql, context)
    print(f"   处理后SQL: {result_with_context.strip()}")
    print(f"   注意：即使提供了context，也使用默认值20251231")
    
    # 4. 测试预处理器管理器
    print(f"\n4. 测试PreprocessorManager:")
    from pathlib import Path
    preprocessors_dir = str(Path(__file__).parent / "app" / "rules" / "preprocessors")
    manager = PreprocessorManager(preprocessors_dir)
    preprocessors_info = manager.get_preprocessors_info()
    
    for info in preprocessors_info:
        print(f"   - {info['name']}: order={info['order']}, description={info['description']}")
    
    # 5. 测试LintService集成
    print(f"\n5. 测试LintService集成:")
    lint_service = LintService(enable_hot_reload=False)
    
    sql_with_vars = """
    set hive.exec.dynamic.partition.mode=nonstrict;
    SELECT * FROM orders 
    WHERE order_date = '${batch_date}'
    AND region = '${batch_yyyymm}'
    AND status = '${unknown_var}';
    """
    
    print(f"   测试SQL: {sql_with_vars.strip()}")
    result = lint_service.lint_sql(sql_with_vars)
    
    print(f"   Lint结果: {len(result)} 个问题")
    for violation in result:
        print(f"     - {violation['rule_id']}: {violation['message']}")
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


def demo_useful_date_variables():
    """演示get_useful_date变量列表"""
    print("\n" + "=" * 60)
    print("演示：get_useful_date变量列表")
    print("=" * 60)
    
    preprocessor = DateVariablePreprocessor()
    
    print(f"get_useful_date方法返回的变量数量: {len(preprocessor.useful_date_variables)}")
    print("\n变量列表:")
    
    # 分组显示变量
    groups = {
        "基础日期": ["batch_date", "batch_yyyymm", "next_date", "last_date", "max_date", "min_date"],
        "时间戳": ["batch_timestamp", "batch_timestamp_with_t"],
        "周相关": ["retain_week", "week_start", "week_end", "next_week_start", "next_week_end", "last_week_start", "last_week_end"],
        "月相关": ["retain_month", "month_start", "month_end", "next_month_start", "next_month_end", "last_month_start", "last_month_end", "last_month_yyyymm", "previous_month_start", "previous_month_end", "previous_month_yyyymm"],
        "季度相关": ["quarter_start", "quarter_end", "next_quarter_start", "next_quarter_end", "last_quarter_start", "last_quarter_end"],
        "年相关": ["year_start", "year_end", "next_year_start", "next_year_end", "last_year_start", "last_year_end", "last_year_bath_date", "year_before_last_bath_date"],
    }
    
    for group_name, variables in groups.items():
        print(f"\n{group_name}:")
        for var in variables:
            if var in preprocessor.useful_date_variables:
                default_value = preprocessor.default_variables.get(var, "N/A")
                print(f"  - {var}: {default_value}")
    
    print("\n" + "=" * 60)
    print("变量列表演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo_date_variable_preprocessor()
    demo_useful_date_variables()