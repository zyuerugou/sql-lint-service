#!/bin/bash
# Docker助手脚本 - 支持build、run、test等命令

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认值
IMAGE_NAME="sql-lint-service"
TAG="latest"
VERSION="0.2.0"
POETRY_VERSION="2.3.1"
PORT=5000

# 显示帮助信息
show_help() {
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  build       构建Docker镜像"
    echo "  run         运行Docker容器"
    echo "  test        测试Docker容器"
    echo "  clean       清理Docker资源"
    echo "  help        显示此帮助信息"
    echo ""
    echo "构建选项 (用于 build 命令):"
    echo "  -n, --name NAME       镜像名称 (默认: $IMAGE_NAME)"
    echo "  -t, --tag TAG         镜像标签 (默认: $TAG)"
    echo "  -v, --version VERSION 应用版本 (默认: $VERSION)"
    echo "  -p, --poetry VERSION  Poetry版本 (默认: $POETRY_VERSION)"
    echo "  --no-cache            构建时不使用缓存"
    echo ""
    echo "运行选项 (用于 run 命令):"
    echo "  -p, --port PORT       映射端口 (默认: $PORT)"
    echo "  -d, --detach          后台运行"
    echo "  --name NAME           容器名称"
    echo "  --hot-reload          启用规则热加载"
    echo ""
    echo "示例:"
    echo "  $0 build"
    echo "  $0 build --no-cache -t v1.0.0"
    echo "  $0 run -p 8080:5000"
    echo "  $0 run --hot-reload"
    echo "  $0 test"
    echo "  $0 clean"
}

# 构建镜像
build_image() {
    local BUILD_ARGS=""
    
    # 解析构建参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--name)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -p|--poetry)
                POETRY_VERSION="$2"
                shift 2
                ;;
            --no-cache)
                BUILD_ARGS="--no-cache"
                shift
                ;;
            *)
                echo -e "${RED}错误: 未知构建选项 $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${GREEN}开始构建Docker镜像...${NC}"
    echo "镜像名称: $IMAGE_NAME"
    echo "镜像标签: $IMAGE_NAME:$TAG"
    echo "应用版本: $VERSION"
    echo "Poetry版本: $POETRY_VERSION"
    echo "构建参数: $BUILD_ARGS"
    echo ""
    
    # 检查Docker是否可用
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker未安装或不在PATH中${NC}"
        exit 1
    fi
    
    # 构建镜像
    echo -e "${YELLOW}构建镜像中...${NC}"
    docker build $BUILD_ARGS \
        --build-arg VERSION=$VERSION \
        --build-arg POETRY_VERSION=$POETRY_VERSION \
        -t $IMAGE_NAME:$TAG \
        -t $IMAGE_NAME:latest \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 镜像构建成功！${NC}"
        echo ""
        echo "镜像信息:"
        docker images $IMAGE_NAME:$TAG --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    else
        echo -e "${RED}❌ 镜像构建失败${NC}"
        exit 1
    fi
}

# 运行容器
run_container() {
    local DETACH=""
    local CONTAINER_NAME=""
    local VOLUME_MOUNT=""
    local RUN_PORT="$PORT"
    
    # 解析运行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                RUN_PORT="$2"
                shift 2
                ;;
            -d|--detach)
                DETACH="-d"
                shift
                ;;
            --name)
                CONTAINER_NAME="--name $2"
                shift 2
                ;;
            --hot-reload)
                VOLUME_MOUNT="-v $(pwd)/app/rules:/app/app/rules:ro"
                shift
                ;;
            *)
                echo -e "${RED}错误: 未知运行选项 $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${GREEN}启动Docker容器...${NC}"
    echo "镜像: $IMAGE_NAME:$TAG"
    echo "端口映射: $RUN_PORT:5000"
    echo "容器名称: ${CONTAINER_NAME:-自动生成}"
    echo "热加载: ${VOLUME_MOUNT:+已启用}"
    echo ""
    
    # 检查镜像是否存在
    if ! docker image inspect $IMAGE_NAME:$TAG &> /dev/null; then
        echo -e "${YELLOW}镜像不存在，正在构建...${NC}"
        build_image
    fi
    
    # 运行容器
    echo -e "${YELLOW}启动容器中...${NC}"
    docker run --rm $DETACH $CONTAINER_NAME $VOLUME_MOUNT \
        -p $RUN_PORT:5000 \
        $IMAGE_NAME:$TAG
    
    if [ $? -eq 0 ]; then
        if [ -z "$DETACH" ]; then
            echo -e "${GREEN}✅ 容器已启动（前台模式）${NC}"
        else
            echo -e "${GREEN}✅ 容器已启动（后台模式）${NC}"
            echo "查看日志: docker logs $(docker ps -lq --format '{{.Names}}')"
            echo "停止容器: docker stop $(docker ps -lq --format '{{.Names}}')"
        fi
        echo ""
        echo "测试服务:"
        echo "  curl http://localhost:$RUN_PORT/health"
        echo "  curl -X POST http://localhost:$RUN_PORT/lint -H 'Content-Type: application/json' -d '{\"sql\": \"SELECT * FROM users\"}'"
    else
        echo -e "${RED}❌ 容器启动失败${NC}"
        exit 1
    fi
}

# 测试容器
test_container() {
    echo -e "${GREEN}测试Docker容器...${NC}"
    
    # 检查镜像是否存在
    if ! docker image inspect $IMAGE_NAME:$TAG &> /dev/null; then
        echo -e "${YELLOW}镜像不存在，正在构建...${NC}"
        build_image
    fi
    
    echo -e "${YELLOW}运行健康检查测试...${NC}"
    
    # 启动临时测试容器
    docker run --rm --name sql-lint-test-$RANDOM \
        -d \
        -p 5999:5000 \
        $IMAGE_NAME:$TAG
    
    # 等待服务启动
    echo "等待服务启动..."
    sleep 5
    
    # 测试健康检查
    echo -e "${BLUE}测试健康检查端点...${NC}"
    if curl -s http://localhost:5999/health | grep -q "success"; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"
    else
        echo -e "${RED}❌ 健康检查失败${NC}"
        docker stop sql-lint-test-$RANDOM &> /dev/null
        exit 1
    fi
    
    # 测试lint端点
    echo -e "${BLUE}测试lint端点...${NC}"
    RESPONSE=$(curl -s -X POST http://localhost:5999/lint \
        -H 'Content-Type: application/json' \
        -d '{"sql": "SELECT * FROM users"}')
    
    if echo "$RESPONSE" | grep -q "violations"; then
        echo -e "${GREEN}✅ lint端点测试通过${NC}"
        echo "响应示例:"
        echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${RED}❌ lint端点测试失败${NC}"
        echo "响应: $RESPONSE"
    fi
    
    # 停止测试容器
    docker stop sql-lint-test-$RANDOM &> /dev/null
    echo -e "${GREEN}✅ 所有测试完成${NC}"
}

# 清理资源
clean_resources() {
    echo -e "${GREEN}清理Docker资源...${NC}"
    
    # 停止并删除所有相关容器
    echo "停止相关容器..."
    docker ps -a --filter "ancestor=$IMAGE_NAME:$TAG" --format "{{.ID}}" | xargs -r docker stop
    docker ps -a --filter "ancestor=$IMAGE_NAME:$TAG" --format "{{.ID}}" | xargs -r docker rm
    
    # 删除镜像
    echo "删除镜像..."
    docker rmi $IMAGE_NAME:$TAG 2>/dev/null || true
    docker rmi $IMAGE_NAME:latest 2>/dev/null || true
    
    # 清理悬空镜像
    echo "清理悬空镜像..."
    docker image prune -f
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    COMMAND="$1"
    shift
    
    case $COMMAND in
        build)
            build_image "$@"
            ;;
        run)
            run_container "$@"
            ;;
        test)
            test_container "$@"
            ;;
        clean)
            clean_resources "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知命令 '$COMMAND'${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"