#!/bin/bash

# RAG系统Docker快速启动脚本

set -e

echo "=== RAG系统Docker快速启动 ==="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info &> /dev/null; then
    echo "错误: Docker服务未运行，请启动Docker服务"
    exit 1
fi

echo "✓ Docker环境检查通过"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads data/exports logs volumes

# 设置权限
chmod -R 755 uploads data logs volumes

# 选择部署方式
echo ""
echo "请选择部署方式:"
echo "1) 完整部署 (包含Milvus，连接外部Ollama)"
echo "2) 仅部署RAG应用 (连接外部Milvus和Ollama)"
echo "3) 退出"
echo ""
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "开始完整部署..."
        echo "注意: 需要确保外部Ollama服务正在运行 (默认: localhost:11434)"
        echo ""
        read -p "确认外部Ollama服务正在运行? (y/N): " confirm
        
        if [[ $confirm =~ ^[Yy]$ ]]; then
            # 构建并启动服务
            docker-compose up -d --build
            
            echo ""
            echo "✓ 服务启动完成！"
            echo "访问地址: http://localhost:5000"
            echo ""
            echo "查看服务状态: docker-compose ps"
            echo "查看日志: docker-compose logs -f"
            echo "停止服务: docker-compose down"
        else
            echo "部署已取消"
            exit 0
        fi
        ;;
    2)
        echo "开始部署RAG应用..."
        echo "请确保以下服务正在运行:"
        echo "- Milvus: localhost:19530"
        echo "- Ollama: localhost:11434"
        echo ""
        read -p "确认外部服务正在运行? (y/N): " confirm
        
        if [[ $confirm =~ ^[Yy]$ ]]; then
            # 启动RAG应用
            docker-compose -f docker-compose.simple.yml up -d --build
            
            echo ""
            echo "✓ RAG应用启动完成！"
            echo "访问地址: http://localhost:5000"
            echo ""
            echo "查看服务状态: docker-compose -f docker-compose.simple.yml ps"
            echo "查看日志: docker-compose -f docker-compose.simple.yml logs -f"
            echo "停止服务: docker-compose -f docker-compose.simple.yml down"
        else
            echo "部署已取消"
            exit 0
        fi
        ;;
    3)
        echo "退出部署"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "=== 部署完成 ===" 