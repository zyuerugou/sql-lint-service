from sqlfluff.core.rules import BaseRule, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler


class Rule_SS03(BaseRule):
    """表名和字段名应当为小写（双引号内的内容除外）。"""

    groups = ("all", "customer")
    code = "SS03"
    description = "表名和字段名应当使用小写形式（双引号内的内容除外）。"
    crawl_behaviour = SegmentSeekerCrawler({"identifier", "naked_identifier"})
    config_keywords = []

    def _eval(self, context: RuleContext):
        """检查表名和字段名是否为小写"""
        segment = context.segment

        # 检查是否是标识符类型
        if segment.is_type("identifier") or segment.is_type("naked_identifier"):
            # 获取标识符文本
            identifier_text = segment.raw if hasattr(segment, 'raw') else ''

            if not identifier_text:
                return None

            # 检查是否是双引号标识符（如 "TableName"）
            # 双引号标识符应该保持原样，不检查大小写
            if identifier_text.startswith('"') and identifier_text.endswith('"'):
                return None

            # 检查是否是单引号字符串（如 'string value'）
            if identifier_text.startswith("'") and identifier_text.endswith("'"):
                return None

            # 检查是否是反引号标识符（如 `TableName`）
            if identifier_text.startswith('`') and identifier_text.endswith('`'):
                return None

            # 检查是否是数字（如 123）
            if identifier_text.replace('.', '', 1).isdigit():
                return None

            # 检查是否是布尔值或NULL（如 true, false, null）
            # 注意：这些值可能被识别为关键字而不是标识符
            if identifier_text.lower() in ('true', 'false', 'null'):
                return None

            # 检查标识符是否包含大写字母
            if any(c.isupper() for c in identifier_text):
                # 返回违规结果
                return LintResult(
                    anchor=segment,
                    description=f"{self.description} 发现大写标识符: {identifier_text}"
                )

        return None