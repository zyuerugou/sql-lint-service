"""
测试预处理器管理器
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from app.services.preprocessor_manager import PreprocessorManager


class TestPreprocessorManager:
    """测试预处理器管理器"""
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        
        manager = PreprocessorManager(preprocessors_dir)
        
        assert len(manager) == 3
        assert str(manager) == "PreprocessorManager (3 preprocessors)"
    
    def test_process_sql_with_preprocessors(self):
        """测试使用预处理器处理SQL"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        sql = """
        set hive.exec.dynamic.partition.mode=nonstrict;
        SELECT * FROM table WHERE date = '${batch_date}';
        set tez.queue.name=default;
        """
        
        result = manager.process(sql)
        
        lines = result.split('\n')
        assert lines[1] == ""
        assert "_v_batch_date_" in result
        assert lines[3] == ""
    
    def test_process_empty_sql(self):
        """测试处理空SQL"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        result = manager.process("")
        assert result == ""
    
    def test_get_preprocessors_info(self):
        """测试获取预处理器信息"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        info_list = manager.get_preprocessors_info()
        
        assert len(info_list) == 3
        
        names = [info["name"] for info in info_list]
        assert "CommentFilterPreprocessor" in names
        assert "SetStatementFilterPreprocessor" in names
        assert "DateVariablePreprocessor" in names
        
        orders = [info["order"] for info in info_list]
        assert orders == [10, 100, 125]
    
    def test_reload(self):
        """测试重新加载"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        initial_count = len(manager)
        assert initial_count == 3
        
        new_count = manager.reload()
        assert new_count == 3
    
    def test_nonexistent_directory(self):
        """测试不存在的目录"""
        manager = PreprocessorManager("/nonexistent/directory")
        
        assert len(manager) == 0
    
    def test_preprocessor_order_execution(self):
        """测试预处理器执行顺序"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
    
        sql = "set hive.exec.dynamic.partition.mode=nonstrict;\nSELECT '_v_batch_date_'"
    
        result = manager.process(sql)
    
        assert "set hive.exec" not in result
        assert "_v_batch_date_" in result
