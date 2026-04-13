from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler


class Rule_SS02(BaseRule):
    """SQL关键字必须大写。"""

    groups = ("all", "customer")
    code = "SS02"
    description = "SQL关键字必须使用大写形式。"
    crawl_behaviour = SegmentSeekerCrawler({"keyword"})
    config_keywords = []

    def _eval(self, context: RuleContext):
        """检查关键字是否大写"""
        segment = context.segment
        
        if segment.is_type("keyword"):
            # 获取关键字文本
            keyword_text = segment.raw if hasattr(segment, 'raw') else ''
            
            # 检查是否不是大写
            if keyword_text and not keyword_text.isupper():
                # 返回违规结果
                return LintResult(
                    anchor=segment,
                    description=f"{self.description} 发现小写关键字: {keyword_text}"
                )
        return None