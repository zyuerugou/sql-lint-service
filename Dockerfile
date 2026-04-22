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

# 安装系统依赖并清理缓存以减小镜像大小
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/info/*

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装poetry和项目依赖，使用--no-cache-dir避免缓存
RUN pip install --no-cache-dir poetry==2.3.1 && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root --no-interaction --no-ansi --no-cache

# 复制应用代码（使用.dockerignore排除不需要的文件）
COPY app/ app/

# 创建日志目录和非root用户，并清理不必要的文件
RUN mkdir -p /app/logs && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    # 清理Python字节码缓存和临时文件
    find /app -type f -name '*.pyc' -delete && \
    find /app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
    # 清理其他不必要的文件
    rm -rf /root/.cache /home/appuser/.cache
USER appuser

# 暴露端口
EXPOSE ${PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 启动命令
CMD ["python", "-m", "app.main"]