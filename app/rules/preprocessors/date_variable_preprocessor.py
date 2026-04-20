# coding=utf-8
"""
日期变量预处理器
根据batch_date参数替换SQL中的日期变量，参照references/dateutils.py中的get_useful_date方法
"""

import re
import logging
import datetime
from typing import Dict, Any, Optional

from .base_preprocessor import BasePreprocessor

logger = logging.getLogger(__name__)


class DateVariablePreprocessor(BasePreprocessor):
    """
    日期变量预处理器
    
    功能：
    1. 替换SQL中的日期变量为实际日期值
    2. 参照references/dateutils.py中的get_useful_date方法
    3. 使用固定batch_date=20251231计算日期变量
    4. 不在get_useful_date方法内的变量替换为默认值
    """
    
    # 预处理器执行顺序（在SET过滤器之后，变量替换器之前）
    order = 125
    
    def __init__(self):
        """初始化日期变量预处理器"""
        # 变量正则表达式
        self.variable_pattern = re.compile(r'\$\{([^}]+)\}')
        
        # 默认变量映射（当batch_date未提供或变量不在get_useful_date中时使用）
        # 基于batch_date=20251231计算
        self.default_variables = {
            # 基础日期变量
            "batch_date": "20251231",
            "batch_yyyymm": "202512",
            "next_date": "20260101",
            "last_date": "20251230",
            "max_date": "20991231",
            "min_date": "19000101",
            
            # 周相关
            "retain_week": "20251224",
            "week_start": "20251229",
            "week_end": "20260104",
            "next_week_start": "20260105",
            "next_week_end": "20260111",
            "last_week_start": "20251222",
            "last_week_end": "20251228",
            
            # 月相关
            "retain_month": "20251130",
            "month_start": "20251201",
            "month_end": "20251231",
            "next_month_start": "20260101",
            "next_month_end": "20260131",
            "last_month_start": "20251101",
            "last_month_end": "20251130",
            "last_month_yyyymm": "202511",
            "previous_month_start": "20251001",
            "previous_month_end": "20251031",
            "previous_month_yyyymm": "202510",
            
            # 季度相关
            "quarter_start": "20251001",
            "quarter_end": "20251231",
            "next_quarter_start": "20260101",
            "next_quarter_end": "20260331",
            "last_quarter_start": "20250701",
            "last_quarter_end": "20250930",
            
            # 年相关
            "year_start": "20250101",
            "year_end": "20251231",
            "next_year_start": "20260101",
            "next_year_end": "20261231",
            "last_year_start": "20240101",
            "last_year_end": "20241231",
            "last_year_bath_date": "20241231",
            "year_before_last_bath_date": "20231231",
            
            # 时间戳相关
            "batch_timestamp": "2025-12-31 00:00:00.000000",
            "batch_timestamp_with_t": "2025-12-31T00:00:00.000000",
        }
        
        # get_useful_date方法返回的所有变量名
        self.useful_date_variables = [
            "batch_timestamp",
            "batch_timestamp_with_t",
            "batch_date",
            "batch_yyyymm",
            "next_date",
            "last_date",
            "max_date",
            "min_date",
            "retain_week",
            "retain_month",
            "week_start",
            "week_end",
            "next_week_start",
            "next_week_end",
            "last_week_start",
            "last_week_end",
            "month_start",
            "month_end",
            "last_month_end_list",
            "next_month_start",
            "next_month_end",
            "last_month_start",
            "last_month_end",
            "last_month_yyyymm",
            "previous_month_start",
            "previous_month_end",
            "previous_month_yyyymm",
            "quarter_start",
            "quarter_end",
            "next_quarter_start",
            "next_quarter_end",
            "last_quarter_start",
            "last_quarter_end",
            "year_start",
            "year_end",
            "next_year_start",
            "next_year_end",
            "last_year_start",
            "last_year_end",
            "last_year_bath_date",
            "year_before_last_bath_date"
        ]
    
    def process(self, sql: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        处理SQL，替换所有变量
        
        Args:
            sql: 原始SQL字符串
            context: 上下文信息（不再使用batch_date参数）
            
        Returns:
            处理后的SQL字符串
        """
        if not sql:
            return sql
        
        # 直接使用默认日期变量（不再检查上下文）
        date_variables = self.default_variables.copy()
        
        # 替换所有变量
        def replace_variable(match):
            var_name = match.group(1)
            
            # 首先检查是否在date_variables中（基于batch_date计算的结果）
            if var_name in date_variables:
                return date_variables[var_name]
            
            # 然后检查是否在get_useful_date变量列表中
            elif var_name in self.useful_date_variables:
                # 如果在列表中但不在计算结果中，使用默认值
                if var_name in self.default_variables:
                    logger.warning(f"日期变量 {var_name} 使用默认值")
                    return self.default_variables[var_name]
                else:
                    # 保留原样
                    logger.warning(f"未找到日期变量 {var_name} 的默认值")
                    return match.group(0)
            
            else:
                # 不是日期变量，使用默认值替换
                # 这里可以添加更多的默认值
                default_value = "DEFAULT_VALUE"
                logger.warning(f"变量 {var_name} 不在get_useful_date中，使用默认值: {default_value}")
                return default_value
        
        result = self.variable_pattern.sub(replace_variable, sql)
        return result
    
    def get_info(self) -> Dict[str, Any]:
        """获取预处理器信息"""
        info = super().get_info()
        info.update({
            "description": "日期变量预处理器（参照dateutils.py，使用batch_date=20251231）",
            "requires_batch_date": False,
            "default_batch_date": "20251231",
            "useful_date_variables_count": len(self.useful_date_variables),
            "default_variables_count": len(self.default_variables),
            "abstract_base": False
        })
        return info