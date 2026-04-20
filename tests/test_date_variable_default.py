# coding=utf-8
"""
测试日期变量预处理器的默认batch_date值
"""

import pytest
from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor


class TestDateVariableDefault:
    """测试日期变量默认值"""
    
    def test_default_batch_date(self):
        """测试默认batch_date值为20251231"""
        preprocessor = DateVariablePreprocessor()
        
        # 测试默认变量映射
        assert preprocessor.default_variables["batch_date"] == "20251231"
        assert preprocessor.default_variables["batch_yyyymm"] == "202512"
        assert preprocessor.default_variables["next_date"] == "20260101"
        assert preprocessor.default_variables["last_date"] == "20251230"
        
        # 测试周相关变量
        assert preprocessor.default_variables["week_start"] == "20251229"
        assert preprocessor.default_variables["week_end"] == "20260104"
        
        # 测试月相关变量
        assert preprocessor.default_variables["month_start"] == "20251201"
        assert preprocessor.default_variables["month_end"] == "20251231"
        
        # 测试年相关变量
        assert preprocessor.default_variables["year_start"] == "20250101"
        assert preprocessor.default_variables["year_end"] == "20251231"
        
        # 测试时间戳相关变量
        assert preprocessor.default_variables["batch_timestamp"] == "2025-12-31 00:00:00.000000"
        assert preprocessor.default_variables["batch_timestamp_with_t"] == "2025-12-31T00:00:00.000000"
    
    def test_process_without_context(self):
        """测试没有上下文时的变量替换"""
        preprocessor = DateVariablePreprocessor()
        
        # 测试SQL中的日期变量替换
        sql = """
        SELECT * FROM users 
        WHERE create_date = '${batch_date}'
        AND update_date = '${batch_yyyymm}'
        AND status = '${unknown_var}'
        """
        
        result = preprocessor.process(sql)
        
        # 检查batch_date被替换为20251231
        assert "20251231" in result
        assert "${batch_date}" not in result
        
        # 检查batch_yyyymm被替换为202512
        assert "202512" in result
        assert "${batch_yyyymm}" not in result
        
        # 检查未知变量被替换为DEFAULT_VALUE
        assert "DEFAULT_VALUE" in result
        assert "${unknown_var}" not in result
    
    def test_process_ignores_context(self):
        """测试预处理器忽略上下文参数"""
        preprocessor = DateVariablePreprocessor()
        
        # 使用不同的batch_date测试
        sql = "SELECT * FROM table WHERE date = '${batch_date}' AND month = '${batch_yyyymm}'"
        
        # 即使提供了context，也应该使用默认值
        context = {"batch_date": "20250101"}
        result = preprocessor.process(sql, context)
        
        # 应该使用默认值，而不是上下文中的值
        assert "20251231" in result  # 默认值应该出现
        assert "20250101" not in result  # 上下文值不应该出现
        assert "202512" in result  # batch_yyyymm应该基于默认值计算
        
        # 检查变量被正确替换
        assert "${batch_date}" not in result
        assert "${batch_yyyymm}" not in result
    
    def test_useful_date_variables_list(self):
        """测试get_useful_date变量列表"""
        preprocessor = DateVariablePreprocessor()
        
        # 检查列表包含所有41个变量
        assert len(preprocessor.useful_date_variables) == 41
        
        # 检查一些关键变量是否在列表中
        assert "batch_date" in preprocessor.useful_date_variables
        assert "batch_yyyymm" in preprocessor.useful_date_variables
        assert "next_date" in preprocessor.useful_date_variables
        assert "last_date" in preprocessor.useful_date_variables
        assert "week_start" in preprocessor.useful_date_variables
        assert "month_start" in preprocessor.useful_date_variables
        assert "quarter_start" in preprocessor.useful_date_variables
        assert "year_start" in preprocessor.useful_date_variables
        
        # 检查所有默认变量都在useful_date_variables列表中
        for var_name in preprocessor.default_variables.keys():
            assert var_name in preprocessor.useful_date_variables, f"{var_name}不在useful_date_variables列表中"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])