# SQL Lint Service 部署指南

## 版本信息
- **当前版本**: 0.2.0
- **SQL解析引擎**: sqlglot (已从sqlfluff迁移)
- **性能提升**: 24.69倍 (相比sqlfluff)
- **Python版本**: 3.12+

## 部署方式

### 1. 使用Docker (推荐)

#### 使用专用Docker脚本

**Linux/macOS (bash):**
```bash
# 构建镜像
./docker-build.sh

# 不使用缓存构建
./docker-build.sh --no-cache

# 构建特定版本
./docker-build.sh --tag v0.2.0 --version 0.2.0

# 启动服务（后台运行，自动挂载规则和日志目录）
./docker-run.sh start

# 停止服务
./docker-run.sh stop

# 重启服务
./docker-run.sh restart

# 查看日志
./docker-run.sh logs

# 查看服务状态
./docker-run.sh status

# 清理Docker资源
./docker-run.sh clean

# 显示帮助
./docker-run.sh help
```

**Windows (PowerShell):**
```powershell
# 构建镜像
.\docker-build.ps1

# 不使用缓存构建
.\docker-build.ps1 -NoCache

# 构建特定版本
.\docker-build.ps1 -Tag v0.2.0 -Version 0.2.0

# 启动服务（后台运行，自动挂载规则和日志目录）
.\docker-run.ps1 start

# 停止服务
.\docker-run.ps1 stop

# 重启服务
.\docker-run.ps1 restart

# 查看日志
.\docker-run.ps1 logs

# 查看服务状态
.\docker-run.ps1 status

# 清理Docker资源
.\docker-run.ps1 clean

# 显示帮助
.\docker-run.ps1 help
```

#### 直接使用Docker命令
```bash
# 构建镜像
docker build -t sql-lint-service:latest .

# 运行容器
docker run -p 5000:5000 sql-lint-service:latest

# 启用规则热加载
docker run -p 5000:5000 -v $(pwd)/app/rules:/app/app/rules:ro sql-lint-service:latest
```

#### 运行容器
```bash
# 基本运行
docker run -p 5000:5000 sql-lint-service:latest

# 使用docker-compose (推荐)
docker-compose up -d

# 自定义配置
docker run -p 5000:5000 \
  -e LOG_LEVEL=DEBUG \
  -e SQL_DIALECT=spark \
  -v $(pwd)/app/rules:/app/app/rules:ro \
  sql-lint-service:latest
```

### 2. 使用Poetry (开发环境)

#### 安装依赖
```bash
# 安装生产依赖
poetry install --only=main

# 安装所有依赖（包含开发依赖）
poetry install
```

#### 运行服务
```bash
# 使用poetry运行
poetry run sql-lint-service

# 或直接运行
python -m app.main
```

### 3. 使用pip (生产环境)

#### 安装依赖
```bash
# 从requirements.txt安装
pip install -r requirements.txt

# 或从requirements-dev.txt安装（包含开发工具）
pip install -r requirements-dev.txt
```

#### 运行服务
```bash
# 直接运行
python -m app.main

# 或使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | 5000 | 服务监听端口 |
| `LOG_LEVEL` | INFO | 日志级别 (DEBUG, INFO, WARNING, ERROR) |
| `LOG_DIR` | /app/logs | 日志目录 |
| `LOG_FILE` | sql-lint-service.log | 日志文件名 |
| `ENABLE_HOT_RELOAD` | true | 是否启用规则热加载 |
| `HOT_RELOAD_DEBOUNCE` | 0.5 | 热加载防抖时间（秒） |
| `SQL_DIALECT` | hive | SQL方言 (hive, spark, mysql, postgres等) |
| `TIMEOUT_SECONDS` | 5 | SQL检查超时时间（秒） |
| `MAX_SQL_SIZE_MB` | 10 | 最大SQL大小（MB） |
| `ENABLE_SAMPLING` | true | 是否启用采样检查 |
| `SAMPLING_THRESHOLD_KB` | 100 | 采样阈值（KB） |
| `CACHE_SIZE` | 100 | 缓存大小 |

## 健康检查

服务提供健康检查端点：
- `GET /health` - 服务健康状态
- `GET /monitor/status` - 监控状态（热加载、规则数量等）

### Docker健康检查
Docker容器已配置健康检查，自动监控服务状态。

## 监控和日志

### 日志位置
- 容器内: `/app/logs/sql-lint-service.log`
- 本地挂载: `./logs/sql-lint-service.log` (使用docker-compose时)

### 日志级别
通过`LOG_LEVEL`环境变量控制日志详细程度：
- `DEBUG`: 最详细，包含SQL解析细节
- `INFO`: 默认级别，包含服务操作信息
- `WARNING`: 仅警告和错误
- `ERROR`: 仅错误信息

## 规则管理

### 规则目录
- 本地: `./app/rules/`
- 容器内: `/app/app/rules/`

### 热加载
启用热加载后，修改规则文件会自动重新加载，无需重启服务。

### 添加新规则
1. 在`app/rules/`目录创建新的规则文件
2. 规则类必须继承`SQLGlotBaseRule`
3. 实现`check`方法
4. 服务会自动检测并加载新规则

## 性能优化

### 已实现的优化
1. **SQL解析**: 使用sqlglot替代sqlfluff，性能提升24.69倍
2. **缓存**: LRU缓存100个最近检查的SQL
3. **超时保护**: 5秒自动中断长处理
4. **采样检查**: 100KB以上SQL启用30%采样
5. **大小限制**: 拒绝>10MB超大SQL

### 调优建议
- 对于大量简单SQL: 增加`CACHE_SIZE`
- 对于复杂嵌套SQL: 增加`TIMEOUT_SECONDS`
- 对于大数据平台: 设置`SQL_DIALECT=spark`或`SQL_DIALECT=hive`

## 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口是否被占用
netstat -an | grep 5000

# 检查依赖是否安装
poetry check
```

#### 2. SQL解析失败
- 检查`SQL_DIALECT`设置是否正确
- 确认SQL语法符合目标方言
- 查看日志获取详细错误信息

#### 3. 规则不生效
- 确认规则文件在`app/rules/`目录
- 检查规则类是否正确继承`SQLGlotBaseRule`
- 查看服务日志确认规则加载成功

#### 4. 性能问题
- 检查SQL大小是否超过`MAX_SQL_SIZE_MB`
- 考虑启用采样检查 (`ENABLE_SAMPLING=true`)
- 调整缓存大小 (`CACHE_SIZE`)

### 日志分析
```bash
# 查看容器日志
docker logs sql-lint-service

# 查看详细日志
tail -f logs/sql-lint-service.log

# 过滤错误日志
grep -i "error\|exception" logs/sql-lint-service.log
```

## 升级说明

### 从sqlfluff迁移到sqlglot
本项目已从sqlfluff完全迁移到sqlglot，主要变化：

1. **性能**: 提升24.69倍
2. **兼容性**: API完全兼容，客户端无需修改
3. **功能**: 支持更多SQL方言和复杂语法
4. **依赖**: 移除sqlfluff，添加sqlglot

### 升级步骤
1. 更新依赖: `poetry update`
2. 重建Docker镜像: `./docker-build.sh --no-cache`
3. 重启服务

## 安全建议

1. **网络隔离**: 在生产环境中将服务部署在内网
2. **访问控制**: 通过反向代理添加认证
3. **资源限制**: 设置Docker资源限制 (CPU, 内存)
4. **日志轮转**: 配置日志轮转，避免磁盘写满
5. **定期更新**: 定期更新依赖和安全补丁

## 支持

- 问题反馈: 查看日志文件获取详细信息
- 功能请求: 通过issue跟踪系统提交
- 紧急支持: 联系系统管理员