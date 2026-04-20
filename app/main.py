# coding=utf-8
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from app.services.lint_service import LintService
import logging
import os
import sys
from pathlib import Path

# 从环境变量获取日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
LOG_FILE = os.getenv("LOG_FILE", "sql-lint-service.log")

# 确保日志目录存在
log_dir_path = Path(LOG_DIR)
log_dir_path.mkdir(parents=True, exist_ok=True)

# 日志文件路径
log_file_path = log_dir_path / LOG_FILE

# 日志格式
log_format = "%(asctime)s [%(levelname)s] - %(name)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# 清除现有的处理器
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 添加文件处理器
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(file_handler)

# 添加控制台处理器（用于Docker日志）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(console_handler)

# 设置特定日志器的级别
logging.getLogger("uvicorn").setLevel(logging.WARNING)  # 禁用uvicorn的access日志
logging.getLogger("sqlfluff").setLevel(logging.WARNING)  # 禁用sqlfluff的日志
logging.getLogger("watchdog").setLevel(logging.INFO)     # 设置watchdog日志级别

logger = logging.getLogger(__name__)

# 全局服务实例
from typing import Optional
lint_service: Optional[LintService] = None

# 从环境变量获取是否启用热加载，默认启用
ENABLE_HOT_RELOAD = os.getenv("ENABLE_HOT_RELOAD", "true").lower() == "true"
HOT_RELOAD_DEBOUNCE = float(os.getenv("HOT_RELOAD_DEBOUNCE", "0.5"))
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")

# 优化参数配置
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "5"))
MAX_SQL_SIZE_MB = int(os.getenv("MAX_SQL_SIZE_MB", "10"))
ENABLE_SAMPLING = os.getenv("ENABLE_SAMPLING", "true").lower() == "true"
SAMPLING_THRESHOLD_KB = int(os.getenv("SAMPLING_THRESHOLD_KB", "100"))
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "100"))
# SQL方言配置，支持：ansi, hive, sparksql, oracle, mysql, postgres等
SQL_DIALECT = os.getenv("SQL_DIALECT", "ansi")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global lint_service
    
    # 启动时初始化服务
    logger.info(f"启动SQL Lint Service v{APP_VERSION}")
    logger.info(f"日志配置 - 级别: {LOG_LEVEL}, 目录: {LOG_DIR}, 文件: {LOG_FILE}")
    logger.info(f"热加载配置 - 启用: {ENABLE_HOT_RELOAD}, 防抖间隔: {HOT_RELOAD_DEBOUNCE}秒")
    logger.info(f"优化配置 - 超时: {TIMEOUT_SECONDS}秒, 最大SQL: {MAX_SQL_SIZE_MB}MB, 采样: {ENABLE_SAMPLING}, 方言: {SQL_DIALECT}")
    lint_service = LintService(
        enable_hot_reload=ENABLE_HOT_RELOAD,
        hot_reload_debounce=HOT_RELOAD_DEBOUNCE,
        timeout_seconds=TIMEOUT_SECONDS,
        max_sql_size_mb=MAX_SQL_SIZE_MB,
        enable_sampling=ENABLE_SAMPLING,
        sampling_threshold_kb=SAMPLING_THRESHOLD_KB,
        cache_size=CACHE_SIZE,
        sql_dialect=SQL_DIALECT
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
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        result = lint_service.lint_sql(request.sql)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules")
async def get_rules():
    """获取当前加载的规则列表"""
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        rules = lint_service.get_loaded_rules()
        return {"status": "success", "rules": rules, "hot_reload_enabled": ENABLE_HOT_RELOAD}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preprocessors")
async def get_preprocessors():
    """获取当前加载的预处理器信息"""
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        preprocessors = lint_service.get_loaded_preprocessors()
        return {"status": "success", "preprocessors": preprocessors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules/reload")
async def reload_rules():
    """手动触发规则重新加载"""
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
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
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        # 简单测试服务是否正常
        rules = lint_service.get_loaded_rules()
        return {
            "status": "healthy",
            "service": "sql-lint-service",
            "rules_loaded": len(rules),
            "hot_reload_enabled": ENABLE_HOT_RELOAD,
            "optimization_config": {
                "timeout_seconds": TIMEOUT_SECONDS,
                "max_sql_size_mb": MAX_SQL_SIZE_MB,
                "enable_sampling": ENABLE_SAMPLING,
                "sampling_threshold_kb": SAMPLING_THRESHOLD_KB,
                "cache_size": CACHE_SIZE
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"服务异常: {str(e)}")

@app.get("/monitor/status")
async def monitor_status():
    """获取监控器状态"""
    if lint_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    try:
        status = {
            "hot_reload_enabled": ENABLE_HOT_RELOAD,
            "watchdog_available": True,  # watchdog是必需依赖
            "rules_dir": lint_service.rules_dir,
            "debounce_seconds": HOT_RELOAD_DEBOUNCE
        }
        
        return {"status": "success", "monitor": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # host="0.0.0.0", port=5000
    uvicorn.run(app, host="0.0.0.0", port=5000)
