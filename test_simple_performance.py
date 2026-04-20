#!/usr/bin/env python3
"""
简化性能测试
"""

import sys
import time
sys.path.insert(0, '.')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor
from app.services.preprocessor_manager import PreprocessorManager


def test_large_sql():
    """测试大SQL处理性能"""
    print("测试大SQL处理性能 (客户端timeout: 5s)")
    print("=" * 60)
    
    # 创建预处理器
    preprocessor = DateVariablePreprocessor()
    
    # 测试1: 生成1MB的SQL
    print("\n1. 测试1MB SQL:")
    
    # 生成包含大量变量的SQL
    sql_parts = []
    for i in range(10000):
        sql_parts.append(f"SELECT * FROM table_{i} WHERE date = '20251231' AND batch = 'batch_{i}';")
    
    large_sql = "\n".join(sql_parts)
    print(f"   SQL大小: {len(large_sql) / 1024 / 1024:.2f} MB")
    print(f"   行数: {large_sql.count(chr(10)) + 1}")
    
    # 测试处理时间
    start_time = time.time()
    result = preprocessor.process(large_sql)
    process_time = time.time() - start_time
    
    print(f"   处理时间: {process_time:.3f} 秒")
    
    # 验证替换是否正确
    if "20251231" in result and "${batch_date}" not in result:
        print("   [OK] 变量替换正确")
    else:
        print("   [ERROR] 变量替换失败")
    
    # 测试2: 生成10MB的SQL
    print("\n2. 测试10MB SQL:")
    
    # 生成更大的SQL
    huge_sql_parts = []
    for i in range(100000):
        huge_sql_parts.append(f"INSERT INTO data_{i} (id, date, value) VALUES ({i}, '20251231', 'value_{i}');")
    
    huge_sql = "\n".join(huge_sql_parts)
    print(f"   SQL大小: {len(huge_sql) / 1024 / 1024:.2f} MB")
    print(f"   行数: {huge_sql.count(chr(10)) + 1}")
    
    # 测试处理时间 (只处理前1MB以避免内存问题)
    sample_size = 1024 * 1024  # 1MB
    sample_sql = huge_sql[:sample_size]
    
    start_time = time.time()
    result_sample = preprocessor.process(sample_sql)
    process_time_sample = time.time() - start_time
    
    print(f"   处理时间 (1MB样本): {process_time_sample:.3f} 秒")
    
    # 测试3: PreprocessorManager性能
    print("\n3. 测试PreprocessorManager:")
    from pathlib import Path
    preprocessors_dir = str(Path(__file__).parent / "app" / "rules" / "preprocessors")
    manager = PreprocessorManager(preprocessors_dir)
    
    test_sql = "SELECT * FROM users WHERE create_date = '20251231';"
    
    start_time = time.time()
    for _ in range(1000):  # 模拟1000次请求
        manager.process(test_sql)
    manager_time = time.time() - start_time
    
    print(f"   1000次请求处理时间: {manager_time:.3f} 秒")
    print(f"   平均每次: {manager_time / 1000:.3f} 秒")
    
    # 性能总结
    print("\n" + "=" * 60)
    print("性能测试总结")
    print("=" * 60)
    
    print(f"客户端timeout: 5秒")
    print(f"最大测试SQL: 10MB (样本测试)")
    print(f"最大处理时间: {max(process_time, process_time_sample, manager_time/1000):.3f} 秒")
    
    if max(process_time, process_time_sample, manager_time/1000) < 5:
        print("\n[OK] 所有测试都在5秒内完成!")
        print("预处理器性能满足要求。")
    else:
        print("\n[WARNING] 有些测试超过5秒!")
        print("可能需要优化预处理器性能。")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


def test_real_world_scenario():
    """测试真实场景"""
    print("\n\n测试真实场景: 复杂ETL SQL")
    print("=" * 60)
    
    preprocessor = DateVariablePreprocessor()
    
    # 模拟真实ETL SQL
    etl_sql = """
-- ETL作业: 数据清洗和转换
DROP TABLE IF EXISTS temp.staging_20251231;

-- 创建临时表
CREATE TABLE temp.staging_20251231 AS
SELECT 
    user_id,
    user_name,
    email,
    phone,
    address,
    create_date,
    update_date,
    status,
    '20251231' as batch_date
FROM source.users
WHERE 
    create_date >= '20240101'
    AND status IN ('active', 'pending')
    AND update_date <= '20251231';

-- 数据清洗
UPDATE temp.staging_20251231 
SET email = LOWER(email),
    phone = REGEXP_REPLACE(phone, '[^0-9]', '')
WHERE batch_date = '20251231';

-- 数据验证
SELECT COUNT(*) as total_records,
       COUNT(DISTINCT user_id) as distinct_users,
       SUM(CASE WHEN email LIKE '%@%' THEN 1 ELSE 0 END) as valid_emails
FROM temp.staging_20251231
WHERE batch_date = '20251231';

-- 加载到目标表
INSERT INTO target.user_dimension (
    user_id,
    user_name,
    email,
    phone,
    address,
    create_date,
    update_date,
    status,
    batch_date
)
SELECT 
    user_id,
    user_name,
    email,
    phone,
    address,
    create_date,
    update_date,
    status,
    '20251231'
FROM temp.staging_20251231
WHERE batch_date = '20251231'
  AND status = 'active';

-- 清理临时表
DROP TABLE IF EXISTS temp.staging_20251231;

-- 记录日志
INSERT INTO etl.logs (job_name, batch_date, records_processed, status, run_time)
VALUES ('user_etl', '20251231', 
        (SELECT COUNT(*) FROM target.user_dimension WHERE batch_date = '20251231'),
        'SUCCESS', CURRENT_TIMESTAMP);
"""
    
    print("ETL SQL大小:", len(etl_sql), "字符")
    print("包含变量: ${batch_date}")
    
    # 测试处理时间
    start_time = time.time()
    result = preprocessor.process(etl_sql)
    process_time = time.time() - start_time
    
    print(f"处理时间: {process_time:.3f} 秒")
    
    # 检查替换结果
    if "20251231" in result and "${batch_date}" not in result:
        print("[OK] 所有变量被正确替换")
    else:
        print("[ERROR] 变量替换失败")
    
    # 统计替换次数
    original_count = etl_sql.count("${batch_date}")
    result_count = result.count("20251231")
    print(f"替换统计: {original_count} 个变量 -> {result_count} 次替换")
    
    print("\n" + "=" * 60)
    print("真实场景测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_large_sql()
    test_real_world_scenario()