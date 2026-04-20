"""
测试SET语句过滤器预处理器
"""

import pytest
from app.rules.preprocessors.set_statement_filter_preprocessor import SetStatementFilterPreprocessor


class TestSetStatementFilterPreprocessor:
    """测试SET语句过滤器预处理器"""
    
    @pytest.fixture
    def preprocessor(self):
        """创建预处理器实例"""
        return SetStatementFilterPreprocessor()
    
    def test_filter_hive_set_statements(self, preprocessor):
        """测试过滤Hive SET语句"""
        sql = """
        set hive.exec.dynamic.partition.mode=nonstrict;
        SELECT * FROM table;
        set tez.queue.name=default;
        INSERT INTO table VALUES (1, 2);
        """
        
        result = preprocessor.process(sql)
        
        # SET语句应该被过滤为空行
        lines = result.split('\n')
        assert lines[1] == ""  # 第一行SET语句
        assert lines[2].strip() == "SELECT * FROM table;"
        assert lines[3] == ""  # 第二行SET语句
        assert lines[4].strip() == "INSERT INTO table VALUES (1, 2);"
    
    def test_filter_all_set_statements(self, preprocessor):
        """测试过滤所有SET配置语句"""
        sql = """
        set my.config=value;
        SELECT * FROM table;
        set another.config = 123;
        """
        
        result = preprocessor.process(sql)
        
        lines = result.split('\n')
        assert lines[1] == ""  # SET语句被过滤
        assert lines[2].strip() == "SELECT * FROM table;"
        assert lines[3] == ""  # SET语句被过滤
    
    def test_not_filter_update_set(self, preprocessor):
        """测试不过滤UPDATE语句中的SET子句"""
        sql = """
        UPDATE table SET column1 = 'value' WHERE id = 1;
        set config.value = 123;
        UPDATE another SET col = 'test' WHERE condition;
        """
        
        result = preprocessor.process(sql)
        
        lines = result.split('\n')
        assert "UPDATE table SET column1 = 'value' WHERE id = 1;" in result
        assert lines[2] == ""  # SET配置语句被过滤
        assert "UPDATE another SET col = 'test' WHERE condition;" in result
    
    def test_empty_sql(self, preprocessor):
        """测试空SQL"""
        result = preprocessor.process("")
        assert result == ""
    
    def test_no_set_statements(self, preprocessor):
        """测试没有SET语句的SQL"""
        sql = """
        SELECT * FROM users;
        INSERT INTO logs VALUES (1, 'test');
        DELETE FROM temp WHERE id = 5;
        """
        
        result = preprocessor.process(sql)
        # 由于处理逻辑会去除语句前后的空格，所以结果会有所不同
        # 但核心内容应该保持不变
        assert "SELECT * FROM users;" in result
        assert "INSERT INTO logs VALUES (1, 'test');" in result
        assert "DELETE FROM temp WHERE id = 5;" in result
    
    def test_get_info(self, preprocessor):
        """测试获取预处理器信息"""
        info = preprocessor.get_info()
        
        assert info["name"] == "SetStatementFilterPreprocessor"
        assert info["description"] == "SET语句过滤器预处理器"
        assert info["order"] == 100
        assert "patterns_count" in info
    
    def test_order_property(self, preprocessor):
        """测试order属性"""
        assert hasattr(preprocessor, 'order')
        assert preprocessor.order == 100