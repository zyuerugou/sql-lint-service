# SQL Lint Service Docker部署指南

## 概述

本文档介绍如何使用Docker部署SQL Lint Service。我们提供了多种部署方式，包括直接使用Docker命令、Docker Compose以及自动化脚本。

## 文件说明

- `Dockerfile` - 标准Docker构建文件
- `Dockerfile.optimized` - 优化版Dockerfile（多阶段构建，镜像更小）
- `docker-compose.yml` - Docker Compose配置文件
- `docker-build.sh` - Docker构建和运行自动化脚本
- `.env.example` - 环境变量配置示例
- `.dockerignore` - Docker忽略文件，确保镜像只包含运行所需文件
- `DOCKER-README.md` - 本文档

## 快速开始

### 方法1：使用自动化脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x docker-build.sh

# 构建镜像
./docker-build.sh build

# 运行容器
./docker-build.sh run

# 查看日志
./docker-build.sh logs

# 停止容器
./docker-build.sh stop

# 运行测试
./docker-build.sh test

# 查看帮助
./docker-build.sh help
```

### 方法2：使用Docker命令

```bash
# 构建镜像
docker build -t sql-lint-service:latest .

# 运行容器
docker run -d \
  --name sql-lint-service \
  -p 5000:5000 \
  -e ENABLE_HOT_RELOAD=true \
  -e HOT_RELOAD_DEBOUNCE=0.5 \
  -v $(pwd)/app/rules:/app/app/rules:ro \
  -v $(pwd)/logs:/app/logs \
  sql-lint-service:latest

# 查看容器状态
docker ps

# 查看日志
docker logs -f sql-lint-service

# 停止容器
docker stop sql-lint-service
docker rm sql-lint-service
```

### 方法3：使用Docker Compose

```bash
# 复制环境变量文件
cp .env.example .env

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_HOT_RELOAD` | `true` | 是否启用热加载 |
| `HOT_RELOAD_DEBOUNCE` | `0.5` | 热加载防抖间隔（秒） |
| `PORT` | `5000` | 服务端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 卷挂载

容器挂载了以下目录：

1. **规则目录**：`./app/rules:/app/app/rules:ro`
   - 只读挂载，用于热加载规则文件
   - 可以在宿主机修改规则文件，容器会自动重新加载

2. **日志目录**：`./logs:/app/logs`
   - 读写挂载，用于存储服务日志
   - 方便查看和备份日志文件

## 健康检查

容器配置了健康检查，可以通过以下方式检查服务状态：

```bash
# 使用Docker命令
docker inspect --format='{{.State.Health.Status}}' sql-lint-service

# 直接访问健康检查端点
curl http://localhost:5000/health
```

健康检查响应示例：
```json
{
  "status": "healthy",
  "service": "sql-lint-service",
  "rules_loaded": 3,
  "hot_reload_enabled": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

## 生产环境部署建议

### 1. 安全配置
```bash
# 使用非root用户运行
# 已在Dockerfile中配置了appuser用户

# 限制资源使用
docker run -d \
  --memory=512m \
  --cpus=1 \
  --name sql-lint-service \
  # ... 其他参数
```

### 2. 网络配置
```bash
# 使用自定义网络
docker network create sql-lint-network

docker run -d \
  --network sql-lint-network \
  --name sql-lint-service \
  # ... 其他参数
```

### 3. 日志管理
```bash
# 配置日志驱动和大小限制
docker run -d \
  --log-driver=json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  --name sql-lint-service \
  # ... 其他参数
```

### 4. 使用优化版镜像
```bash
# 使用多阶段构建的优化版Dockerfile
docker build -t sql-lint-service:optimized -f Dockerfile.optimized .
```

## 故障排除

### 1. 容器启动失败
```bash
# 查看详细错误信息
docker logs sql-lint-service

# 检查端口是否被占用
netstat -tulpn | grep :5000

# 检查文件权限
ls -la app/rules/
```

### 2. 热加载不工作
```bash
# 检查环境变量
docker exec sql-lint-service env | grep ENABLE_HOT_RELOAD

# 检查规则目录挂载
docker exec sql-lint-service ls -la /app/app/rules/

# 查看监控状态
curl http://localhost:5000/monitor/status
```

### 3. 服务不可访问
```bash
# 检查容器状态
docker ps

# 检查端口映射
docker port sql-lint-service

# 测试服务连通性
curl -v http://localhost:5000/health
```

### 4. 镜像构建失败
```bash
# 清理构建缓存
docker system prune -f

# 使用无缓存构建
docker build --no-cache -t sql-lint-service:latest .
```

## 性能优化

### 1. 镜像大小优化
- 使用多阶段构建（`Dockerfile.optimized`）
- 清理不必要的依赖和缓存
- 使用Alpine基础镜像（如果需要更小的镜像）

### 2. 启动时间优化
- 预构建基础镜像
- 使用镜像层缓存
- 优化依赖安装顺序

### 3. 运行时优化
- 配置适当的JVM参数（如果使用Java）
- 优化Python垃圾回收
- 配置连接池大小

## 监控和日志

### 1. 日志查看
```bash
# 实时查看日志
docker logs -f sql-lint-service

# 查看特定时间段的日志
docker logs --since 1h sql-lint-service

# 导出日志到文件
docker logs sql-lint-service > service.log
```

### 2. 监控端点
- `/health` - 健康检查
- `/monitor/status` - 监控状态
- `/rules` - 规则列表

### 3. 集成监控系统
可以将服务集成到以下监控系统：
- Prometheus + Grafana
- ELK Stack（Elasticsearch, Logstash, Kibana）
- Datadog
- New Relic

## 更新和升级

### 1. 更新服务
```bash
# 拉取最新代码
git pull

# 重新构建镜像
./docker-build.sh build

# 重启服务
./docker-build.sh restart
```

### 2. 升级依赖
```bash
# 更新pyproject.toml中的依赖版本

# 重新构建镜像
docker build --no-cache -t sql-lint-service:latest .
```

### 3. 数据迁移
如果需要迁移规则或配置：
```bash
# 备份规则
cp -r app/rules app/rules_backup_$(date +%Y%m%d)

# 恢复规则
cp -r app/rules_backup/* app/rules/
```

## 常见问题

### Q1: 如何修改规则文件？
A: 规则文件挂载为只读卷，需要在宿主机修改：
```bash
# 在宿主机编辑规则文件
vim app/rules/rule_ss01.py

# 容器会自动检测变化并重新加载
```

### Q2: 如何查看服务版本？
A: 服务目前没有版本API，可以通过以下方式查看：
```bash
# 查看镜像标签
docker images | grep sql-lint-service

# 查看构建信息
docker inspect sql-lint-service:latest | grep -A5 Labels
```

### Q3: 如何配置自定义端口？
A: 通过环境变量和端口映射：
```bash
docker run -d \
  -p 8080:5000 \
  -e PORT=5000 \
  --name sql-lint-service \
  sql-lint-service:latest
```

### Q4: 如何备份和恢复数据？
A: 主要需要备份规则文件：
```bash
# 备份
tar -czf rules_backup_$(date +%Y%m%d).tar.gz app/rules/

# 恢复
tar -xzf rules_backup_20240101.tar.gz -C ./
```

## 支持

如有问题，请参考：
1. [项目README](../README.md)
2. [测试文档](../tests/README.md)
3. 创建GitHub Issue
4. 查看容器日志：`docker logs sql-lint-service`