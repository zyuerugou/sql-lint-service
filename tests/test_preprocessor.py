#!/usr/bin/env python3
"""
测试预处理器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from app.services.preprocessor_manager import PreprocessorManager
from pathlib import Path

def test_preprocessor():
    """测试预处理器"""
    print("=" * 80)
    print("测试预处理器")
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
    
    print("原始SQL:")
    print(sql)
    print(f"长度: {len(sql)} 字符")
    print("-" * 80)
    
    # 创建预处理器管理器
    preprocessors_dir = str(Path(__file__).parent / "app" / "rules" / "preprocessors")
    manager = PreprocessorManager(preprocessors_dir)
    
    print("预处理器信息:")
    for info in manager.get_preprocessors_info():
        print(f"  - {info['name']} (order={info['order']}): {info['description']}")
    print("-" * 80)
    
    # 处理SQL
    processed_sql = manager.process(sql)
    
    print("处理后的SQL:")
    print(processed_sql)
    print(f"长度: {len(processed_sql)} 字符")
    print("-" * 80)
    
    # 比较差异
    print("差异分析:")
    original_lines = sql.split('\n')
    processed_lines = processed_sql.split('\n')
    
    for i in range(min(len(original_lines), len(processed_lines))):
        if original_lines[i] != processed_lines[i]:
            print(f"行 {i+1}:")
            print(f"  原始: {repr(original_lines[i])}")
            print(f"  处理后: {repr(processed_lines[i])}")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_preprocessor()