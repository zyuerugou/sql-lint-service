# coding=utf-8
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from app.services.lint_service import LintService
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(name)s - %(message)s")
logging.getLogger("uvicorn").setLevel(logging.WARNING)  # 禁用uvicorn的access日志
logging.getLogger("sqlfluff").setLevel(logging.WARNING)  # 禁用sqlfluff的日志
logger = logging.getLogger(__name__)

# 全局服务实例
lint_service = None

# 从环境变量获取是否启用热加载，默认启用
ENABLE_HOT_RELOAD = os.getenv("ENABLE_HOT_RELOAD", "true").lower() == "true"
HOT_RELOAD_DEBOUNCE = float(os.getenv("HOT_RELOAD_DEBOUNCE", "0.5"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global lint_service
    
    # 启动时初始化服务
    logger.info(f"启动SQL Lint Service，热加载: {ENABLE_HOT_RELOAD}，防抖间隔: {HOT_RELOAD_DEBOUNCE}秒")
    lint_service = LintService(
        enable_hot_reload=ENABLE_HOT_RELOAD,
        hot_reload_debounce=HOT_RELOAD_DEBOUNCE
    )
    
    yield  # 应用运行期间
    
    # 关闭时清理资源
    logger.info("正在停止SQL Lint Service...")
    if lint_service:
        lint_service.stop_monitor()
    logger.info("SQL Lint Service已停止")

app = FastAPI(lifespan=lifespan)

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

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 简单测试服务是否正常
        rules = lint_service.get_loaded_rules()
        return {
            "status": "healthy",
            "service": "sql-lint-service",
            "rules_loaded": len(rules),
            "hot_reload_enabled": ENABLE_HOT_RELOAD,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")

@app.get("/monitor/status")
async def monitor_status():
    """获取监控器状态"""
    try:
        from app.services.lint_service import WATCHDOG_AVAILABLE
        
        status = {
            "hot_reload_enabled": ENABLE_HOT_RELOAD,
            "watchdog_available": WATCHDOG_AVAILABLE,
            "rules_dir": lint_service.rules_dir,
            "debounce_seconds": HOT_RELOAD_DEBOUNCE
        }
        
        return {"status": "success", "monitor": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # host="0.0.0.0", port=5000
    uvicorn.run(app, host="0.0.0.0", port=5000)
