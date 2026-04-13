from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from app.services.lint_service import LintService
import logging
import os

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] - %(name)s - %(message)s")
logging.getLogger("uvicorn").setLevel(logging.WARNING)  # 禁用uvicorn的access日志
logging.getLogger("sqlfluff").setLevel(logging.WARNING)  # 禁用sqlfluff的日志
logger = logging.getLogger(__name__)

app = FastAPI()

# 从环境变量获取是否启用热加载，默认启用
ENABLE_HOT_RELOAD = os.getenv("ENABLE_HOT_RELOAD", "true").lower() == "true"
lint_service = LintService(enable_hot_reload=ENABLE_HOT_RELOAD)  # 初始化Lint服务

class SQLRequest(BaseModel):
    sql: str  # 请求体：SQL语句

class RuleFile(BaseModel):
    filename: str
    content: str

@app.post("/lint")
async def lint_sql(request: SQLRequest):
    """提交SQL并返回lint结果"""
    try:
        result = lint_service.lint_sql(request.sql)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules")
async def get_rules():
    """获取当前加载的规则列表"""
    try:
        rules = lint_service.get_loaded_rules()
        return {"status": "success", "rules": rules, "hot_reload_enabled": ENABLE_HOT_RELOAD}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/reload")
async def reload_rules():
    """手动触发规则重新加载"""
    try:
        success = lint_service.manual_reload()
        if success:
            return {"status": "success", "message": "规则重新加载成功"}
        else:
            raise HTTPException(status_code=500, detail="规则重新加载失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # host="0.0.0.0", port=5000
    uvicorn.run(app, host="0.0.0.0", port=5000)
