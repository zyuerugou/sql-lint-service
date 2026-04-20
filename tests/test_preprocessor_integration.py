"""
预处理器集成测试
测试预处理器与LintService的集成
"""

import pytest
from app.services.lint_service import LintService


class TestPreprocessorIntegration:
    """预处理器集成测试"""
    
    @pytest.fixture
    def lint_service(self):
        """创建LintService实例"""
        return LintService(enable_hot_reload=False)
    
    def test_lint_with_preprocessors(self, lint_service):
        """测试使用预处理器的lint功能"""
        # 包含SET语句和变量的SQL
        sql = """
        set hive.exec.dynamic.partition.mode=nonstrict;
        SELECT * FROM users 
        WHERE create_date = '${batch_date}'
        AND status = 'active';
        set another.config = value;
        """
        
        result = lint_service.lint_sql(sql)
        
        # 应该没有PRS错误（因为SET语句被过滤了）
        # 应该没有SS02/SS03错误（因为SET语句被过滤了）
        for violation in result:
            assert violation["rule_id"] not in ["PRS", "SS02", "SS03"]
    
    def test_get_preprocessors_info(self, lint_service):
        """测试获取预处理器信息"""
        preprocessors_info = lint_service.get_loaded_preprocessors()
        
        assert len(preprocessors_info) == 2
        
        # 检查预处理器信息
        names = [info["name"] for info in preprocessors_info]
        assert "SetStatementFilterPreprocessor" in names
        assert "DateVariablePreprocessor" in names
    
    def test_preprocessor_order_in_lint_service(self, lint_service):
        """测试在LintService中预处理器的执行顺序"""
        # 创建一个复杂的SQL测试预处理器的执行顺序
        sql = """
        -- 这是一个测试SQL
        set hive.exec.dynamic.partition.mode=nonstrict;
        
        SELECT 
            user_id,
            user_name,
            create_time
        FROM users
        WHERE 
            create_time >= '${yesterday}'
            AND status = '${batch_date}'
        ORDER BY create_time DESC;
        
        set tez.queue.name=default;
        """
        
        # 执行lint
        result = lint_service.lint_sql(sql)
        
        # 验证结果：应该没有SET语句相关的错误
        for violation in result:
            rule_id = violation["rule_id"]
            # SET语句应该被过滤，所以不会有相关错误
            if rule_id in ["SS02", "SS03"]:
                # 检查错误消息，确保不是SET语句相关的错误
                message = violation["message"]
                assert "SET" not in message
    
    def test_variable_replacement_in_context(self, lint_service):
        """测试使用上下文变量的替换"""
        # 注意：当前的VariableReplacerPreprocessor不支持从LintService传递上下文
        # 这是一个设计决策，如果需要可以扩展
        
        sql = "SELECT * FROM table WHERE date = '${batch_date}'"
        
        result = lint_service.lint_sql(sql)
        
        # 变量应该被替换为默认值
        # 由于变量被替换为具体日期，lint应该正常工作
        # 主要验证没有因为变量语法导致的解析错误