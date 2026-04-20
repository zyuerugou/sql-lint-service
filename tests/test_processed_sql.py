#!/usr/bin/env python3
"""
测试预处理后的SQL解析
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

def test_processed_sql():
    """测试预处理后的SQL"""
    print("=" * 80)
    print("测试预处理后的SQL解析")
    print("=" * 80)
    
    # 预处理后的SQL（从上一个测试中复制）
    processed_sql = """
INSERT INTO a(id, name, bal, avg)
SELECT
CAST(a.id AS VARCHAR(50)),
CAST(CASE WHEN a.name='' OR a.name IS NULL THEN b.name ELSE a.name END AS VARCHAR(200)),
CAST(NVL(a.bal, 0) AS DECIMAL(30,6)),
CAST(a.accum_bal /  x.days AS DECIMAL(30,6))
FROM
(SELECT * FROM a WHERE 1=1 AND a.part_ymd='20251231' AND a.cust_typ=1) a
INNER JOIN (
SELECT id, min(name) FROM b WHERE start_dt <= '20251231' AND end_dt > '20251231' AND part_ym >= '202512'
and trim(id) <> '' GROUP BY id) b
ON 1=1 AND a.id = b.id AND b.id LIKE 'p%'
LEFT JOIN e ON a.id = e.id
LEFT JOIN x ON 1=1   AND x.curr_dt = '20251231';
"""
    
    print("预处理后的SQL:")
    print(processed_sql)
    print(f"长度: {len(processed_sql)} 字符")
    print("-" * 80)
    
    # 使用项目实际配置
    config = FluffConfig(
        overrides={
            "dialect": "hive",
            "rules": "customer",  # 只使用自定义规则
            "max_line_length": 0,
            "comma_style": "trailing",
            "indent_unit": "space",
            "tab_space_size": 4,
            "ignore": "",
        }
    )
    
    print("使用sqlfluff解析...")
    linter = Linter(config=config)
    
    try:
        result = linter.lint_string(processed_sql)
        print("解析成功！")
        print(f"发现 {len(result.violations)} 个问题:")
        
        for i, violation in enumerate(result.violations, 1):
            print(f"  {i}. [{violation.rule_code()}] 行{violation.line_no}: {violation.desc()}")
            
    except Exception as e:
        print(f"解析失败！错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        import traceback
        print("\n完整错误堆栈:")
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_processed_sql()