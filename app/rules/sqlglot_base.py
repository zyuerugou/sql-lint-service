#!/usr/bin/env python3
# coding=utf-8
"""
sqlglot规则基类
定义sqlglot规则的统一接口和基础功能
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import sqlglot.expressions as exp

logger = logging.getLogger(__name__)


class Violation:
    """规则违规结果"""
    
    def __init__(self, rule_id: str, message: str, line: int, column: int, severity: str = "error"):
        self.rule_id = rule_id
        self.message = message
        self.line = line
        self.column = column
        self.severity = severity
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity,
            "line": self.line,
            "column": self.column
        }


class SQLGlotBaseRule(ABC):
    """
    sqlglot规则抽象基类
    
    所有基于sqlglot的规则必须继承此类并实现check方法
    """
    
    # 规则元数据
    code: str = ""  # 规则代码，如"SS01"
    description: str = ""  # 规则描述
    groups: tuple = ("all", "customer")  # 规则分组
    
    def __init__(self):
        """初始化规则"""
        if not self.code:
            self.code = self.__class__.__name__
    
    @abstractmethod
    def check(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        """
        检查SQL AST，返回违规列表
        
        Args:
            ast: sqlglot解析的AST
            sql: 原始SQL字符串（可选，用于更准确的位置信息）
            
        Returns:
            违规列表
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取规则信息"""
        return {
            "code": self.code,
            "description": self.description,
            "groups": self.groups,
            "class_name": self.__class__.__name__
        }
    
    def _get_position(self, expr: exp.Expression, sql: str = "", ast_start_pos: int = 0) -> tuple:
        """
        获取表达式的位置信息
        
        Args:
            expr: sqlglot表达式
            sql: 原始SQL字符串（可选，用于更准确的位置信息）
            
        Returns:
            (行号, 列号)，如果无法获取返回(1, 1)
        """
        try:
            # 首先尝试从sqlglot的token位置获取
            # sqlglot 24.x版本中，位置信息可能不在meta中
            
            # 方法1: 检查是否有直接的位置属性
            # 检查更多可能的属性名，包括sqlglot不同版本使用的
            line_attrs = ['line', 'start_line', 'this_line', 'line_no']
            col_attrs = ['col', 'start_col', 'this_col', 'column_no']
            
            line = 0
            col = 0
            
            # 查找行号
            for attr_name in line_attrs:
                if hasattr(expr, attr_name):
                    value = getattr(expr, attr_name)
                    if value and isinstance(value, int) and value > 0:
                        line = value
                        break
            
            # 查找列号
            for attr_name in col_attrs:
                if hasattr(expr, attr_name):
                    value = getattr(expr, attr_name)
                    if value and isinstance(value, int) and value > 0:
                        col = value
                        break
            
            # 如果找到了行和列，返回
            if line > 0 and col > 0:
                return line, col
            
            # 如果只找到了行号，尝试找对应的列号
            if line > 0:
                # 尝试从其他属性找列号
                for attr_name in ['col', 'start_col', 'this_col', 'column_no', 'start']:
                    if hasattr(expr, attr_name):
                        value = getattr(expr, attr_name)
                        if value and isinstance(value, int) and value > 0:
                            return line, value
                return line, 1
            
            # 如果只找到了列号，尝试找对应的行号
            if col > 0:
                # 尝试从其他属性找行号
                for attr_name in ['line', 'start_line', 'this_line', 'line_no']:
                    if hasattr(expr, attr_name):
                        value = getattr(expr, attr_name)
                        if value and isinstance(value, int) and value > 0:
                            return value, col
                return 1, col
            
            # 方法2: 检查meta字典
            if hasattr(expr, 'meta') and expr.meta:
                line = expr.meta.get('line', 1)
                col = expr.meta.get('col', 1)
                if line != 1 or col != 1:
                    return line, col
            
            # 方法3: 对于特定类型的表达式，使用上下文感知的位置查找
            if sql:
                # 导入re模块
                import re
                
                # 对于Column节点，特别处理
                if isinstance(expr, exp.Column) and hasattr(expr, 'name') and expr.name:
                    # 检查是否在SELECT中
                    parent = expr.parent
                    if parent and isinstance(parent, exp.Select):
                        # 获取SELECT的SQL
                        select_sql = parent.sql()
                        
                        # 在SELECT SQL中查找列名
                        col_match = re.search(re.escape(expr.name), select_sql, re.IGNORECASE)
                        if col_match:
                            # 尝试找到这个SELECT在完整SQL中的位置
                            # 首先找到包含这个SELECT的根表达式（如Insert）
                            root_expr = expr
                            while root_expr.parent:
                                root_expr = root_expr.parent
                                if isinstance(root_expr, (exp.Insert, exp.Select, exp.Create, exp.Update, exp.Delete)):
                                    break
                            
                            # 获取根表达式的SQL
                            root_sql = root_expr.sql() if hasattr(root_expr, 'sql') else ""
                            
                            if root_sql:
                                # 在完整SQL中查找根表达式
                                # 使用更精确的查找：确保匹配完整的单词
                                root_pattern = re.escape(root_sql)
                                root_matches = list(re.finditer(root_pattern, sql, re.IGNORECASE))
                                
                                if root_matches:
                                    # 如果有多个匹配，选择最可能的一个
                                    # 对于我们的情况，选择最后一个匹配（假设相同的INSERT语句在后面）
                                    root_match = root_matches[-1]
                                    root_start = root_match.start()
                                    
                                    # 在根表达式中查找SELECT
                                    root_text = sql[root_start:root_start + len(root_sql)]
                                    select_in_root = re.search(r'\bSELECT\b', root_text, re.IGNORECASE)
                                    
                                    if select_in_root:
                                        select_start = root_start + select_in_root.start()
                                        
                                        # 列在SELECT中的位置
                                        col_in_select = col_match.start()
                                        
                                        # 列在整个SQL中的位置
                                        col_in_sql = select_start + col_in_select
                                        
                                        # 计算行和列
                                        lines_before = sql[:col_in_sql].split('\n')
                                        line_num = len(lines_before)
                                        
                                        if line_num > 0:
                                            last_line_start = sql.rfind('\n', 0, col_in_sql)
                                            if last_line_start == -1:
                                                col_num = col_in_sql + 1  # 第一行
                                            else:
                                                col_num = col_in_sql - last_line_start
                                        else:
                                            col_num = col_in_sql + 1
                                        
                                        return line_num, col_num
            
            # 方法4: 如果有原始SQL，尝试在SQL中查找表达式（大小写敏感）
            if sql:
                # 根据表达式类型生成查找模式
                pattern = self._get_expression_pattern(expr)
                if pattern:
                    # 首先尝试大小写敏感查找
                    line, col = self._find_in_sql(pattern, sql, case_sensitive=True)
                    if line != 1 or col != 1:
                        return line, col
                    
                    # 如果大小写敏感没找到，再尝试大小写不敏感
                    line, col = self._find_in_sql(pattern, sql, case_sensitive=False)
                    if line != 1 or col != 1:
                        return line, col
            
            # 方法4: 对于特定类型的表达式，提供智能默认位置
            if isinstance(expr, exp.Select):
                return 1, 1
            elif isinstance(expr, exp.Star):
                # SELECT * 中的*通常在SELECT之后
                return 1, 8  # SELECT (7字符) + 空格
            elif isinstance(expr, exp.Table) and hasattr(expr, 'name'):
                # 表名，尝试估算位置
                return 1, 15  # SELECT * FROM (14字符) + 空格
            
            # 方法5: 尝试从父节点获取
            if hasattr(expr, 'parent') and expr.parent:
                return self._get_position(expr.parent, sql)
                
        except Exception as e:
            logger.debug(f"获取位置信息失败: {type(e).__name__}: {e}")
        
        # 默认返回行1列1
        return 1, 1
    
    def _get_expression_pattern(self, expr: exp.Expression) -> str:
        """
        根据表达式类型生成正则表达式模式
        
        Args:
            expr: sqlglot表达式
            
        Returns:
            正则表达式模式字符串，如果无法生成返回None
        """
        try:
            if isinstance(expr, exp.Star):
                return r'\*'
            elif isinstance(expr, exp.Table) and hasattr(expr, 'name'):
                # 转义表名中的特殊字符
                table_name = re.escape(expr.name)
                return table_name
            elif isinstance(expr, exp.Column) and hasattr(expr, 'name'):
                # 转义列名中的特殊字符
                column_name = re.escape(expr.name)
                return column_name
            elif isinstance(expr, exp.Identifier) and hasattr(expr, 'name'):
                # 转义标识符中的特殊字符
                identifier_name = re.escape(expr.name)
                return identifier_name
            elif hasattr(expr, 'name'):
                # 其他有name属性的表达式
                name = re.escape(str(expr.name))
                return name
            elif hasattr(expr, 'this'):
                # 尝试从this属性获取
                this_expr = expr.this
                if this_expr:
                    return self._get_expression_pattern(this_expr)
        except Exception as e:
            logger.debug(f"生成表达式模式失败: {type(e).__name__}: {e}")
        
        return None
    
    def _find_in_sql(self, pattern: str, sql: str, default_line: int = 1, case_sensitive: bool = False, start_pos: int = 0) -> tuple:
        """
        在SQL字符串中查找模式的位置
        
        Args:
            pattern: 要查找的正则表达式模式
            sql: SQL字符串
            default_line: 默认行号
            case_sensitive: 是否大小写敏感
            start_pos: 开始查找的位置（字符位置）
            
        Returns:
            (行号, 列号)
        """
        try:
            if not sql:
                return default_line, 1
            
            # 设置正则标志
            flags = 0
            if not case_sensitive:
                flags = re.IGNORECASE
            
            # 从start_pos开始查找
            search_text = sql[start_pos:] if start_pos > 0 else sql
            
            # 按行分割SQL
            lines = search_text.split('\n')
            
            for line_num_offset, line in enumerate(lines, 1):
                match = re.search(pattern, line, flags)
                if match:
                    # 计算实际行号
                    actual_line = default_line + line_num_offset - 1
                    # 计算列号
                    col = match.start() + 1  # 列号从1开始
                    
                    # 如果不是第一行，需要调整列号
                    if line_num_offset > 1:
                        # 计算前几行的总长度
                        prev_lines = '\n'.join(lines[:line_num_offset-1])
                        col = match.start() + 1
                    else:
                        # 第一行，需要考虑start_pos
                        if start_pos > 0:
                            # 计算start_pos之前的行数
                            text_before = sql[:start_pos]
                            lines_before = text_before.split('\n')
                            actual_line = len(lines_before) + 1
                            
                            # 计算列号
                            if len(lines_before) > 0:
                                last_line_len = len(lines_before[-1])
                                col = match.start() + 1
                            else:
                                col = start_pos + match.start() + 1
                    
                    return actual_line, col
            
            # 如果没有找到，在整个搜索文本中查找
            full_match = re.search(pattern, search_text, flags)
            if full_match:
                # 计算在整个SQL中的位置
                pos = start_pos + full_match.start()
                # 计算对应的行和列
                text_before = sql[:pos]
                lines_before = text_before.split('\n')
                line_num = len(lines_before)
                col_num = len(lines_before[-1]) + 1 if lines_before else pos + 1
                return line_num, col_num
                
        except Exception as e:
            logger.debug(f"在SQL中查找模式失败: {pattern}, 错误: {e}")
        
        return default_line, 1
    
    def __str__(self) -> str:
        """返回规则描述"""
        return f"{self.code}: {self.description}"
    
    def __repr__(self) -> str:
        """返回规则表示"""
        return f"{self.__class__.__name__}(code={self.code})"


class SQLGlotRuleLoader:
    """
    sqlglot规则加载器
    
    动态加载基于sqlglot的规则
    """
    
    def __init__(self, rules_dir: str):
        """
        初始化规则加载器
        
        Args:
            rules_dir: 规则目录路径
        """
        self.rules_dir = rules_dir
        self.loaded_rules: Dict[str, SQLGlotBaseRule] = {}
    
    def load_rules_from_files(self) -> List[SQLGlotBaseRule]:
        """
        从文件加载所有规则
        
        Returns:
            规则实例列表
        """
        import os
        import sys
        import importlib
        
        rules_list = []
        
        # 扫描规则目录
        for filename in os.listdir(self.rules_dir):
            if filename.endswith('.py') and filename.startswith('rule_') and not filename.endswith('.disabled'):
                module_name = filename[:-3]  # 移除.py
                
                try:
                    # 动态导入模块
                    module_path = f"app.rules.{module_name}"
                    
                    # 清理模块缓存（如果存在）
                    # 需要清理所有相关的模块缓存
                    modules_to_remove = []
                    for cached_module in list(sys.modules.keys()):
                        if cached_module == module_path or cached_module.startswith(module_path + '.'):
                            modules_to_remove.append(cached_module)
                    
                    for module_to_remove in modules_to_remove:
                        del sys.modules[module_to_remove]
                        logger.debug(f"清理规则模块缓存: {module_to_remove}")
                    
                    module = importlib.import_module(module_path)
                    
                    # 查找规则类（类名与文件名相同，但首字母大写）
                    # 支持两种命名约定：Rule_Ss04Sqlglot 和 RuleSs04Sqlglot
                    class_name1 = ''.join(word.capitalize() for word in module_name.split('_'))
                    class_name2 = 'Rule_' + ''.join(word.capitalize() for word in module_name.split('_')[1:])
                    
                    # 尝试第一种命名约定
                    class_name = class_name1
                    if not hasattr(module, class_name1) and hasattr(module, class_name2):
                        class_name = class_name2
                    
                    if hasattr(module, class_name):
                        rule_class = getattr(module, class_name)
                        
                        # 检查是否是SQLGlotBaseRule的子类
                        # 注意：由于模块缓存问题，issubclass可能失败，所以简化检查
                        if isinstance(rule_class, type):
                            # 检查是否有必要的属性和方法
                            # code, description, severity 可以是类属性或实例属性
                            # check 必须是方法
                            has_check = hasattr(rule_class, 'check') and callable(getattr(rule_class, 'check', None))
                            
                            if has_check:
                                # 创建规则实例
                                try:
                                    rule_instance = rule_class()
                                    rules_list.append(rule_instance)
                                    
                                    # 记录到加载的规则字典
                                    self.loaded_rules[rule_instance.code] = rule_instance
                                    
                                    logger.info(f"sqlglot规则加载成功: {rule_instance.code}")
                                except Exception as e:
                                    logger.error(f"实例化规则 {class_name} 失败: {e}")
                            else:
                                logger.warning(f"文件 {filename} 中的类 {class_name} 缺少check方法")
                        else:
                            logger.warning(f"文件 {filename} 中的 {class_name} 不是类")
                    else:
                        logger.warning(f"文件 {filename} 中没有找到类 {class_name}")
                        
                except Exception as e:
                    logger.error(f"加载规则文件 {filename} 失败: {type(e).__name__}: {e}")
        
        logger.info(f"共加载 {len(rules_list)} 个sqlglot规则")
        return rules_list
    
    def reload_rules(self) -> List[SQLGlotBaseRule]:
        """重新加载所有规则"""
        self.loaded_rules.clear()
        return self.load_rules_from_files()
    
    def get_rule(self, rule_code: str) -> Optional[SQLGlotBaseRule]:
        """根据规则代码获取规则实例"""
        return self.loaded_rules.get(rule_code)
    
    def get_all_rules(self) -> List[SQLGlotBaseRule]:
        """获取所有已加载的规则"""
        return list(self.loaded_rules.values())
    
    def get_rule_codes(self) -> List[str]:
        """获取所有已加载的规则代码"""
        return list(self.loaded_rules.keys())
    
    def check_all_rules(self, ast: exp.Expression, sql: str = "") -> List[Violation]:
        """
        应用所有规则检查
        
        Args:
            ast: sqlglot AST
            sql: 原始SQL字符串
            
        Returns:
            所有违规结果
        """
        all_violations = []
        
        for rule in self.get_all_rules():
            try:
                violations = rule.check(ast, sql)
                all_violations.extend(violations)
            except Exception as e:
                logger.error(f"规则 {rule.code} 检查失败: {type(e).__name__}: {e}")
        
        return all_violations


