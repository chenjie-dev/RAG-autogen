#!/bin/bash

# AutoGen智能体RAG系统部署脚本
# =====================================
# 
# 功能说明:
# - 自动安装依赖包
# - 检查系统环境
# - 启动必要服务
# - 部署AutoGen智能体系统
# 
# 使用方法:
#   chmod +x deploy_autogen.sh
#   ./deploy_autogen.sh [mode]
# 
# 部署模式:
#   full: 完整部署（包含所有依赖和服务）
#   simple: 简单部署（仅部署应用）
#   docker: Docker部署
#   test: 测试部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_system_requirements() {
    print_info "检查系统要求..."
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python版本: $PYTHON_VERSION"
    else
        print_error "Python3未安装，请先安装Python3"
        exit 1
    fi
    
    # 检查pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3已安装"
    else
        print_error "pip3未安装，请先安装pip3"
        exit 1
    fi
    
    # 检查Docker（可选）
    if command -v docker &> /dev/null; then
        print_success "Docker已安装"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker未安装，将跳过Docker相关功能"
        DOCKER_AVAILABLE=false
    fi
}

# 安装Python依赖
install_python_dependencies() {
    print_info "安装Python依赖包..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装基础依赖
    pip3 install -r requirements.txt
    
    # 安装AutoGen相关依赖
    pip3 install pyautogen>=0.2.0 openai>=1.0.0
    
    print_success "Python依赖安装完成"
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    
    # 检查Ollama服务
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama服务正在运行"
    else
        print_warning "Ollama服务未运行，请启动Ollama服务"
        print_info "启动命令: ollama serve"
    fi
    
    # 检查Milvus服务
    if python3 -c "from pymilvus import connections; connections.connect(host='localhost', port=19530); connections.disconnect()" 2>/dev/null; then
        print_success "Milvus服务正在运行"
    else
        print_warning "Milvus服务未运行，请启动Milvus服务"
        print_info "启动命令: docker run -d --name milvus-standalone -p 19530:19530 milvusdb/milvus:v2.3.11"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p uploads
    mkdir -p data
    mkdir -p volumes
    
    print_success "目录创建完成"
}

# 配置环境变量
setup_environment() {
    print_info "配置环境变量..."
    
    if [ ! -f .env ]; then
        cat > .env << EOF
# Milvus向量数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
COLLECTION_NAME=finance_knowledge

# Ollama大语言模型配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:14b

# AutoGen配置
AUTOGEN_CONFIG_LIST=[{"model": "ollama", "base_url": "http://localhost:11434"}]
AUTOGEN_MAX_ROUNDS=10
AUTOGEN_TEMPERATURE=0.7

# Web UI配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/autogen_system.log

# 数据目录配置
DATA_DIR=data
UPLOADS_DIR=uploads
EXPORTS_DIR=data/exports

# 部署环境配置
FLASK_ENV=production
EOF
        print_success "环境配置文件创建完成"
    else
        print_info "环境配置文件已存在"
    fi
}

# 启动Docker服务
start_docker_services() {
    if [ "$DOCKER_AVAILABLE" = true ]; then
        print_info "启动Docker服务..."
        
        # 启动Milvus
        if ! docker ps | grep -q milvus-standalone; then
            docker run -d --name milvus-standalone \
                -p 19530:19530 \
                -p 9091:9091 \
                milvusdb/milvus:v2.3.11
            print_success "Milvus服务启动完成"
        else
            print_info "Milvus服务已在运行"
        fi
        
        # 等待服务启动
        sleep 10
    fi
}

# 测试系统
test_system() {
    print_info "测试AutoGen智能体系统..."
    
    if python3 test_autogen.py basic; then
        print_success "系统测试通过"
    else
        print_error "系统测试失败"
        exit 1
    fi
}

# 启动应用
start_application() {
    print_info "启动AutoGen智能体系统..."
    
    echo ""
    echo "请选择启动模式:"
    echo "1) 命令行模式"
    echo "2) Web界面模式"
    echo "3) 退出"
    echo ""
    read -p "请输入选择 (1-3): " choice
    
    case $choice in
        1)
            print_info "启动命令行模式..."
            python3 start_autogen.py cli
            ;;
        2)
            print_info "启动Web界面模式..."
            python3 start_autogen.py web
            ;;
        3)
            print_info "退出部署"
            exit 0
            ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac
}

# Docker部署
deploy_docker() {
    if [ "$DOCKER_AVAILABLE" = false ]; then
        print_error "Docker未安装，无法进行Docker部署"
        exit 1
    fi
    
    print_info "开始Docker部署..."
    
    # 构建镜像
    docker build -t rag-autogen:latest .
    
    # 启动容器
    docker run -d --name rag-autogen-app \
        -p 5000:5000 \
        -v $(pwd)/uploads:/app/uploads \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        rag-autogen:latest
    
    print_success "Docker部署完成"
    print_info "访问地址: http://localhost:5000"
}

# 完整部署
deploy_full() {
    print_info "开始完整部署..."
    
    check_system_requirements
    install_python_dependencies
    create_directories
    setup_environment
    start_docker_services
    check_services
    test_system
    start_application
}

# 简单部署
deploy_simple() {
    print_info "开始简单部署..."
    
    check_system_requirements
    install_python_dependencies
    create_directories
    setup_environment
    check_services
    start_application
}

# 测试部署
deploy_test() {
    print_info "开始测试部署..."
    
    check_system_requirements
    install_python_dependencies
    create_directories
    setup_environment
    test_system
}

# 主函数
main() {
    echo "=========================================="
    echo "🚀 AutoGen智能体RAG系统部署脚本"
    echo "=========================================="
    
    MODE=${1:-full}
    
    case $MODE in
        full)
            deploy_full
            ;;
        simple)
            deploy_simple
            ;;
        docker)
            deploy_docker
            ;;
        test)
            deploy_test
            ;;
        *)
            echo "使用方法: $0 [full|simple|docker|test]"
            echo ""
            echo "部署模式:"
            echo "  full    - 完整部署（包含所有依赖和服务）"
            echo "  simple  - 简单部署（仅部署应用）"
            echo "  docker  - Docker部署"
            echo "  test    - 测试部署"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 