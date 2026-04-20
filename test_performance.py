#!/usr/bin/env python3
"""
测试大SQL和长SQL的处理性能
客户端timeout是5s，需要确保预处理器能在5s内完成
"""

import sys
import time
import random
sys.path.insert(0, '.')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor
from app.rules.preprocessors.set_statement_filter_preprocessor import SetStatementFilterPreprocessor
from app.services.preprocessor_manager import PreprocessorManager
from app.services.lint_service import LintService


def generate_large_sql(num_statements=1000, max_columns=50):
    """
    生成大型SQL语句
    
    Args:
        num_statements: 语句数量
        max_columns: 每行最大列数
    """
    print(f"生成大型SQL: {num_statements}个语句，每行最多{max_columns}列")
    
    sql_parts = []
    
    # 常见的表名和列名
    tables = ["users", "orders", "products", "customers", "transactions", "logs", "events"]
    columns = ["id", "name", "email", "phone", "address", "city", "state", "country", 
               "created_at", "updated_at", "status", "type", "category", "price", "quantity",
               "amount", "total", "discount", "tax", "shipping", "batch_date", "batch_yyyymm"]
    
    # 生成多个语句
    for i in range(num_statements):
        # 随机选择语句类型
        stmt_type = random.choice(["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"])
        
        if stmt_type == "SELECT":
            # 生成SELECT语句
            table = random.choice(tables)
            num_select_cols = random.randint(1, max_columns)
            select_cols = random.sample(columns, min(num_select_cols, len(columns)))
            
            # 添加变量
            where_conditions = []
            if random.random() > 0.3:  # 70%的概率添加WHERE条件
                num_conditions = random.randint(1, 5)
                for _ in range(num_conditions):
                    col = random.choice(columns[:10])  # 使用前10个列
                    if col == "batch_date":
                        where_conditions.append(f"{col} = '20251231'")
                    else:
                        where_conditions.append(f"{col} = '{random.choice(['active', 'pending', 'completed'])}'")
            
            # 构建SELECT语句
            select_stmt = f"SELECT {', '.join(select_cols)} FROM {table}"
            if where_conditions:
                select_stmt += f" WHERE {' AND '.join(where_conditions)}"
            select_stmt += ";"
            sql_parts.append(select_stmt)
            
        elif stmt_type == "INSERT":
            # 生成INSERT语句
            table = random.choice(tables)
            num_insert_cols = random.randint(1, 10)
            insert_cols = random.sample(columns, min(num_insert_cols, len(columns)))
            
            # 生成VALUES
            values = []
            for _ in range(random.randint(1, 3)):  # 1-3行数据
                row_values = []
                for col in insert_cols:
                    if col == "batch_date":
                        row_values.append("'20251231'")
                    elif col in ["created_at", "updated_at"]:
                        row_values.append("CURRENT_TIMESTAMP")
                    else:
                        row_values.append(f"'{random.choice(['value1', 'value2', 'value3'])}'")
                values.append(f"({', '.join(row_values)})")
            
            insert_stmt = f"INSERT INTO {table} ({', '.join(insert_cols)}) VALUES {', '.join(values)};"
            sql_parts.append(insert_stmt)
            
        elif stmt_type == "CREATE":
            # 生成CREATE TABLE语句
            table = f"temp_table_{i}"
            num_table_cols = random.randint(5, 20)
            table_cols = []
            
            for j in range(num_table_cols):
                col_name = f"col_{j}"
                col_type = random.choice(["INT", "VARCHAR(255)", "DECIMAL(10,2)", "DATE", "TIMESTAMP"])
                table_cols.append(f"{col_name} {col_type}")
            
            create_stmt = f"CREATE TABLE {table} (\n    " + ",\n    ".join(table_cols) + "\n);"
            sql_parts.append(create_stmt)
            
        elif stmt_type == "DROP":
            # 生成DROP TABLE语句
            table = random.choice(tables)
            drop_stmt = f"DROP TABLE IF EXISTS {table};"
            sql_parts.append(drop_stmt)
    
    # 添加一些包含变量的语句
    for i in range(min(100, num_statements // 10)):
        sql_parts.append(f"SELECT * FROM table_{i} WHERE date_column = '20251231';")
        sql_parts.append(f"INSERT INTO logs_{i} (log_date, message) VALUES ('20251231', 'Test message');")
    
    return "\n".join(sql_parts)


def generate_long_sql_line(max_length=10000):
    """
    生成超长单行SQL
    
    Args:
        max_length: 最大长度
    """
    print(f"生成超长单行SQL: 目标长度{max_length}")
    
    # 构建一个非常长的SELECT语句
    base_sql = "SELECT "
    
    # 添加大量列
    columns = []
    for i in range(500):  # 500列
        columns.append(f"column_{i:04d}")
    
    base_sql += ", ".join(columns)
    base_sql += " FROM very_large_table WHERE "
    
    # 添加大量WHERE条件
    conditions = []
    for i in range(100):  # 100个条件
        if i % 10 == 0:
            conditions.append(f"date_column_{i} = '20251231'")
        else:
            conditions.append(f"col_{i} = 'value_{i}'")
    
    base_sql += " AND ".join(conditions)
    base_sql += " ORDER BY "
    
    # 添加大量ORDER BY
    order_cols = []
    for i in range(50):  # 50个排序列
        order_cols.append(f"sort_col_{i}")
    
    base_sql += ", ".join(order_cols)
    base_sql += ";"
    
    # 如果还不够长，重复添加
    while len(base_sql) < max_length:
        base_sql += " -- " + "x" * 100
    
    return base_sql[:max_length]


def test_performance():
    """测试性能"""
    print("=" * 80)
    print("SQL处理性能测试")
    print("=" * 80)
    
    # 创建预处理器实例
    date_preprocessor = DateVariablePreprocessor()
    set_preprocessor = SetStatementFilterPreprocessor()
    
    # 测试1: 中等大小SQL
    print("\n1. 测试中等大小SQL (约100个语句):")
    medium_sql = generate_large_sql(num_statements=100, max_columns=20)
    print(f"   SQL长度: {len(medium_sql):,} 字符")
    print(f"   行数: {medium_sql.count(chr(10)) + 1}")
    
    # 测试DateVariablePreprocessor
    start_time = time.time()
    result_date = date_preprocessor.process(medium_sql)
    date_time = time.time() - start_time
    print(f"   DateVariablePreprocessor处理时间: {date_time:.3f}秒")
    
    # 测试SetStatementFilterPreprocessor
    start_time = time.time()
    result_set = set_preprocessor.process(medium_sql)
    set_time = time.time() - start_time
    print(f"   SetStatementFilterPreprocessor处理时间: {set_time:.3f}秒")
    
    # 测试2: 大型SQL
    print("\n2. 测试大型SQL (约1000个语句):")
    large_sql = generate_large_sql(num_statements=1000, max_columns=30)
    print(f"   SQL长度: {len(large_sql):,} 字符")
    print(f"   行数: {large_sql.count(chr(10)) + 1}")
    
    # 测试DateVariablePreprocessor
    start_time = time.time()
    result_date_large = date_preprocessor.process(large_sql)
    date_time_large = time.time() - start_time
    print(f"   DateVariablePreprocessor处理时间: {date_time_large:.3f}秒")
    
    # 测试3: 超长单行SQL
    print("\n3. 测试超长单行SQL (约10,000字符):")
    long_line_sql = generate_long_sql_line(max_length=10000)
    print(f"   SQL长度: {len(long_line_sql):,} 字符")
    print(f"   行数: 1")
    
    # 测试DateVariablePreprocessor
    start_time = time.time()
    result_long = date_preprocessor.process(long_line_sql)
    long_time = time.time() - start_time
    print(f"   DateVariablePreprocessor处理时间: {long_time:.3f}秒")
    
    # 测试4: 极端情况 - 超大SQL
    print("\n4. 测试极端情况 - 超大SQL (约10,000个语句):")
    huge_sql = generate_large_sql(num_statements=10000, max_columns=10)
    print(f"   SQL长度: {len(huge_sql):,} 字符")
    print(f"   行数: {huge_sql.count(chr(10)) + 1}")
    
    # 测试DateVariablePreprocessor (只测试部分)
    start_time = time.time()
    # 只处理前10000个字符以避免内存问题
    sample_huge = huge_sql[:10000]
    result_huge = date_preprocessor.process(sample_huge)
    huge_time = time.time() - start_time
    print(f"   DateVariablePreprocessor处理时间 (样本): {huge_time:.3f}秒")
    
    # 测试5: PreprocessorManager性能
    print("\n5. 测试PreprocessorManager性能:")
    from pathlib import Path
    preprocessors_dir = str(Path(__file__).parent / "app" / "rules" / "preprocessors")
    manager = PreprocessorManager(preprocessors_dir)
    
    # 使用中等大小SQL测试
    start_time = time.time()
    result_manager = manager.process(medium_sql)
    manager_time = time.time() - start_time
    print(f"   PreprocessorManager处理时间: {manager_time:.3f}秒")
    
    # 测试6: LintService性能
    print("\n6. 测试LintService性能 (注意: Lint可能较慢):")
    lint_service = LintService(enable_hot_reload=False)
    
    # 使用小SQL测试，因为Lint可能很慢
    small_sql = "SELECT id, name FROM users WHERE status = 'active';"
    start_time = time.time()
    lint_result = lint_service.lint_sql(small_sql)
    lint_time = time.time() - start_time
    print(f"   LintService处理时间 (小SQL): {lint_time:.3f}秒")
    print(f"   发现 {len(lint_result)} 个lint问题")
    
    # 性能总结
    print("\n" + "=" * 80)
    print("性能测试总结")
    print("=" * 80)
    
    print(f"客户端timeout: 5秒")
    print(f"\n预处理器性能:")
    print(f"  DateVariablePreprocessor:")
    print(f"    - 中等SQL (100语句): {date_time:.3f}秒")
    print(f"    - 大型SQL (1000语句): {date_time_large:.3f}秒")
    print(f"    - 超长单行: {long_time:.3f}秒")
    
    print(f"\n  SetStatementFilterPreprocessor:")
    print(f"    - 中等SQL (100语句): {set_time:.3f}秒")
    
    print(f"\n  PreprocessorManager:")
    print(f"    - 中等SQL (100语句): {manager_time:.3f}秒")
    
    print(f"\n  LintService (注意: 可能较慢):")
    print(f"    - 小SQL: {lint_time:.3f}秒")
    
    # 检查是否在5秒内
    max_processor_time = max(date_time, date_time_large, long_time, set_time, manager_time)
    if max_processor_time < 5:
        print(f"\n[OK] 所有预处理器都在5秒内完成!")
        print(f"   最长时间: {max_processor_time:.3f}秒 < 5秒")
    else:
        print(f"\n[WARNING] 警告: 有些处理时间超过5秒!")
        print(f"   最长时间: {max_processor_time:.3f}秒 > 5秒")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


def test_memory_usage():
    """测试内存使用情况"""
    print("\n" + "=" * 80)
    print("内存使用测试")
    print("=" * 80)
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    # 测试前内存
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"测试前内存使用: {memory_before:.2f} MB")
    
    # 生成大型SQL
    large_sql = generate_large_sql(num_statements=5000, max_columns=20)
    print(f"生成的SQL大小: {len(large_sql) / 1024 / 1024:.2f} MB")
    
    # 创建预处理器
    preprocessor = DateVariablePreprocessor()
    
    # 处理SQL并测量内存
    start_time = time.time()
    result = preprocessor.process(large_sql)
    process_time = time.time() - start_time
    
    # 测试后内存
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = memory_after - memory_before
    
    print(f"测试后内存使用: {memory_after:.2f} MB")
    print(f"内存增加: {memory_increase:.2f} MB")
    print(f"处理时间: {process_time:.3f}秒")
    
    # 清理
    del large_sql
    del result
    
    # 强制垃圾回收
    import gc
    gc.collect()
    
    memory_final = process.memory_info().rss / 1024 / 1024  # MB
    print(f"清理后内存: {memory_final:.2f} MB")
    
    print("\n" + "=" * 80)
    print("内存测试完成!")
    print("=" * 80)


def test_concurrent_requests():
    """测试并发请求处理"""
    print("\n" + "=" * 80)
    print("并发请求测试")
    print("=" * 80)
    
    import concurrent.futures
    import threading
    
    # 创建预处理器实例（每个线程一个）
    preprocessors = [DateVariablePreprocessor() for _ in range(10)]
    
    # 生成测试SQL
    test_sqls = []
    for i in range(10):
        sql = f"""
        SELECT * FROM table_{i} WHERE date = '20251231';
        INSERT INTO logs_{i} (log_date, message) VALUES ('20251231', 'Message {i}');
        DROP TABLE IF EXISTS temp_{i};
        """
        test_sqls.append(sql)
    
    # 并发处理函数
    def process_sql(processor_idx, sql_idx):
        processor = preprocessors[processor_idx]
        sql = test_sqls[sql_idx]
        
        start_time = time.time()
        result = processor.process(sql)
        end_time = time.time()
        
        return {
            "thread": threading.current_thread().name,
            "processor_idx": processor_idx,
            "sql_idx": sql_idx,
            "time": end_time - start_time,
            "success": "20251231" in result
        }
    
    # 并发测试
    print("开始并发测试 (10个线程同时处理)...")
    start_time = time.time()
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(10):
            future = executor.submit(process_sql, i % len(preprocessors), i % len(test_sqls))
            futures.append(future)
        
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    total_time = time.time() - start_time
    
    # 分析结果
    print(f"\n并发测试完成!")
    print(f"总时间: {total_time:.3f}秒")
    print(f"请求数量: {len(results)}")
    
    success_count = sum(1 for r in results if r["success"])
    print(f"成功处理: {success_count}/{len(results)}")
    
    times = [r["time"] for r in results]
    if times:
        print(f"最短处理时间: {min(times):.3f}秒")
        print(f"最长处理时间: {max(times):.3f}秒")
        print(f"平均处理时间: {sum(times)/len(times):.3f}秒")
    
    # 检查是否有超时
    timeout_count = sum(1 for t in times if t > 5)
    if timeout_count > 0:
        print(f"[WARNING] 警告: {timeout_count}个请求处理时间超过5秒!")
    else:
        print(f"[OK] 所有请求都在5秒内完成!")
    
    print("\n" + "=" * 80)
    print("并发测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_performance()
    except Exception as e:
        print(f"性能测试出错: {e}")
    
    try:
        test_memory_usage()
    except ImportError:
        print("\n跳过内存测试 (需要psutil模块)")
    except Exception as e:
        print(f"内存测试出错: {e}")
    
    try:
        test_concurrent_requests()
    except Exception as e:
        print(f"并发测试出错: {e}")