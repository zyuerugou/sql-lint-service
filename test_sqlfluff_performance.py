#!/usr/bin/env python3
"""
测试sqlfluff处理大SQL的性能
"""

import sys
import time
import cProfile
import pstats
import io
import random
sys.path.insert(0, '.')

from app.services.lint_service import LintService


def generate_complex_sql(size_kb=100):
    """
    生成复杂的SQL用于测试
    
    Args:
        size_kb: 目标大小(KB)
    """
    print(f"生成 {size_kb}KB 复杂SQL...")
    
    target_size = size_kb * 1024
    sql_parts = []
    current_size = 0
    
    # 复杂SQL模板
    templates = [
        # 复杂SELECT
        """SELECT 
    t1.id,
    t1.name,
    t1.email,
    t2.order_id,
    t2.order_date,
    t2.total_amount,
    t3.product_name,
    t3.category,
    t4.shipping_address,
    t4.billing_address
FROM users t1
LEFT JOIN orders t2 ON t1.id = t2.user_id
INNER JOIN products t3 ON t2.product_id = t3.id
LEFT JOIN addresses t4 ON t1.id = t4.user_id
WHERE t1.status = 'active'
    AND t2.order_date >= '2024-01-01'
    AND t3.category IN ('electronics', 'books', 'clothing')
    AND (t4.country = 'US' OR t4.country = 'CA')
GROUP BY t1.id, t1.name, t1.email, t2.order_id, t2.order_date, 
         t2.total_amount, t3.product_name, t3.category,
         t4.shipping_address, t4.billing_address
HAVING COUNT(t2.order_id) > 0
ORDER BY t2.total_amount DESC, t1.name ASC
LIMIT 100;""",
        
        # 复杂INSERT
        """INSERT INTO analytics.daily_summary (
    summary_date,
    user_count,
    order_count,
    total_revenue,
    avg_order_value,
    top_product,
    top_category
)
SELECT 
    DATE('2025-12-31') as summary_date,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(o.id) as order_count,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as avg_order_value,
    (SELECT p.product_name FROM products p 
     WHERE p.id = (SELECT product_id FROM orders 
                   WHERE order_date = '2025-12-31' 
                   GROUP BY product_id 
                   ORDER BY COUNT(*) DESC 
                   LIMIT 1)) as top_product,
    (SELECT p.category FROM products p 
     WHERE p.id = (SELECT product_id FROM orders 
                   WHERE order_date = '2025-12-31' 
                   GROUP BY product_id 
                   ORDER BY COUNT(*) DESC 
                   LIMIT 1)) as top_category
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.order_date = '2025-12-31'
WHERE u.create_date <= '2025-12-31'
GROUP BY DATE('2025-12-31');""",
        
        # 复杂UPDATE
        """UPDATE user_metrics um
SET 
    last_active_date = '2025-12-31',
    total_orders = (SELECT COUNT(*) FROM orders o WHERE o.user_id = um.user_id),
    total_spent = (SELECT SUM(total_amount) FROM orders o WHERE o.user_id = um.user_id),
    avg_order_value = (SELECT AVG(total_amount) FROM orders o WHERE o.user_id = um.user_id),
    favorite_category = (
        SELECT p.category 
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.user_id = um.user_id 
        GROUP BY p.category 
        ORDER BY COUNT(*) DESC 
        LIMIT 1
    )
WHERE um.user_id IN (
    SELECT id FROM users 
    WHERE last_login_date >= '2025-01-01'
    AND status = 'active'
);""",
        
        # 复杂CREATE TABLE
        """CREATE TABLE IF NOT EXISTS data_warehouse.user_behavior_20251231 (
    user_id BIGINT NOT NULL,
    user_name VARCHAR(255),
    email VARCHAR(255),
    registration_date DATE,
    last_login_date TIMESTAMP,
    total_logins INT DEFAULT 0,
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0.00,
    avg_session_duration INT,
    favorite_device VARCHAR(50),
    preferred_category VARCHAR(100),
    churn_risk_score DECIMAL(5,2),
    engagement_score DECIMAL(5,2),
    lifetime_value DECIMAL(15,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_date DATE NOT NULL,
    PRIMARY KEY (user_id, batch_date),
    INDEX idx_email (email),
    INDEX idx_registration_date (registration_date),
    INDEX idx_last_login (last_login_date),
    INDEX idx_churn_risk (churn_risk_score),
    PARTITION BY RANGE (batch_date) (
        PARTITION p2025 VALUES LESS THAN ('2026-01-01'),
        PARTITION p2026 VALUES LESS THAN ('2027-01-01')
    )
) ENGINE=InnoDB 
ROW_FORMAT=COMPRESSED 
KEY_BLOCK_SIZE=8 
COMMENT='用户行为分析表 - 2025-12-31批次';"""
    ]
    
    while current_size < target_size:
        template = random.choice(templates)
        sql_parts.append(template)
        current_size += len(template) + 2  # +2 for newlines
        
        # 每10个语句打印进度
        if len(sql_parts) % 10 == 0:
            print(f"  已生成 {len(sql_parts)} 个语句，大小: {current_size / 1024:.1f}KB")
    
    result = "\n\n".join(sql_parts)
    print(f"生成完成: {len(result) / 1024:.1f}KB, {len(sql_parts)} 个语句")
    return result


def test_sqlfluff_performance():
    """测试sqlfluff性能"""
    print("测试sqlfluff处理大SQL性能")
    print("=" * 60)
    
    # 创建LintService（禁用热加载以减少开销）
    print("初始化LintService...")
    start_time = time.time()
    lint_service = LintService(enable_hot_reload=False)
    init_time = time.time() - start_time
    print(f"初始化时间: {init_time:.3f}秒")
    
    # 测试不同大小的SQL
    test_sizes = [10, 50, 100, 200, 500]  # KB
    
    for size_kb in test_sizes:
        print(f"\n{'='*40}")
        print(f"测试 {size_kb}KB SQL:")
        
        # 生成SQL
        sql = generate_complex_sql(size_kb=size_kb)
        
        # 测试1: 仅预处理器
        print(f"\n1. 仅预处理器处理:")
        start_time = time.time()
        processed_sql = lint_service.preprocessor_manager.process(sql)
        preprocess_time = time.time() - start_time
        print(f"   处理时间: {preprocess_time:.3f}秒")
        print(f"   处理速度: {size_kb / preprocess_time:.1f}KB/秒")
        
        # 测试2: sqlfluff lint
        print(f"\n2. sqlfluff lint处理:")
        start_time = time.time()
        try:
            result = lint_service.lint_sql(sql)
            lint_time = time.time() - start_time
            
            print(f"   处理时间: {lint_time:.3f}秒")
            print(f"   处理速度: {size_kb / lint_time:.1f}KB/秒")
            print(f"   发现问题: {len(result)} 个")
            
            # 分析时间分布
            sqlfluff_time = lint_time - preprocess_time
            print(f"   sqlfluff实际时间: {sqlfluff_time:.3f}秒 ({sqlfluff_time/lint_time*100:.1f}%)")
            print(f"   预处理器时间: {preprocess_time:.3f}秒 ({preprocess_time/lint_time*100:.1f}%)")
            
            if lint_time > 5:
                print(f"   [WARNING] 超过5秒超时限制!")
            else:
                print(f"   [OK] 在5秒内完成")
                
        except Exception as e:
            print(f"   [ERROR] sqlfluff处理失败: {e}")
            lint_time = 999  # 标记为失败
        
        # 测试3: 内存使用
        print(f"\n3. 内存使用情况:")
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   当前内存使用: {memory_mb:.1f}MB")
        
        # 清理
        del sql
        del processed_sql
        if 'result' in locals():
            del result
        
        # 强制垃圾回收
        import gc
        gc.collect()
    
    print(f"\n{'='*60}")
    print("性能测试总结")
    print("=" * 60)
    
    print(f"sqlfluff初始化时间: {init_time:.3f}秒")
    print(f"注意: sqlfluff处理复杂SQL可能较慢，特别是:")
    print("  - 包含嵌套子查询")
    print("  - 多表JOIN")
    print("  - 复杂WHERE条件")
    print("  - 大量聚合函数")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


def profile_sqlfluff():
    """性能分析sqlfluff"""
    print("\n\n性能分析sqlfluff")
    print("=" * 60)
    
    # 创建LintService
    lint_service = LintService(enable_hot_reload=False)
    
    # 生成中等大小SQL
    sql = generate_complex_sql(size_kb=50)
    print(f"测试SQL大小: {len(sql) / 1024:.1f}KB")
    
    # 性能分析
    print("\n开始性能分析...")
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        result = lint_service.lint_sql(sql)
        print(f"发现问题: {len(result)} 个")
    except Exception as e:
        print(f"处理失败: {e}")
    
    profiler.disable()
    
    # 输出分析结果
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # 显示前20个最耗时的函数
    
    print("\n性能分析结果 (前20个最耗时函数):")
    print("=" * 60)
    print(s.getvalue())
    
    print("=" * 60)
    print("性能分析完成!")
    print("=" * 60)


def test_optimization_ideas():
    """测试优化想法"""
    print("\n\nsqlfluff优化建议测试")
    print("=" * 60)
    
    print("1. 问题分析:")
    print("   sqlfluff性能瓶颈可能包括:")
    print("   - SQL解析 (sqlfluff.core.parser)")
    print("   - 规则检查 (每个规则独立运行)")
    print("   - 结果格式化")
    print("   - 内存分配")
    
    print("\n2. 优化建议:")
    print("   a) 禁用不必要的规则")
    print("   b) 简化SQLFluff配置")
    print("   c) 缓存解析结果")
    print("   d) 异步处理")
    print("   e) 超时机制")
    print("   f) 采样检查 (对于超大SQL)")
    
    print("\n3. 测试简化配置:")
    from sqlfluff.core import Linter
    from sqlfluff.core.config import FluffConfig
    
    # 测试最小配置
    print("\n测试最小化配置...")
    minimal_config = FluffConfig(
        overrides={
            "dialect": "ansi",  # 最简单的方言
            "rules": "",  # 空规则，只做语法检查
            "max_line_length": 0,  # 禁用行长度检查
        }
    )
    
    # 生成测试SQL
    test_sql = "SELECT id, name FROM users WHERE status = 'active';"
    
    # 原始配置
    original_config = FluffConfig(
        overrides={
            "dialect": "hive",
            "rules": "customer"
        }
    )
    
    # 测试两种配置的性能
    print("测试原始配置...")
    start_time = time.time()
    linter_original = Linter(config=original_config)
    result_original = linter_original.lint_string(test_sql)
    original_time = time.time() - start_time
    
    print("测试最小配置...")
    start_time = time.time()
    linter_minimal = Linter(config=minimal_config)
    result_minimal = linter_minimal.lint_string(test_sql)
    minimal_time = time.time() - start_time
    
    print(f"\n性能对比:")
    print(f"  原始配置: {original_time:.3f}秒, 问题: {len(result_original.violations)}")
    print(f"  最小配置: {minimal_time:.3f}秒, 问题: {len(result_minimal.violations)}")
    print(f"  速度提升: {original_time/minimal_time:.1f}x")
    
    print("\n4. 规则性能测试:")
    print("   测试每个规则的性能影响...")
    
    # 获取所有规则
    from sqlfluff.core.rules import get_ruleset
    ruleset = get_ruleset()
    
    # 测试几个常见规则
    test_rules = ["L001", "L003", "L004", "L010", "L014"]
    
    for rule_code in test_rules:
        rule_config = FluffConfig(
            overrides={
                "dialect": "ansi",
                "rules": rule_code
            }
        )
        
        start_time = time.time()
        linter_rule = Linter(config=rule_config)
        result_rule = linter_rule.lint_string(test_sql * 100)  # 放大SQL
        rule_time = time.time() - start_time
        
        print(f"  规则 {rule_code}: {rule_time:.3f}秒, 问题: {len(result_rule.violations)}")
    
    print("\n" + "=" * 60)
    print("优化建议测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_sqlfluff_performance()
    profile_sqlfluff()
    test_optimization_ideas()