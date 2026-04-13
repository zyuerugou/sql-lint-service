from sqlfluff.core.plugin import hookimpl

@hookimpl
def get_rules():
    # Rules should be imported within the `get_rules` method instead
    from app.rules.rule_ss01 import Rule_SS01
    from app.rules.rule_ss02 import Rule_SS02
    from app.rules.rule_ss03 import Rule_SS03
    return [Rule_SS01, Rule_SS02, Rule_SS03]