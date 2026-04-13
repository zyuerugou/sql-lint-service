#!/usr/bin/env python3
# coding=utf-8
"""
SS03规则测试 - 表名和字段名应当为小写（双引号内的内容除外）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from app.services.lint_service import LintService

def test_rule_ss03():
    """测试SS03规则：表名和字段名应当为小写（双引号内的内容除外）"""
    print("=" * 60)
    print("SS03规则测试 - 表名和字段名应当为小写（双引号内的内容除外）")
    print("=" * 60)
    
    # 创建LintService实例
    service = LintService(enable_hot_reload=False)
    
    # 测试用例
    test_cases = [
        {
            "sql": "SELECT id, name FROM users",
            "description": "不应该触发SS03规则（所有标识符都是小写）",
            "expected_rule": "SS03",
            "should_trigger": False
        },
        {
            "sql": "SELECT UserID, FullName FROM UserTable",
            "description": "应该触发SS03规则（标识符包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "SELECT id AS UserID FROM users",
            "description": "应该触发SS03规则（别名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "SELECT id AS user_id FROM users",
            "description": "不应该触发SS03规则（别名是小写）",
            "expected_rule": "SS03",
            "should_trigger": False
        },
        {
            "sql": "SELECT id, name FROM users WHERE status = 'ACTIVE'",
            "description": "不应该触发SS03规则（字符串值不检查）",
            "expected_rule": "SS03",
            "should_trigger": False
        },
        {
            "sql": "SELECT COUNT(*) AS TotalCount FROM users",
            "description": "应该触发SS03规则（别名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "INSERT INTO UserTable (UserID, FullName) VALUES (1, 'John Doe')",
            "description": "应该触发SS03规则（表名和字段名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "UPDATE UserTable SET FullName = 'Jane Doe' WHERE UserID = 1",
            "description": "应该触发SS03规则（表名和字段名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "DELETE FROM UserTable WHERE UserID = 1",
            "description": "应该触发SS03规则（表名和字段名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "SELECT 123 AS Number, true AS Flag FROM users",
            "description": "应该触发SS03规则（别名包含大写字母）",
            "expected_rule": "SS03",
            "should_trigger": True
        },
        {
            "sql": "SELECT `TableName`, `ColumnName` FROM `Database`.`Schema`.`Table`",
            "description": "不应该触发SS03规则（反引号标识符保持原样）",
            "expected_rule": "SS03",
            "should_trigger": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['description']}")
        print(f"SQL: {test_case['sql']}")
        
        result = service.lint_sql(test_case['sql'])
        
        # 检查是否触发了SS03规则
        has_rule = any(item['rule_id'] == 'SS03' for item in result)
        
        if has_rule == test_case['should_trigger']:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"触发SS03: {'是' if has_rule else '否'}")
        print(f"预期触发: {'是' if test_case['should_trigger'] else '否'}")
        print(f"[{status}] {'符合预期' if status == 'PASS' else '不符合预期'}")
        
        # 显示详细结果
        if result:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == 'SS03':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}，失败 {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("[PASS] 所有SS03规则测试通过")
        return True
    else:
        print("[FAIL] 部分SS03规则测试失败")
        return False

def test_rule_ss03_edge_cases():
    """测试SS03规则边界情况"""
    print("\n" + "=" * 60)
    print("SS03规则边界情况测试")
    print("=" * 60)
    
    service = LintService(enable_hot_reload=False)
    
    edge_cases = [
        {
            "sql": "SELECT MAX(salary) AS MaxSalary FROM employees",
            "description": "函数名和别名（函数名可能被识别为标识符）"
        },
        {
            "sql": "SELECT * FROM public.UserTable",
            "description": "带schema的表名（schema.table格式）"
        },
        {
            "sql": "SELECT column1, column2 FROM table1 JOIN table2 ON table1.id = table2.id",
            "description": "JOIN语句中的表名和字段名"
        },
        {
            "sql": "SELECT UPPER(name) AS NameUpper FROM users",
            "description": "函数调用中的参数"
        },
        {
            "sql": "SELECT 1.23 AS DecimalValue, -100 AS NegativeValue FROM dual",
            "description": "带符号的数字"
        }
    ]
    
    for case in edge_cases:
        print(f"\n边界测试: {case['description']}")
        print(f"SQL: {case['sql']}")
        
        result = service.lint_sql(case['sql'])
        has_rule = any(item['rule_id'] == 'SS03' for item in result)
        
        print(f"触发SS03: {'是' if has_rule else '否'}")
        
        if has_rule:
            print("详细结果:")
            for item in result:
                if item['rule_id'] == 'SS03':
                    print(f"  - {item['rule_id']}: {item['message']}")
    
    print("\n" + "=" * 60)
    print("SS03规则边界情况测试完成")

if __name__ == "__main__":
    # 运行SS03规则测试
    success = test_rule_ss03()
    
    # 运行边界情况测试
    test_rule_ss03_edge_cases()
    
    # 返回退出码
    sys.exit(0 if success else 1)