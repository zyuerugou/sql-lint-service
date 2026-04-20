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
        # 使用项目中的预处理器目录
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        
        manager = PreprocessorManager(preprocessors_dir)
        
        # 应该加载了2个预处理器
        assert len(manager) == 2
        assert str(manager) == "PreprocessorManager (2 preprocessors)"
    
    def test_process_sql_with_preprocessors(self):
        """测试使用预处理器处理SQL"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        # 测试SQL包含SET语句和变量
        sql = """
        set hive.exec.dynamic.partition.mode=nonstrict;
        SELECT * FROM table WHERE date = '${batch_date}';
        set another.config = value;
        """
        
        result = manager.process(sql)
        
        # SET语句应该被过滤
        lines = result.split('\n')
        assert lines[1] == ""  # 第一行SET语句被过滤
        assert "20251231" in result  # 变量被替换（日期格式为YYYYMMDD）
        assert lines[3] == ""  # 第二行SET语句被过滤
    
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
        
        assert len(info_list) == 2
        
        # 检查预处理器信息
        names = [info["name"] for info in info_list]
        assert "SetStatementFilterPreprocessor" in names
        assert "DateVariablePreprocessor" in names
        
        # 检查顺序
        orders = [info["order"] for info in info_list]
        assert orders == [100, 125]  # 按order排序
    
    def test_reload(self):
        """测试重新加载"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
        
        # 初始加载2个预处理器
        initial_count = len(manager)
        assert initial_count == 2
        
        # 重新加载
        new_count = manager.reload()
        assert new_count == 2  # 应该还是2个
    
    def test_nonexistent_directory(self):
        """测试不存在的目录"""
        manager = PreprocessorManager("/nonexistent/directory")
        
        # 应该没有预处理器被加载
        assert len(manager) == 0
    
    def test_preprocessor_order_execution(self):
        """测试预处理器执行顺序"""
        preprocessors_dir = str(Path(__file__).parent.parent / "app" / "rules" / "preprocessors")
        manager = PreprocessorManager(preprocessors_dir)
    
        # 创建一个测试SQL，包含SET语句和变量
        sql = "set config=value; SELECT '${batch_date}'"
    
        result = manager.process(sql)
    
        # SET语句过滤器(order=100)先执行，过滤SET语句
        # 日期变量预处理器(order=125)后执行，替换变量
        assert result.strip() == "SELECT '20251231'"  # SET语句被过滤，变量被替换（YYYYMMDD格式）
        assert "set config" not in result  # SET语句应该被移除
        assert "20251231" in result  # 变量应该被替换