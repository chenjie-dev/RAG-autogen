#!/bin/bash

# Docker入口脚本
# 等待依赖服务启动，然后启动RAG应用

set -e

echo "=== RAG系统Docker启动脚本 ==="

# 等待Milvus服务启动
echo "等待Milvus服务启动..."
until nc -z $MILVUS_HOST $MILVUS_PORT; do
    echo "Milvus服务未就绪，等待5秒..."
    sleep 5
done
echo "✓ Milvus服务已就绪"

# 检查外部Ollama服务（可选）
echo "检查外部Ollama服务..."
OLLAMA_HOST_CLEAN=$(echo $OLLAMA_HOST | sed 's|http://||' | sed 's|https://||')
OLLAMA_HOST_ONLY=$(echo $OLLAMA_HOST_CLEAN | cut -d: -f1)
OLLAMA_PORT_ONLY=$(echo $OLLAMA_HOST_CLEAN | cut -d: -f2)

if nc -z $OLLAMA_HOST_ONLY $OLLAMA_PORT_ONLY 2>/dev/null; then
    echo "✓ 外部Ollama服务已就绪"
else
    echo "⚠ 外部Ollama服务未检测到，请确保服务正在运行: $OLLAMA_HOST"
    echo "继续启动应用，但问答功能可能不可用..."
fi

# 创建必要的目录
mkdir -p uploads data/exports logs volumes

# 设置权限
chmod +x start.py start_web_ui.py

echo "=== 启动RAG Web应用 ==="
echo "访问地址: http://localhost:5000"
echo "注意: 请确保外部Ollama服务正在运行: $OLLAMA_HOST"

# 启动应用
exec python start_web_ui.py 