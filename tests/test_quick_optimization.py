#!/usr/bin/env python3
"""
快速测试优化效果
"""

import sys
import time
sys.path.insert(0, '..')

# 测试优化服务的关键功能
from app.services.lint_service import LintService


def test_basic_functionality():
    """测试基本功能"""
    print("测试LintService基本功能")
    print("=" * 60)
    
    # 创建服务
    service = LintService(
        enable_hot_reload=False,
        timeout_seconds=3,
        max_sql_size_mb=1,
        enable_sampling=True,
        sampling_threshold_kb=50,
        cache_size=10
    )
    
    # 测试1: 正常SQL
    print("\n1. 测试正常SQL:")
    sql = "SELECT id, name FROM users WHERE status = 'active';"
    result = service.lint_sql(sql)
    print(f"   SQL: {sql}")
    print(f"   结果: {len(result)} 个问题")
    
    # 测试2: 缓存功能
    print("\n2. 测试缓存功能:")
    
    # 第一次查询
    start = time.time()
    result1 = service.lint_sql(sql)
    time1 = time.time() - start
    
    # 第二次查询
    start = time.time()
    result2 = service.lint_sql(sql)
    time2 = time.time() - start
    
    print(f"   第一次: {time1:.3f}秒")
    print(f"   第二次: {time2:.3f}秒")
    if time2 > 0:
        print(f"   缓存加速: {time1/time2:.1f}x")
    else:
        print(f"   缓存加速: 极快")
    
    # 测试3: 大小限制
    print("\n3. 测试大小限制 (1MB限制):")
    large_sql = "SELECT * FROM large_table;" * 50000  # 约2MB
    print(f"   SQL大小: {len(large_sql)/1024/1024:.1f}MB")
    
    result = service.lint_sql(large_sql)
    print(f"   结果: {len(result)} 个问题")
    if result:
        print(f"   错误类型: {result[0]['rule_id']}")
        print(f"   错误信息: {result[0]['message']}")
    
    # 测试4: 采样功能
    print("\n4. 测试采样功能 (阈值50KB):")
    medium_sql = ""
    for i in range(200):
        medium_sql += f"SELECT * FROM table_{i} WHERE date = '2025-12-31' AND status = 'active';\n"
    
    print(f"   SQL大小: {len(medium_sql)/1024:.1f}KB")
    
    result = service.lint_sql(medium_sql)
    print(f"   结果: {len(result)} 个问题")
    
    # 显示统计
    print("\n5. 服务统计:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("基本功能测试完成!")
    print("=" * 60)


def test_timeout_protection():
    """测试超时保护"""
    print("\n\n测试超时保护功能")
    print("=" * 60)
    
    # 创建服务，设置1秒超时
    service = LintService(
        enable_hot_reload=False,
        timeout_seconds=1,  # 1秒超时
        max_sql_size_mb=5,
        enable_sampling=False,
        cache_size=5
    )
    
    # 创建一个可能超时的复杂SQL
    print("生成复杂SQL...")
    complex_sql = ""
    for i in range(100):
        complex_sql += f"""
        WITH recursive_cte AS (
            SELECT 1 as level
            UNION ALL
            SELECT level + 1 FROM recursive_cte WHERE level < 50
        )
        SELECT 
            cte.level,
            t1.*,
            t2.*
        FROM recursive_cte cte
        CROSS JOIN (SELECT * FROM large_table_1 WHERE status = 'active') t1
        CROSS JOIN (SELECT * FROM large_table_2 WHERE category = 'electronics') t2
        WHERE t1.id = t2.ref_id 
            AND t1.create_date >= '2024-01-01'
            AND t2.update_date <= '2025-12-31'
        ORDER BY cte.level, t1.id, t2.id;
        """
    
    print(f"SQL大小: {len(complex_sql)/1024:.1f}KB")
    print(f"超时设置: {service.timeout_seconds}秒")
    
    print("\n开始处理（可能触发超时）...")
    start_time = time.time()
    result = service.lint_sql(complex_sql)
    process_time = time.time() - start_time
    
    print(f"实际处理时间: {process_time:.3f}秒")
    print(f"结果数量: {len(result)}")
    
    if result:
        print(f"第一个结果: {result[0]['rule_id']} - {result[0]['message']}")
    
    if process_time > service.timeout_seconds:
        print("[WARNING] 实际处理时间超过超时设置!")
    else:
        print("[OK] 在超时时间内完成")
    
    print("\n" + "=" * 60)
    print("超时保护测试完成!")
    print("=" * 60)


def test_performance_improvement():
    """测试性能改进"""
    print("\n\n测试性能改进")
    print("=" * 60)
    
    # 测试不同配置的性能
    test_sql = "SELECT id, name, email FROM users WHERE status = 'active' AND create_date > '2024-01-01';" * 100
    
    print(f"测试SQL大小: {len(test_sql)/1024:.1f}KB")
    
    # 配置1: 无优化
    print("\n1. 无采样，无缓存:")
    service1 = LintService(
        enable_hot_reload=False,
        timeout_seconds=10,
        max_sql_size_mb=10,
        enable_sampling=False,
        sampling_threshold_kb=0,
        cache_size=0
    )
    
    start_time = time.time()
    result1 = service1.lint_sql(test_sql)
    time1 = time.time() - start_time
    print(f"   处理时间: {time1:.3f}秒")
    print(f"   问题数量: {len(result1)}")
    
    # 配置2: 有采样
    print("\n2. 有采样 (阈值50KB):")
    service2 = LintService(
        enable_hot_reload=False,
        timeout_seconds=10,
        max_sql_size_mb=10,
        enable_sampling=True,
        sampling_threshold_kb=50,
        cache_size=0
    )
    
    start_time = time.time()
    result2 = service2.lint_sql(test_sql)
    time2 = time.time() - start_time
    print(f"   处理时间: {time2:.3f}秒")
    print(f"   问题数量: {len(result2)}")
    if time2 > 0:
        print(f"   速度提升: {time1/time2:.1f}x")
    else:
        print(f"   速度提升: 极快")
    
    # 配置3: 有缓存
    print("\n3. 有缓存:")
    service3 = LintService(
        enable_hot_reload=False,
        timeout_seconds=10,
        max_sql_size_mb=10,
        enable_sampling=False,
        sampling_threshold_kb=0,
        cache_size=10
    )
    
    # 第一次查询
    start_time = time.time()
    result3a = service3.lint_sql(test_sql)
    time3a = time.time() - start_time
    
    # 第二次查询（应命中缓存）
    start_time = time.time()
    result3b = service3.lint_sql(test_sql)
    time3b = time.time() - start_time
    
    print(f"   第一次: {time3a:.3f}秒")
    print(f"   第二次: {time3b:.3f}秒")
    if time3b > 0:
        print(f"   缓存加速: {time3a/time3b:.1f}x")
    else:
        print(f"   缓存加速: 极快")
    
    # 配置4: 完整优化
    print("\n4. 完整优化 (采样+缓存):")
    service4 = LintService(
        enable_hot_reload=False,
        timeout_seconds=10,
        max_sql_size_mb=10,
        enable_sampling=True,
        sampling_threshold_kb=50,
        cache_size=10
    )
    
    start_time = time.time()
    result4 = service4.lint_sql(test_sql)
    time4 = time.time() - start_time
    print(f"   处理时间: {time4:.3f}秒")
    print(f"   问题数量: {len(result4)}")
    if time4 > 0:
        print(f"   总速度提升: {time1/time4:.1f}x")
    else:
        print(f"   总速度提升: 极快")
    
    print("\n" + "=" * 60)
    print("性能改进测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_functionality()
    test_timeout_protection()
    test_performance_improvement()