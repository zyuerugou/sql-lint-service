#!/bin/bash

# SQL Lint Service Docker构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    print_message "Docker已安装"
}

# 检查Docker Compose是否安装
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose未安装，将使用docker命令"
        DOCKER_COMPOSE=false
    else
        DOCKER_COMPOSE=true
        print_message "Docker Compose已安装"
    fi
}

# 从pyproject.toml读取版本号
read_version() {
    if [ -f "pyproject.toml" ]; then
        # 尝试从pyproject.toml读取版本号
        local version=$(grep -E '^version =' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/' | tr -d '[:space:]')
        if [ -n "$version" ]; then
            echo "$version"
            return 0
        fi
    fi
    echo "0.1.0"
}

# 构建镜像
build_image() {
    local version=$(read_version)
    local tag=${1:-"sql-lint-service:$version"}

    print_message "开始构建Docker镜像: $tag (版本: $version)"

    # 构建镜像，传递版本号参数
    docker build \
        --build-arg VERSION="$version" \
        -t "$tag" \
        .

    # 同时打上latest标签
    if [[ "$tag" == "sql-lint-service:"* ]]; then
        docker tag "$tag" "sql-lint-service:latest"
        print_message "同时标记为: sql-lint-service:latest"
    fi

    if [ $? -eq 0 ]; then
        print_message "Docker镜像构建成功: $tag"
        print_message "同时标记为: sql-lint-service:latest"
    else
        print_error "Docker镜像构建失败"
        exit 1
    fi
}

# 运行容器
run_container() {
    local tag=${1:-"sql-lint-service:latest"}
    local port=${2:-"5000"}

    print_message "启动容器，映射端口: $port"

    if [ "$DOCKER_COMPOSE" = true ]; then
        docker-compose up -d
    else
        docker run -d \
            --name sql-lint-service \
            -p "$port:5000" \
            -e ENABLE_HOT_RELOAD=true \
            -e HOT_RELOAD_DEBOUNCE=0.5 \
            -v "$(pwd)/app/rules:/app/app/rules:ro" \
            -v "$(pwd)/logs:/app/logs" \
            "$tag"
    fi

    if [ $? -eq 0 ]; then
        print_message "容器启动成功"
        print_message "服务地址: http://localhost:$port"
        print_message "查看日志: docker logs -f sql-lint-service"
    else
        print_error "容器启动失败"
        exit 1
    fi
}

# 停止容器
stop_container() {
    print_message "停止容器..."

    if [ "$DOCKER_COMPOSE" = true ]; then
        docker-compose down
    else
        docker stop sql-lint-service 2>/dev/null || true
        docker rm sql-lint-service 2>/dev/null || true
    fi

    print_message "容器已停止"
}

# 清理镜像
cleanup() {
    print_message "清理未使用的Docker资源..."
    docker system prune -f
}

# 显示帮助
show_help() {
    echo "SQL Lint Service Docker管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  build [tag]     构建Docker镜像（默认从pyproject.toml读取版本号）"
    echo "  run [tag] [port] 运行容器（默认使用最新版本, 端口: 5000）"
    echo "  stop            停止容器"
    echo "  restart         重启容器"
    echo "  logs            查看容器日志"
    echo "  status          查看容器状态"
    echo "  test            运行测试"
    echo "  cleanup         清理Docker资源"
    echo "  help            显示此帮助信息"
    echo ""
    echo "版本管理:"
    echo "  构建时会自动从pyproject.toml读取版本号"
    echo "  同时创建版本标签和latest标签"
    echo ""
    echo "示例:"
    echo "  $0 build                    构建当前版本"
    echo "  $0 build sql-lint-service:v1.0 指定标签构建"
    echo "  $0 run                      运行最新版本"
    echo "  $0 run sql-lint-service:0.1.0 运行指定版本"
    echo "  $0 stop                     停止容器"
}

# 查看日志
show_logs() {
    if [ "$DOCKER_COMPOSE" = true ]; then
        docker-compose logs -f
    else
        docker logs -f sql-lint-service
    fi
}

# 查看状态
show_status() {
    print_message "容器状态:"
    docker ps -a --filter "name=sql-lint-service"

    print_message "\n镜像信息:"
    docker images | grep sql-lint-service
}

# 运行测试
run_tests() {
    print_message "运行测试..."

    # 构建测试镜像
    docker build -t sql-lint-test -f Dockerfile .

    # 运行测试
    docker run --rm \
        -e ENABLE_HOT_RELOAD=false \
        sql-lint-test \
        sh -c "python -m pytest tests/test_set_statements.py tests/test_multiple_statements.py -v && \
               python -m pytest tests/test_rules_integration.py -v"
}

# 重启容器
restart_container() {
    stop_container
    run_container "$@"
}

# 主函数
main() {
    check_docker
    check_docker_compose

    case "$1" in
        build)
            build_image "$2"
            ;;
        run)
            run_container "$2" "$3"
            ;;
        stop)
            stop_container
            ;;
        restart)
            restart_container "$2" "$3"
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        test)
            run_tests
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"