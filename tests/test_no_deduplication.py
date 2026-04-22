#!/usr/bin/env python3
# coding=utf-8
"""
测试没有去重逻辑的情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlglot
from app.rules.rule_ss02_sqlglot import RuleSs02Sqlglot


def test_no_deduplication():
    """测试没有去重逻辑的情况"""
    # 创建没有去重逻辑的规则
    class NoDedupRuleSs02Sqlglot(RuleSs02Sqlglot):
        """没有去重逻辑的SS02规则"""
        
        def check(self, ast, sql: str = ""):
            # 复制逻辑，但去掉去重
            import re
            from app.rules.sqlglot_base import Violation
            
            violations = []
            
            if not ast or not sql:
                return violations
            
            # 将SQL按行分割
            lines = sql.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # 查找小写关键字
                for match in re.finditer(r'\b([a-z][a-z_]+)\b', line):
                    word = match.group(1).lower()
                    
                    # 检查是否是SQL关键字
                    if word in self.SQL_KEYWORDS:
                        violations.append(Violation(
                            rule_id=self.code,
                            message=f"{self.description} 发现小写关键字: {word}",
                            line=line_num,
                            column=match.start() + 1,
                            severity="error"
                        ))
            
            return violations
    
    # 测试SQL
    test_sql = """SELECT * FROM users -- id in ('ncp', 'nad')"""
    
    print("测试没有去重逻辑的SS02规则:")
    print(f"SQL: {test_sql}")
    print()
    
    rule = NoDedupRuleSs02Sqlglot()
    
    # 解析SQL
    ast = sqlglot.parse_one(test_sql, read="hive")
    
    # 检查规则
    violations = rule.check(ast, test_sql)
    
    print(f"发现 {len(violations)} 个违规")
    for i, v in enumerate(violations, 1):
        print(f"  违规 {i}: 行{v.line}, 列{v.column}, 消息: {v.message}")
    
    # 分析正则表达式匹配
    print(f"\n分析正则表达式匹配:")
    import re
    lines = test_sql.split('\n')
    for line_num, line in enumerate(lines, 1):
        print(f"行 {line_num}: '{line}'")
        matches = list(re.finditer(r'\b([a-z][a-z_]+)\b', line))
        print(f"  匹配到 {len(matches)} 个小写单词:")
        for match in matches:
            word = match.group(1).lower()
            if word in rule.SQL_KEYWORDS:
                print(f"    '{match.group(1)}' (位置: {match.start()}) -> SQL关键字")
            else:
                print(f"    '{match.group(1)}' (位置: {match.start()}) -> 非关键字")
    
    return len(violations)


if __name__ == "__main__":
    violation_count = test_no_deduplication()
    print(f"\n结论: 没有去重逻辑时发现 {violation_count} 个违规")