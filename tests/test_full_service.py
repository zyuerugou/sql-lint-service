#!/usr/bin/env python3
"""
使用完整的LintService测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置日志，显示INFO级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 设置sqlfluff日志级别为WARNING
logging.getLogger("sqlfluff").setLevel(logging.WARNING)

from app.services.lint_service import LintService

def test_full_service():
    """使用完整的LintService测试"""
    print("=" * 80)
    print("使用完整的LintService测试")
    print("=" * 80)
    
    # 测试SQL
    sql = """
INSERT INTO a(id, name, bal, avg) 
SELECT 
  CAST(a.id AS VARCHAR(50)),
  CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200)), 
  CAST(NVL(a.bal, 0) AS DECIMAL(30,6)), 
  CAST(a.accum_bal /  x.days AS DECIMAL(30,6)) 
FROM 
  (SELECT * FROM a WHERE 1=1 AND a.part_ymd='${batch_date}' AND a.cust_typ=1) a 
  INNER JOIN (  
    SELECT id, min(name) FROM b WHERE start_dt <= '${batch_date}' AND end_dt > '${batch_date}' AND part_ym >= '${batch_yyyymm}'     
    and trim(id) <> '' GROUP BY id) b 
    ON 1=1 AND a.id = b.id AND b.id LIKE 'p%' 
  LEFT JOIN e ON a.id = e.id 
  LEFT JOIN x ON 1=1   AND x.curr_dt = '${batch_date}';
"""
    
    print("测试SQL长度:", len(sql), "字符")
    print("-" * 80)
    
    # 创建服务实例（禁用采样，避免干扰）
    service = LintService(
        enable_hot_reload=False,
        timeout_seconds=10,
        max_sql_size_mb=10,
        enable_sampling=False,  # 禁用采样
        cache_size=0  # 禁用缓存
    )
    
    print("开始检查SQL...")
    try:
        result = service.lint_sql(sql)
        print(f"检查完成，发现 {len(result)} 个问题:")
        
        for i, violation in enumerate(result, 1):
            print(f"  {i}. [{violation.get('rule_id')}] 行{violation.get('line')}: {violation.get('message')}")
            
    except Exception as e:
        print(f"检查失败！错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        import traceback
        print("\n完整错误堆栈:")
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_full_service()