# SQL Lint Service Docker运行脚本 (简化PowerShell版本)

# 项目配置
$IMAGE_NAME = "sql-lint-service"
$TAG = "latest"
$CONTAINER_NAME = "sql-lint-service"
$PORT = 5000
$RULES_DIR = ".\app\rules"
$LOGS_DIR = ".\logs"

# 显示帮助
function Show-Help {
    Write-Host "SQL Lint Service Docker运行脚本"
    Write-Host "用法: .\docker-run-simple.ps1 [命令]"
    Write-Host ""
    Write-Host "命令:"
    Write-Host "  build    - 构建Docker镜像"
    Write-Host "  start    - 启动服务"
    Write-Host "  stop     - 停止服务"
    Write-Host "  restart  - 重启服务"
    Write-Host "  logs     - 查看日志"
    Write-Host "  status   - 查看状态"
    Write-Host "  clean    - 清理资源"
    Write-Host "  help     - 显示帮助"
    Write-Host ""
    Write-Host "预设:"
    Write-Host "  端口: $PORT"
    Write-Host "  规则目录: $RULES_DIR"
    Write-Host "  日志目录: $LOGS_DIR"
}

# 构建镜像
function Build-Image {
    Write-Host "构建Docker镜像..."
    docker build -t "${IMAGE_NAME}:${TAG}" .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 镜像构建成功"
    } else {
        Write-Host "❌ 镜像构建失败"
        exit 1
    }
}

# 启动服务
function Start-Service {
    Write-Host "启动服务..."
    
    # 检查目录
    if (-not (Test-Path $RULES_DIR)) {
        Write-Host "创建规则目录: $RULES_DIR"
        New-Item -ItemType Directory -Force -Path $RULES_DIR | Out-Null
    }
    
    if (-not (Test-Path $LOGS_DIR)) {
        Write-Host "创建日志目录: $LOGS_DIR"
        New-Item -ItemType Directory -Force -Path $LOGS_DIR | Out-Null
    }
    
    # 检查镜像
    try {
        docker image inspect "${IMAGE_NAME}:${TAG}" | Out-Null
    } catch {
        Write-Host "镜像不存在，正在构建..."
        Build-Image
    }
    
    # 停止已存在的容器
    $existing = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
    if ($existing -contains $CONTAINER_NAME) {
        Write-Host "停止现有容器..."
        docker stop $CONTAINER_NAME 2>$null
        docker rm $CONTAINER_NAME 2>$null
    }
    
    # 启动容器
    Write-Host "启动容器..."
    $rulesPath = Resolve-Path $RULES_DIR
    $logsPath = Resolve-Path $LOGS_DIR
    
    docker run -d `
        --name $CONTAINER_NAME `
        -p "${PORT}:5000" `
        -v "${rulesPath}:/app/app/rules:ro" `
        -v "${logsPath}:/app/logs" `
        -e "ENABLE_HOT_RELOAD=true" `
        -e "LOG_LEVEL=INFO" `
        -e "SQL_DIALECT=hive" `
        --restart unless-stopped `
        "${IMAGE_NAME}:${TAG}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 服务启动成功"
        Write-Host "URL: http://localhost:$PORT"
        Write-Host "健康检查: http://localhost:$PORT/health"
    } else {
        Write-Host "❌ 服务启动失败"
        exit 1
    }
}

# 停止服务
function Stop-Service {
    Write-Host "停止服务..."
    docker stop $CONTAINER_NAME 2>$null
    docker rm $CONTAINER_NAME 2>$null
    Write-Host "✅ 服务已停止"
}

# 重启服务
function Restart-Service {
    Stop-Service
    Start-Sleep -Seconds 2
    Start-Service
}

# 查看日志
function Show-Logs {
    Write-Host "查看日志..."
    docker logs -f $CONTAINER_NAME
}

# 查看状态
function Show-Status {
    Write-Host "服务状态:"
    docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
}

# 清理资源
function Clean-Resources {
    Write-Host "清理资源..."
    docker stop $CONTAINER_NAME 2>$null
    docker rm $CONTAINER_NAME 2>$null
    docker rmi "${IMAGE_NAME}:${TAG}" 2>$null
    docker image prune -f 2>$null
    Write-Host "✅ 清理完成"
}

# 主函数
if ($args.Count -eq 0) {
    Show-Help
    exit 0
}

switch ($args[0]) {
    "build" { Build-Image }
    "start" { Start-Service }
    "stop" { Stop-Service }
    "restart" { Restart-Service }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "clean" { Clean-Resources }
    "help" { Show-Help }
    default {
        Write-Host "错误: 未知命令 '$($args[0])'"
        Show-Help
        exit 1
    }
}