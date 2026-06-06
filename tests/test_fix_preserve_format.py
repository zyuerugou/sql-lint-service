import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.lint_service import LintService

def test_preserves_format():
    service = LintService(enable_hot_reload=False)

    sql = "select crm_cust_id, crm_cust_name from customers where   crm_status = 'ACTIVE'"
    fixed = service.fix_sql(sql)
    print(f"原始: {repr(sql)}")
    print(f"修正: {repr(fixed)}")
    # 确保只改了关键字大小写，空格格式不变
    assert "  " in fixed, "多空格应保留"
    assert fixed == "SELECT crm_cust_id, crm_cust_name FROM customers WHERE   crm_status = 'ACTIVE'"

    sql2 = "insert into target (crm_cust_id)\nselect crm_cust_id from source\nwhere crm_status = 'ACTIVE'"
    fixed2 = service.fix_sql(sql2)
    print(f"原始: {repr(sql2)}")
    print(f"修正: {repr(fixed2)}")
    assert "\n" in fixed2, "换行应保留"
    assert fixed2 == "INSERT INTO target (crm_cust_id)\nSELECT crm_cust_id FROM source\nWHERE crm_status = 'ACTIVE'"

    print("所有格式保留测试通过")

test_preserves_format()
