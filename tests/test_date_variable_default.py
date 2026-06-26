# coding=utf-8
"""
测试日期变量预处理器的默认batch_date值
"""

import pytest
from app.rules.preprocessors.date_variable_preprocessor import DateVariablePreprocessor


class TestDateVariableDefault:
    """测试日期变量默认值"""
    
    def test_default_batch_date(self):
        """测试默认变量使用占位符"""
        preprocessor = DateVariablePreprocessor()
        
        assert preprocessor.default_variables["batch_date"] == "_v_batch_date_"
        assert preprocessor.default_variables["batch_yyyymm"] == "_v_batch_yyyymm_"
        assert preprocessor.default_variables["next_date"] == "_v_next_date_"
        assert preprocessor.default_variables["last_date"] == "_v_last_date_"
        assert preprocessor.default_variables["week_start"] == "_v_week_start_"
        assert preprocessor.default_variables["week_end"] == "_v_week_end_"
        assert preprocessor.default_variables["month_start"] == "_v_month_start_"
        assert preprocessor.default_variables["month_end"] == "_v_month_end_"
        assert preprocessor.default_variables["year_start"] == "_v_year_start_"
        assert preprocessor.default_variables["year_end"] == "_v_year_end_"
        assert preprocessor.default_variables["batch_timestamp"] == "_v_batch_timestamp_"
        assert preprocessor.default_variables["batch_timestamp_with_t"] == "_v_batch_timestamp_with_t_"
    
    def test_process_without_context(self):
        """测试没有上下文时的变量替换"""
        preprocessor = DateVariablePreprocessor()
        
        sql = """
        SELECT * FROM users 
        WHERE create_date = '${batch_date}'
        AND update_date = '${batch_yyyymm}'
        AND status = '${unknown_var}'
        """
        
        result = preprocessor.process(sql)
        
        assert "_v_batch_date_" in result
        assert "${batch_date}" not in result
        
        assert "_v_batch_yyyymm_" in result
        assert "${batch_yyyymm}" not in result
        
        assert "_v_unknown_var_" in result
        assert "${unknown_var}" not in result
    
    def test_process_ignores_context(self):
        """测试预处理器忽略上下文参数"""
        preprocessor = DateVariablePreprocessor()
        
        sql = "SELECT * FROM table WHERE date = '${batch_date}' AND month = '${batch_yyyymm}'"
        
        context = {"batch_date": "20250101"}
        result = preprocessor.process(sql, context)
        
        assert "_v_batch_date_" in result
        assert "20250101" not in result
        assert "_v_batch_yyyymm_" in result
        
        assert "${batch_date}" not in result
        assert "${batch_yyyymm}" not in result
    
    def test_default_variables_keys(self):
        """测试默认变量列表"""
        preprocessor = DateVariablePreprocessor()
        
        for key in ["batch_date", "batch_yyyymm", "next_date", "last_date",
                     "week_start", "month_start", "quarter_start", "year_start"]:
            assert key in preprocessor.default_variables, f"{key}不在default_variables中"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
