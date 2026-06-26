#!/usr/bin/env python3
"""
SQL lint 服务性能测试合集
"""

import sys
import time
import random
sys.path.insert(0, '..')

from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor
from app.rules.preprocessors.set_statement_filter_preprocessor import SetStatementFilterPreprocessor
from app.services.preprocessor_manager import PreprocessorManager
from app.services.lint_service import LintService


def generate_large_sql(num_statements=1000, max_columns=50):
    tables = ["users", "orders", "products", "customers", "transactions", "logs", "events"]
    columns = ["id", "name", "email", "phone", "address", "city", "state", "country",
               "created_at", "updated_at", "status", "type", "category", "price", "quantity",
               "amount", "total", "discount", "tax", "shipping", "batch_date", "batch_yyyymm"]

    sql_parts = []
    for i in range(num_statements):
        stmt_type = random.choice(["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"])

        if stmt_type == "SELECT":
            table = random.choice(tables)
            num_select_cols = random.randint(1, max_columns)
            select_cols = random.sample(columns, min(num_select_cols, len(columns)))
            where_conditions = []
            if random.random() > 0.3:
                num_conditions = random.randint(1, 5)
                for _ in range(num_conditions):
                    col = random.choice(columns[:10])
                    if col == "batch_date":
                        where_conditions.append(f"{col} = '20251231'")
                    else:
                        where_conditions.append(f"{col} = '{random.choice(['active', 'pending', 'completed'])}'")
            select_stmt = f"SELECT {', '.join(select_cols)} FROM {table}"
            if where_conditions:
                select_stmt += f" WHERE {' AND '.join(where_conditions)}"
            select_stmt += ";"
            sql_parts.append(select_stmt)
        elif stmt_type == "INSERT":
            table = random.choice(tables)
            num_insert_cols = random.randint(1, 10)
            insert_cols = random.sample(columns, min(num_insert_cols, len(columns)))
            values = []
            for _ in range(random.randint(1, 3)):
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
            table = random.choice(tables)
            drop_stmt = f"DROP TABLE IF EXISTS {table};"
            sql_parts.append(drop_stmt)

    for i in range(min(100, num_statements // 10)):
        sql_parts.append(f"SELECT * FROM table_{i} WHERE date_column = '20251231';")
        sql_parts.append(f"INSERT INTO logs_{i} (log_date, message) VALUES ('20251231', 'Test message');")

    return "\n".join(sql_parts)


def generate_complex_sql(size_kb=100):
    target_size = size_kb * 1024
    sql_parts = []
    current_size = 0

    templates = [
        """SELECT t1.id, t1.name, t1.email, t2.order_id, t2.order_date, t2.total_amount,
    t3.product_name, t3.category, t4.shipping_address, t4.billing_address
FROM users t1
LEFT JOIN orders t2 ON t1.id = t2.user_id
INNER JOIN products t3 ON t2.product_id = t3.id
LEFT JOIN addresses t4 ON t1.id = t4.user_id
WHERE t1.status = 'active' AND t2.order_date >= '2024-01-01'
    AND t3.category IN ('electronics', 'books', 'clothing')
    AND (t4.country = 'US' OR t4.country = 'CA')
GROUP BY t1.id, t1.name, t2.order_id, t2.total_amount, t3.product_name, t3.category
HAVING COUNT(t2.order_id) > 0
ORDER BY t2.total_amount DESC, t1.name ASC LIMIT 100;""",
        """INSERT INTO daily_summary (summary_date, user_count, order_count, total_revenue)
SELECT DATE('2025-12-31'), COUNT(DISTINCT u.id), COUNT(o.id), SUM(o.total_amount)
FROM users u LEFT JOIN orders o ON u.id = o.user_id AND o.order_date = '2025-12-31'
WHERE u.create_date <= '2025-12-31';""",
        """UPDATE user_metrics um
SET last_active_date = '2025-12-31',
    total_orders = (SELECT COUNT(*) FROM orders o WHERE o.user_id = um.user_id),
    total_spent = (SELECT SUM(total_amount) FROM orders o WHERE o.user_id = um.user_id)
WHERE um.user_id IN (SELECT id FROM users WHERE last_login_date >= '2025-01-01' AND status = 'active');""",
    ]

    while current_size < target_size:
        template = random.choice(templates)
        sql_parts.append(template)
        current_size += len(template) + 2

    return "\n\n".join(sql_parts)


def test_preprocessor_performance():
    print("预处理器性能测试")
    print("=" * 60)

    date_preprocessor = DateVariablePreprocessor()
    set_preprocessor = SetStatementFilterPreprocessor()

    for name, sql, desc in [
        ("中等大小SQL (100语句)", generate_large_sql(num_statements=100, max_columns=20), "100语句"),
        ("大型SQL (1000语句)", generate_large_sql(num_statements=1000, max_columns=30), "1000语句"),
        ("超长单行SQL (10K字符)", "SELECT " + ", ".join([f"col_{i}" for i in range(500)]) + " FROM t WHERE " + " AND ".join([f"c_{i}='v'" for i in range(100)]) + ";", "单行"),
        ("极端情况 (10000语句)", generate_large_sql(num_statements=10000, max_columns=10), "10000语句"),
    ]:
        print(f"\n{name}:")
        print(f"  大小: {len(sql):,} 字符")

        for pname, pre in [("DateVariablePreprocessor", date_preprocessor), ("SetStatementFilterPreprocessor", set_preprocessor)]:
            start = time.time()
            pre.process(sql[:10000] if "极端" in name and id(pre) == id(date_preprocessor) else sql)
            elapsed = time.time() - start
            print(f"  {pname}: {elapsed:.3f}秒")

    print("\nPreprocessorManager 中等SQL:")
    from pathlib import Path
    manager = PreprocessorManager(str(Path(__file__).parent / "app" / "rules" / "preprocessors"))
    medium_sql = generate_large_sql(num_statements=100, max_columns=20)
    start = time.time()
    manager.process(medium_sql)
    print(f"  处理时间: {time.time() - start:.3f}秒")


def test_lint_performance():
    print("\nLintService 性能测试")
    print("=" * 60)

    service = LintService(enable_hot_reload=False)

    for name, sql in [
        ("小SQL (简单查询)", "SELECT id, name FROM users WHERE status = 'active';"),
        ("复杂SQL (100KB)", generate_complex_sql(size_kb=100)),
    ]:
        print(f"\n{name}:")
        start = time.time()
        result = service.lint_sql(sql)
        elapsed = time.time() - start
        print(f"  SQL大小: {len(sql)/1024:.1f}KB" if len(sql) > 1000 else f"  SQL大小: {len(sql)} 字符")
        print(f"  处理时间: {elapsed:.3f}秒, 问题: {len(result)} 个")


def test_cache_and_sampling():
    print("\n缓存 & 采样测试")
    print("=" * 60)

    service = LintService(enable_hot_reload=False, cache_size=10, enable_sampling=True, sampling_threshold_kb=50)

    sql = "SELECT id, name FROM users WHERE status = 'active';"
    start = time.time()
    service.lint_sql(sql)
    t1 = time.time() - start
    start = time.time()
    service.lint_sql(sql)
    t2 = time.time() - start
    print(f"  首次: {t1:.3f}秒, 缓存命中: {t2:.3f}秒" + (f" ({t1/t2:.0f}x 加速)" if t2 > 0 else ""))

    large_sql = generate_large_sql(num_statements=200)
    print(f"\n  采样测试 ({len(large_sql)/1024:.0f}KB):")
    start = time.time()
    result = service.lint_sql(large_sql)
    print(f"  处理时间: {time.time() - start:.3f}秒, 问题: {len(result)} 个")


def test_timeout_protection():
    print("\n超时保护测试")
    print("=" * 60)

    service = LintService(enable_hot_reload=False, timeout_seconds=1, max_sql_size_mb=5, enable_sampling=False)
    complex_sql = "\n".join([
        f"SELECT t1.*, t2.* FROM t1 CROSS JOIN t2 WHERE t1.id = t2.ref_id AND t1.create_date >= '2024-01-01' AND t2.update_date <= '2025-12-31';"
    ]) * 100

    print(f"  SQL大小: {len(complex_sql)/1024:.1f}KB")
    start = time.time()
    result = service.lint_sql(complex_sql)
    elapsed = time.time() - start
    print(f"  处理时间: {elapsed:.3f}秒, 结果: {len(result)} 个")
    if result and result[0].get("rule_id") == "TIMEOUT":
        print("  [TIMEOUT] 超时触发!")
    else:
        print("  [OK] 在超时内完成")


if __name__ == "__main__":
    test_preprocessor_performance()
    test_lint_performance()
    test_cache_and_sampling()
    test_timeout_protection()
