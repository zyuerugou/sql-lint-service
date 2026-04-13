from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler


class Rule_SS01(BaseRule):
    """禁止使用 SELECT *。"""

    groups = ("all", "customer")
    code = "SS01"
    description = "禁止使用 SELECT *，请明确列出所有字段。"
    crawl_behaviour = SegmentSeekerCrawler({"select_clause"})
    config_keywords = []

    def _eval(self, context: RuleContext):
        """禁止 select * 语句"""
        segment = context.segment
        
        # 检查select子句中是否包含*
        if segment.is_type("select_clause"):
            # 查找所有子节点
            for child in segment.raw_segments:
                # 检查是否是通配符（*）
                if hasattr(child, 'raw') and child.raw == '*':
                    # 返回违规结果
                    return LintResult(
                        anchor=child,
                        description=self.description
                    )
                # 也检查wildcard_expression类型
                if child.is_type("wildcard_expression"):
                    # 返回违规结果
                    return LintResult(
                        anchor=child,
                        description=self.description
                    )
        return None
