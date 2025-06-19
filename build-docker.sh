#!/bin/bash

# 设置错误时退出
set -e

echo "开始构建 RAG Web 镜像..."

# 构建镜像
docker build -t rag-autogen-rag-web:latest .

echo "镜像构建完成！"
echo "镜像名称: rag-autogen-rag-web:latest"

# 显示镜像信息
echo -e "\n镜像详情:"
docker images rag-autogen-rag-web:latest 

# 更新K8S部署
echo -e "\n更新K8S部署..."
kubectl rollout restart deployment rag-web -n rag-system