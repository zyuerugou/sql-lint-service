#!/usr/bin/env python3
"""
测试优化的LintService
"""

import sys
import time
sys.path.insert(0, '.')

from app.services.lint_service import LintService  # 优化版本


def compare_performance():
    """对比原始服务和优化服务的性能"""
    print("对比原始LintService和优化后的LintService")
    print("=" * 80)
    
    # 生成测试SQL
    def generate_test_sql(size_kb):
        """生成测试SQL"""
        base_sql = "SELECT * FROM users WHERE status = 'active';\n"
        return base_sql * int((size_kb * 1024) / len(base_sql))
    
    # 测试不同大小的SQL
    test_cases = [
        ("小SQL", 10),      # 10KB
        ("中SQL", 100),     # 100KB
        ("大SQL", 500),     # 500KB
        ("超大SQL", 2000),  # 2MB
    ]
    
    for name, size_kb in test_cases:
        print(f"\n{'='*40}")
        print(f"测试: {name} ({size_kb}KB)")
        print('='*40)
        
        # 生成SQL
        sql = generate_test_sql(size_kb)
        print(f"SQL大小: {len(sql)/1024:.1f}KB")
        
        # 测试原始服务
        print(f"\n1. 原始LintService:")
        try:
            original_service = LintService(enable_hot_reload=False)
            
            start_time = time.time()
            result = original_service.lint_sql(sql)
            original_time = time.time() - start_time
            
            print(f"   处理时间: {original_time:.3f}秒")
            print(f"   发现问题: {len(result)}个")
            
            if original_time > 5:
                print(f"   [TIMEOUT] 超过5秒!")
            else:
                print(f"   [OK] 在5秒内完成")
                
        except Exception as e:
            print(f"   [ERROR] 处理失败: {e}")
            original_time = 999
        
        # 测试优化服务
        print(f"\n2. 优化LintService:")
        try:
            optimized_service = LintService(
                enable_hot_reload=False,
                timeout_seconds=5,
                max_sql_size_mb=10,
                enable_sampling=True,
                sampling_threshold_kb=100,
                cache_size=10
            )
            
            start_time = time.time()
            result = optimized_service.lint_sql(sql)
            optimized_time = time.time() - start_time
            
            print(f"   处理时间: {optimized_time:.3f}秒")
            print(f"   发现问题: {len(result)}个")
            
            # 检查是否有超时或大小限制错误
            timeout_errors = [r for r in result if r["rule_id"] in ["TIMEOUT", "SIZE_LIMIT"]]
            if timeout_errors:
                print(f"   [PROTECTED] 触发保护机制: {timeout_errors[0]['message']}")
            else:
                print(f"   [OK] 正常完成")
            
            # 显示统计信息
            stats = optimized_service.get_stats()
            print(f"   缓存使用: {stats['cache_size']}/{stats['cache_capacity']}")
            
        except Exception as e:
            print(f"   [ERROR] 处理失败: {e}")
            optimized_time = 999
        
        # 性能对比
        if original_time < 999 and optimized_time < 999:
            print(f"\n3. 性能对比:")
            print(f"   原始服务: {original_time:.3f}秒")
            print(f"   优化服务: {optimized_time:.3f}秒")
            
            if original_time > 0:
                speedup = original_time / optimized_time if optimized_time > 0 else 0
                print(f"   速度比: {speedup:.1f}x")
    
    print(f"\n{'='*80}")
    print("性能对比测试完成!")
    print("=" * 80)


def test_optimization_features():
    """测试优化功能"""
    print("\n\n测试LintService的优化功能")
    print("=" * 80)
    
    # 创建优化服务
    service = LintService(
        enable_hot_reload=False,
        timeout_seconds=3,  # 更短的超时时间用于测试
        max_sql_size_mb=1,  # 1MB限制
        enable_sampling=True,
        sampling_threshold_kb=50,
        cache_size=5
    )
    
    print(f"服务配置:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 测试1: 正常SQL
    print(f"\n1. 测试正常SQL (10KB):")
    normal_sql = "SELECT id, name, email FROM users WHERE status = 'active' AND create_date > '2024-01-01';" * 100
    print(f"   SQL大小: {len(normal_sql)/1024:.1f}KB")
    
    result = service.lint_sql(normal_sql)
    print(f"   结果: {len(result)} 个问题")
    for issue in result[:3]:  # 显示前3个问题
        print(f"     - [{issue['rule_id']}] {issue['message']}")
    
    # 测试2: 超大SQL（应触发大小限制）
    print(f"\n2. 测试超大SQL (2MB，应触发大小限制):")
    huge_sql = "SELECT * FROM large_table;" * 50000
    print(f"   SQL大小: {len(huge_sql)/1024/1024:.1f}MB")
    
    result = service.lint_sql(huge_sql)
    print(f"   结果: {len(result)} 个问题")
    for issue in result:
        print(f"     - [{issue['rule_id']}] {issue['message']}")
    
    # 测试3: 复杂SQL（应触发采样）
    print(f"\n3. 测试复杂SQL (200KB，应触发采样):")
    complex_sql = ""
    for i in range(1000):
        complex_sql += f"""
        SELECT 
            u.id,
            u.name,
            u.email,
            o.order_id,
            o.order_date,
            o.total_amount,
            p.product_name,
            p.category,
            a.shipping_address
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        INNER JOIN products p ON o.product_id = p.id
        LEFT JOIN addresses a ON u.id = a.user_id
        WHERE u.status = 'active'
            AND o.order_date >= '2024-01-01'
            AND p.category IN ('electronics', 'books', 'clothing')
            AND (a.country = 'US' OR a.country = 'CA')
        GROUP BY u.id, u.name, u.email, o.order_id, o.order_date, 
                o.total_amount, p.product_name, p.category,
                a.shipping_address
        HAVING COUNT(o.order_id) > 0
        ORDER BY o.total_amount DESC, u.name ASC
        LIMIT 100;
        """
    
    print(f"   SQL大小: {len(complex_sql)/1024:.1f}KB")
    
    result = service.lint_sql(complex_sql)
    print(f"   结果: {len(result)} 个问题")
    
    # 检查是否有采样标记
    if any("[SAMPLED]" in str(r) for r in result):
        print("   [INFO] 检测到采样检查")
    
    # 测试4: 缓存功能
    print(f"\n4. 测试缓存功能:")
    test_sql = "SELECT * FROM test_table WHERE id = 1;"
    
    # 第一次查询
    start_time = time.time()
    result1 = service.lint_sql(test_sql)
    time1 = time.time() - start_time
    
    # 第二次查询（应命中缓存）
    start_time = time.time()
    result2 = service.lint_sql(test_sql)
    time2 = time.time() - start_time
    
    print(f"   第一次查询: {time1:.3f}秒")
    print(f"   第二次查询: {time2:.3f}秒")
    print(f"   缓存加速: {time1/time2:.1f}x")
    
    # 测试5: 超时保护
    print(f"\n5. 测试超时保护 (设置1秒超时):")
    # 创建新的服务，设置1秒超时
    fast_service = LintService(
        enable_hot_reload=False,
        timeout_seconds=1,  # 1秒超时
        max_sql_size_mb=10,
        enable_sampling=False,
        cache_size=5
    )
    
    # 生成一个可能超时的SQL
    slow_sql = ""
    for i in range(500):
        slow_sql += f"""
        WITH recursive_cte AS (
            SELECT 1 as level
            UNION ALL
            SELECT level + 1 FROM recursive_cte WHERE level < 100
        )
        SELECT * FROM recursive_cte
        CROSS JOIN (SELECT * FROM large_table_1) t1
        CROSS JOIN (SELECT * FROM large_table_2) t2
        WHERE t1.id = t2.ref_id AND t1.status = 'active';
        """
    
    print(f"   SQL大小: {len(slow_sql)/1024:.1f}KB")
    
    result = fast_service.lint_sql(slow_sql)
    print(f"   结果: {len(result)} 个问题")
    for issue in result:
        print(f"     - [{issue['rule_id']}] {issue['message']}")
    
    print(f"\n{'='*80}")
    print("优化功能测试完成!")
    print("=" * 80)


def test_real_world_scenarios():
    """测试真实场景"""
    print("\n\n测试真实场景")
    print("=" * 80)
    
    # 创建优化服务（生产环境配置）
    service = LintService(
        enable_hot_reload=False,
        timeout_seconds=5,
        max_sql_size_mb=5,  # 5MB限制
        enable_sampling=True,
        sampling_threshold_kb=200,  # 200KB以上启用采样
        cache_size=50
    )
    
    print("生产环境配置:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 真实场景1: ETL作业SQL
    print(f"\n1. ETL作业SQL测试:")
    etl_sql = """
-- 数据清洗和转换
WITH cleaned_data AS (
    SELECT 
        user_id,
        TRIM(LOWER(email)) as email,
        REGEXP_REPLACE(phone, '[^0-9]', '') as phone,
        create_date,
        update_date,
        status,
        '20251231' as batch_date
    FROM source.users
    WHERE create_date >= '2024-01-01'
        AND status IN ('active', 'pending')
),
enriched_data AS (
    SELECT 
        cd.*,
        COALESCE(o.order_count, 0) as order_count,
        COALESCE(o.total_spent, 0) as total_spent,
        COALESCE(p.preferred_category, 'unknown') as preferred_category
    FROM cleaned_data cd
    LEFT JOIN (
        SELECT 
            user_id,
            COUNT(*) as order_count,
            SUM(total_amount) as total_spent
        FROM source.orders
        WHERE order_date >= '2024-01-01'
        GROUP BY user_id
    ) o ON cd.user_id = o.user_id
    LEFT JOIN (
        SELECT 
            o.user_id,
            p.category as preferred_category
        FROM source.orders o
        JOIN source.products p ON o.product_id = p.id
        WHERE o.order_date >= '2024-01-01'
        GROUP BY o.user_id, p.category
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) p ON cd.user_id = p.user_id
)
INSERT INTO target.user_metrics (
    user_id, email, phone, create_date, update_date, 
    status, batch_date, order_count, total_spent, preferred_category
)
SELECT * FROM enriched_data
WHERE batch_date = '20251231';
"""
    
    print(f"   ETL SQL大小: {len(etl_sql)/1024:.1f}KB")
    
    start_time = time.time()
    result = service.lint_sql(etl_sql)
    process_time = time.time() - start_time
    
    print(f"   处理时间: {process_time:.3f}秒")
    print(f"   发现问题: {len(result)}个")
    
    # 真实场景2: 报表SQL
    print(f"\n2. 报表SQL测试:")
    report_sql = """
-- 月度销售报表
SELECT 
    DATE_TRUNC('month', order_date) as report_month,
    p.category,
    COUNT(DISTINCT o.user_id) as unique_customers,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    MIN(o.total_amount) as min_order_value,
    MAX(o.total_amount) as max_order_value,
    SUM(CASE WHEN o.payment_method = 'credit_card' THEN o.total_amount ELSE 0 END) as credit_card_revenue,
    SUM(CASE WHEN o.payment_method = 'paypal' THEN o.total_amount ELSE 0 END) as paypal_revenue,
    SUM(CASE WHEN o.payment_method = 'bank_transfer' THEN o.total_amount ELSE 0 END) as bank_transfer_revenue,
    COUNT(DISTINCT CASE WHEN o.is_first_order THEN o.user_id END) as new_customers,
    COUNT(DISTINCT CASE WHEN o.order_date >= DATE_ADD('month', -1, CURRENT_DATE) THEN o.user_id END) as active_customers
FROM source.orders o
JOIN source.products p ON o.product_id = p.id
JOIN source.users u ON o.user_id = u.id
WHERE o.order_date >= '2024-01-01'
    AND o.order_date <= '2025-12-31'
    AND o.status = 'completed'
    AND u.status = 'active'
GROUP BY DATE_TRUNC('month', order_date), p.category
HAVING SUM(o.total_amount) > 0
ORDER BY report_month DESC, total_revenue DESC;
"""
    
    print(f"   报表SQL大小: {len(report_sql)/1024:.1f}KB")
    
    start_time = time.time()
    result = service.lint_sql(report_sql)
    process_time = time.time() - start_time
    
    print(f"   处理时间: {process_time:.3f}秒")
    print(f"   发现问题: {len(result)}个")
    
    # 真实场景3: 数据迁移SQL
    print(f"\n3. 数据迁移SQL测试:")
    migration_sql = """
-- 数据表迁移和重构
BEGIN TRANSACTION;

-- 创建新表结构
CREATE TABLE new_user_profiles (
    profile_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    display_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    website_url VARCHAR(500),
    location VARCHAR(255),
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_date DATE NOT NULL
);

CREATE TABLE new_user_settings (
    setting_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_key)
);

-- 迁移数据
INSERT INTO new_user_profiles (
    user_id, display_name, bio, avatar_url, website_url, 
    location, company, created_at, updated_at, batch_date
)
SELECT 
    u.id,
    COALESCE(up.display_name, u.username),
    up.bio,
    up.avatar_url,
    up.website_url,
    up.location,
    up.company,
    u.created_at,
    CURRENT_TIMESTAMP,
    '20251231'
FROM source.users u
LEFT JOIN source.user_profiles up ON u.id = up.user_id
WHERE u.status = 'active';

INSERT INTO new_user_settings (
    user_id, setting_key, setting_value, created_at, updated_at
)
SELECT 
    us.user_id,
    us.setting_key,
    us.setting_value,
    us.created_at,
    CURRENT_TIMESTAMP
FROM source.user_settings us
JOIN source.users u ON us.user_id = u.id
WHERE u.status = 'active';

-- 创建索引
CREATE INDEX idx_new_user_profiles_user_id ON new_user_profiles(user_id);
CREATE INDEX idx_new_user_profiles_batch_date ON new_user_profiles(batch_date);
CREATE INDEX idx_new_user_settings_user_id ON new_user_settings(user_id);
CREATE INDEX idx_new_user_settings_key ON new_user_settings(setting_key);

COMMIT;

-- 验证数据迁移
SELECT 
    (SELECT COUNT(*) FROM new_user_profiles) as profile_count,
    (SELECT COUNT(*) FROM new_user_settings) as setting_count,
    (SELECT COUNT(DISTINCT user_id) FROM new_user_profiles) as unique_users;
"""
    
    print(f"   迁移SQL大小: {len(migration_sql)/1024:.1f}KB")
    
    start_time = time.time()
    result = service.lint_sql(migration_sql)
    process_time = time.time() - start_time
    
    print(f"   处理时间: {process_time:.3f}秒")
    print(f"   发现问题: {len(result)}个")
    
    print(f"\n{'='*80}")
    print("真实场景测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    compare_performance()
    test_optimization_features()
    test_real_world_scenarios()