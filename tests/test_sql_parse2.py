#!/usr/bin/env python3
"""
使用项目实际配置测试SQL解析
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# 配置日志，只显示错误
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 设置sqlfluff日志级别为ERROR
logging.getLogger("sqlfluff").setLevel(logging.ERROR)

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig

def test_sql_parse_with_project_config():
    """使用项目实际配置测试SQL解析"""
    print("=" * 80)
    print("使用项目实际配置测试SQL解析")
    print("=" * 80)
    
    # 原始SQL（包含变量）
    original_sql = """
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
    
    print("1. 原始SQL（包含变量）:")
    print(original_sql[:200] + "..." if len(original_sql) > 200 else original_sql)
    print("-" * 80)
    
    # 手动替换变量（模拟预处理器）
    processed_sql = original_sql.replace("${batch_date}", "20251231").replace("${batch_yyyymm}", "202512")
    
    print("2. 处理后的SQL（变量替换为常量）:")
    print(processed_sql[:200] + "..." if len(processed_sql) > 200 else processed_sql)
    print("-" * 80)
    
    # 使用项目实际配置（Hive方言，只使用customer规则）
    config = FluffConfig(
        overrides={
            "dialect": "hive",
            "rules": "customer",  # 只使用自定义规则
            "max_line_length": 0,  # 禁用行长度检查
            "comma_style": "trailing",  # 简化逗号样式检查
            "indent_unit": "space",  # 简化缩进检查
            "tab_space_size": 4,
            "ignore": "",  # 不忽略任何语法
        }
    )
    
    print("3. 使用项目配置解析（Hive方言，只使用customer规则）...")
    linter = Linter(config=config)
    
    try:
        result = linter.lint_string(processed_sql)
        print("解析成功！")
        print(f"发现 {len(result.violations)} 个问题:")
        
        # 只显示前10个问题
        for i, violation in enumerate(result.violations[:10], 1):
            print(f"  {i}. [{violation.rule_code()}] 行{violation.line_no}: {violation.desc()}")
        
        if len(result.violations) > 10:
            print(f"  ... 还有{len(result.violations)-10}个问题未显示")
            
    except Exception as e:
        print(f"解析失败！错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 尝试获取更详细的错误信息
        import traceback
        print("\n完整错误堆栈:")
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_sql_parse_with_project_config()