# coding=utf-8
from sqlfluff.core.rules import BaseRule, RuleContext, LintResult
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler


class Rule_SS03(BaseRule):
    """除了关键字、双引号、引号内的内容以外，表名和字段名应当为小写"""
    
    groups = ("all", "customer")
    crawl_behaviour = SegmentSeekerCrawler({"identifier", "naked_identifier", "quoted_identifier"})
    
    def _eval(self, context: RuleContext):
        # 获取当前segment
        segment = context.segment
        
        # 检查是否是标识符
        if segment.type in ["identifier", "naked_identifier", "quoted_identifier"]:
            identifier_name = segment.raw
            
            # 如果是引号标识符（双引号、单引号、反引号），跳过检查
            if segment.type == "quoted_identifier":
                # 检查引号类型
                if identifier_name.startswith(('"', "'", "`")):
                    return None
            
            # 检查是否是数字或布尔值
            if identifier_name.lower() in ["true", "false", "null"]:
                return None
            
            # 检查是否是数字
            if identifier_name.replace(".", "").isdigit():
                return None
            
            # 检查是否包含大写字母
            if any(c.isupper() for c in identifier_name):
                # 获取父级上下文，检查是否在关键字上下文中
                parent = segment._parent
                while parent:
                    if hasattr(parent, 'type') and parent.type in ["keyword", "function_name", "type_identifier"]:
                        return None
                    parent = parent._parent if hasattr(parent, '_parent') else None
                
                return LintResult(
                    anchor=segment,
                    description=f"标识符应当为小写: {identifier_name}",
                )
        
        return None