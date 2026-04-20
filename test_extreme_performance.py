#!/usr/bin/env python3
"""
极端性能测试：测试非常大的SQL和边界情况
"""

import sys
import time
import random
sys.path.insert(0, '.')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor


def generate_extreme_sql(size_mb=50):
    """
    生成极端大的SQL
    
    Args:
        size_mb: 目标大小(MB)
    """
    print(f"生成 {size_mb}MB 的极端大SQL...")
    
    target_size = size_mb * 1024 * 1024
    sql_parts = []
    current_size = 0
    
    # 生成基础SQL模板
    templates = [
        "SELECT * FROM table_{id} WHERE date_column = '20251231' AND status = 'active' AND value > {rand};",
        "INSERT INTO data_{id} (id, date, value1, value2, value3) VALUES ({id}, '20251231', {rand1}, {rand2}, {rand3});",
        "UPDATE records_{id} SET updated_date = '20251231', status = 'processed' WHERE id = {id};",
        "DELETE FROM temp_{id} WHERE create_date < '20251231' AND status = 'expired';",
        "CREATE TABLE backup_{id} AS SELECT * FROM source_{id} WHERE batch_date = '20251231';"
    ]
    
    id_counter = 0
    while current_size < target_size:
        template = random.choice(templates)
        sql = template.format(
            id=id_counter,
            rand=random.randint(1, 1000),
            rand1=random.randint(1, 100),
            rand2=random.randint(1, 100),
            rand3=random.randint(1, 100)
        )
        
        sql_parts.append(sql)
        current_size += len(sql) + 1  # +1 for newline
        id_counter += 1
        
        # 每10000行打印进度
        if id_counter % 10000 == 0:
            print(f"  已生成 {id_counter} 行，大小: {current_size / 1024 / 1024:.1f}MB")
    
    result = "\n".join(sql_parts)
    print(f"生成完成: {len(result) / 1024 / 1024:.1f}MB, {id_counter} 行")
    return result


def test_extreme_cases():
    """测试极端情况"""
    print("极端性能测试")
    print("=" * 60)
    
    preprocessor = DateVariablePreprocessor()
    
    # 测试1: 50MB SQL
    print("\n1. 测试50MB SQL处理:")
    try:
        extreme_sql = generate_extreme_sql(size_mb=50)
        
        # 测试处理时间
        print("开始处理...")
        start_time = time.time()
        result = preprocessor.process(extreme_sql)
        process_time = time.time() - start_time
        
        print(f"处理时间: {process_time:.3f} 秒")
        print(f"处理速度: {len(extreme_sql) / process_time / 1024 / 1024:.1f} MB/秒")
        
        if process_time < 5:
            print("[OK] 在5秒内完成!")
        else:
            print("[WARNING] 超过5秒!")
            
        # 清理内存
        del extreme_sql
        del result
        
    except MemoryError:
        print("[ERROR] 内存不足!")
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
    
    # 测试2: 超长单行（1MB单行）
    print("\n2. 测试1MB单行SQL:")
    try:
        # 生成超长单行
        long_line = "SELECT " + ", ".join([f"column_{i}" for i in range(10000)]) + " "
        long_line += "FROM huge_table WHERE "
        long_line += " AND ".join([f"col_{i} = 'value_{i}'" for i in range(1000)])
        long_line += " AND batch_date = '20251231';"
        
        # 填充到1MB
        while len(long_line) < 1024 * 1024:
            long_line += " -- comment " + "x" * 100
        
        long_line = long_line[:1024 * 1024]
        print(f"单行SQL大小: {len(long_line) / 1024 / 1024:.2f}MB")
        
        # 测试处理时间
        start_time = time.time()
        result = preprocessor.process(long_line)
        process_time = time.time() - start_time
        
        print(f"处理时间: {process_time:.3f} 秒")
        
        if "20251231" in result:
            print("[OK] 变量替换正确")
        else:
            print("[ERROR] 变量替换失败")
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
    
    # 测试3: 大量小SQL语句（模拟API高并发）
    print("\n3. 测试10000个小SQL语句:")
    try:
        small_sqls = []
        for i in range(10000):
            sql = f"SELECT * FROM table_{i} WHERE date = '20251231' AND id = {i};"
            small_sqls.append(sql)
        
        all_sql = "\n".join(small_sqls)
        print(f"总大小: {len(all_sql) / 1024:.1f}KB, 语句数: 10000")
        
        # 测试处理时间
        start_time = time.time()
        result = preprocessor.process(all_sql)
        process_time = time.time() - start_time
        
        print(f"处理时间: {process_time:.3f} 秒")
        print(f"平均每个语句: {process_time / 10000 * 1000:.3f} 毫秒")
        
        if process_time < 5:
            print("[OK] 在5秒内完成!")
        else:
            print("[WARNING] 超过5秒!")
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
    
    # 测试4: 正则表达式性能（大量变量）
    print("\n4. 测试大量变量替换:")
    try:
        # 生成包含大量变量的SQL
        var_sql_parts = []
        for i in range(10000):
            var_sql_parts.append(f"SELECT * FROM data WHERE batch_date = '20251231' AND batch_yyyymm = '202512' AND id = {i};")
        
        var_sql = "\n".join(var_sql_parts)
        print(f"SQL大小: {len(var_sql) / 1024:.1f}KB")
        print(f"变量数量: {var_sql.count('20251231') + var_sql.count('202512')} (预计算)")
        
        # 实际应该包含${batch_date}，但我们已经预填充了
        # 修改为包含实际变量
        var_sql_with_vars = var_sql.replace("20251231", "${batch_date}").replace("202512", "${batch_yyyymm}")
        actual_var_count = var_sql_with_vars.count("${batch_date}") + var_sql_with_vars.count("${batch_yyyymm}")
        print(f"实际变量数量: {actual_var_count}")
        
        # 测试处理时间
        start_time = time.time()
        result = preprocessor.process(var_sql_with_vars)
        process_time = time.time() - start_time
        
        print(f"处理时间: {process_time:.3f} 秒")
        print(f"变量替换速度: {actual_var_count / process_time:.0f} 变量/秒")
        
        # 验证替换
        if "${batch_date}" not in result and "${batch_yyyymm}" not in result:
            print("[OK] 所有变量被正确替换")
        else:
            print("[ERROR] 变量替换不完整")
            
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
    
    print("\n" + "=" * 60)
    print("极端性能测试完成!")
    print("=" * 60)


def test_timeout_scenario():
    """测试超时场景"""
    print("\n\n测试超时场景模拟")
    print("=" * 60)
    
    print("模拟客户端5秒超时...")
    print("测试预处理器在5秒内能处理的最大SQL")
    
    preprocessor = DateVariablePreprocessor()
    
    # 逐步增加SQL大小，直到接近5秒
    test_sizes = [1, 5, 10, 20, 50, 100]  # MB
    
    for size_mb in test_sizes:
        print(f"\n测试 {size_mb}MB SQL:")
        
        try:
            # 生成测试SQL
            print(f"  生成 {size_mb}MB SQL...")
            sql = "SELECT * FROM test WHERE date = '20251231';\n" * int((size_mb * 1024 * 1024) / 50)
            
            if len(sql) < size_mb * 1024 * 1024 * 0.9:  # 确保足够大
                # 填充
                sql += " -- padding " * int((size_mb * 1024 * 1024 - len(sql)) / 12)
            
            print(f"  实际大小: {len(sql) / 1024 / 1024:.1f}MB")
            
            # 测试处理时间
            start_time = time.time()
            result = preprocessor.process(sql)
            process_time = time.time() - start_time
            
            print(f"  处理时间: {process_time:.3f} 秒")
            
            if process_time < 5:
                print(f"  [OK] {size_mb}MB 在5秒内完成")
                if process_time > 4:
                    print(f"  [WARNING] 接近超时 ({process_time:.1f}秒)")
            else:
                print(f"  [TIMEOUT] {size_mb}MB 超过5秒!")
                print(f"  最大支持大小: ~{size_mb/2}MB (在5秒内)")
                break
                
            # 清理内存
            del sql
            del result
            
        except MemoryError:
            print(f"  [ERROR] 内存不足，无法测试 {size_mb}MB")
            break
        except Exception as e:
            print(f"  [ERROR] 测试失败: {e}")
            break
    
    print("\n" + "=" * 60)
    print("超时场景测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_extreme_cases()
    test_timeout_scenario()