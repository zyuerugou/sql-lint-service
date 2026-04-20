#!/usr/bin/env python3
"""
测试StopIteration问题
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

from sqlfluff.core import Linter
from sqlfluff.core.config import FluffConfig

def test_violations_type():
    """测试violations的类型"""
    print("=" * 80)
    print("测试violations的类型")
    print("=" * 80)
    
    # 预处理后的SQL
    sql = """
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
    
    # 使用项目配置
    config = FluffConfig(
        overrides={
            "dialect": "hive",
            "rules": "customer",
            "max_line_length": 0,
            "comma_style": "trailing",
            "indent_unit": "space",
            "tab_space_size": 4,
            "ignore": "",
        }
    )
    
    linter = Linter(config=config)
    result = linter.lint_string(sql)
    
    print(f"result类型: {type(result)}")
    print(f"result.violations类型: {type(result.violations)}")
    print(f"result.violations长度: {len(result.violations)}")
    
    # 测试迭代
    print("\n测试迭代result.violations:")
    try:
        count = 0
        for violation in result.violations:
            count += 1
            print(f"  {count}. [{violation.rule_code()}]")
        
        print(f"成功迭代了 {count} 个violations")
        
    except StopIteration as e:
        print(f"捕获到StopIteration异常: {e}")
    except Exception as e:
        print(f"捕获到其他异常: {type(e).__name__}: {e}")
    
    # 转换为列表测试
    print("\n测试转换为列表:")
    try:
        violations_list = list(result.violations)
        print(f"成功转换为列表，长度: {len(violations_list)}")
    except Exception as e:
        print(f"转换失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

if __name__ == "__main__":
    test_violations_type()