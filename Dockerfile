# 使用Python 3.12作为基础镜像
FROM python:3.12-slim

# 构建参数
ARG VERSION=0.1.0

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENABLE_HOT_RELOAD=true \
    HOT_RELOAD_DEBOUNCE=0.5 \
    PORT=5000 \
    LOG_LEVEL=INFO \
    LOG_DIR=/app/logs \
    LOG_FILE=sql-lint-service.log \
    APP_VERSION=${VERSION} \
    # 优化参数
    TIMEOUT_SECONDS=5 \
    MAX_SQL_SIZE_MB=10 \
    ENABLE_SAMPLING=true \
    SAMPLING_THRESHOLD_KB=100 \
    CACHE_SIZE=100 \
    SQL_DIALECT=ansi

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装poetry（版本与本地一致：2.3.1）和项目依赖
RUN pip install --no-cache-dir poetry==2.3.1 && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root --no-interaction --no-ansi

# 复制应用代码（使用.dockerignore排除不需要的文件）
COPY app/ app/

# 创建日志目录和非root用户
RUN mkdir -p /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE ${PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 启动命令
CMD ["python", "-m", "app.main"]