# RAG系统Docker部署指南

## 概述

本项目支持Docker容器化部署，包含完整的RAG（检索增强生成）系统，包括：
- RAG Web应用（Flask）
- Milvus向量数据库
- **外部Ollama大语言模型服务**（需要单独部署）

## 部署方式

### 方式一：完整部署（推荐）

使用docker-compose启动RAG应用和Milvus，连接外部Ollama服务：

```bash
# 1. 确保外部Ollama服务正在运行
# 例如: ollama serve (在宿主机上运行)

# 2. 构建并启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f rag-web

# 5. 停止服务
docker-compose down
```

### 方式二：仅部署RAG应用

如果Milvus和Ollama服务都已经在外部运行，可以使用简化版部署：

```bash
# 1. 确保外部服务正在运行
# - Milvus: localhost:19530
# - Ollama: localhost:11434

# 2. 启动RAG应用
docker-compose -f docker-compose.simple.yml up -d

# 3. 查看状态
docker-compose -f docker-compose.simple.yml ps
```

### 方式三：手动构建

```bash
# 1. 构建镜像
docker build -t rag-system .

# 2. 运行容器
docker run -d \
  --name rag-web \
  -p 5000:5000 \
  -e MILVUS_HOST=host.docker.internal \
  -e MILVUS_PORT=19530 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --add-host host.docker.internal:host-gateway \
  rag-system
```

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| MILVUS_HOST | localhost | Milvus服务地址 |
| MILVUS_PORT | 19530 | Milvus服务端口 |
| OLLAMA_HOST | http://host.docker.internal:11434 | **外部Ollama服务地址** |
| OLLAMA_MODEL | deepseek-r1:14b | 使用的语言模型 |
| COLLECTION_NAME | finance_knowledge | 向量数据库集合名 |
| FLASK_ENV | production | Flask运行环境 |
| LOG_LEVEL | INFO | 日志级别 |

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| RAG Web应用 | 5000 | Web界面 |
| Milvus | 19530 | 向量数据库API |
| Milvus管理 | 9091 | 健康检查端口 |
| **外部Ollama** | **11434** | **大语言模型API** |

## 外部Ollama服务配置

### 1. 安装Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# 下载安装包: https://ollama.ai/download
```

### 2. 启动Ollama服务

```bash
# 启动服务
ollama serve

# 下载模型（首次使用）
ollama pull deepseek-r1:14b
```

### 3. 验证服务

```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 测试模型
ollama run deepseek-r1:14b "Hello, world!"
```

### 4. Docker环境中的连接配置

在Docker环境中，RAG应用通过以下方式连接外部Ollama服务：

```bash
# 方式一：使用host.docker.internal（推荐）
OLLAMA_HOST=http://host.docker.internal:11434

# 方式二：使用宿主机IP
OLLAMA_HOST=http://172.17.0.1:11434

# 方式三：使用宿主机网络
docker run --network host rag-system
```

## 数据持久化

以下目录会被挂载到宿主机：

- `./uploads`: 上传的文件
- `./data`: 系统数据
- `./logs`: 日志文件
- `./volumes`: Docker卷数据

## 健康检查

系统包含健康检查机制：

```bash
# 检查容器健康状态
docker ps

# 查看健康检查日志
docker inspect rag-web | grep -A 10 Health
```

## 故障排除

### 1. 服务启动失败

```bash
# 查看详细日志
docker-compose logs rag-web

# 检查服务依赖
docker-compose ps
```

### 2. 连接超时

确保依赖服务正在运行：

```bash
# 检查Milvus
curl http://localhost:9091/healthz

# 检查Ollama
curl http://localhost:11434/api/tags
```

### 3. Ollama连接问题

```bash
# 检查Ollama服务状态
ps aux | grep ollama

# 重启Ollama服务
pkill ollama
ollama serve

# 检查模型是否可用
ollama list

# 检查Docker容器是否能访问宿主机
docker exec rag-web curl http://host.docker.internal:11434/api/tags
```

### 4. 权限问题

```bash
# 确保目录权限正确
chmod -R 755 uploads data logs volumes
```

## 性能优化

### 1. 资源限制

在docker-compose.yml中添加资源限制：

```yaml
services:
  rag-web:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### 2. Ollama优化

```bash
# 设置Ollama环境变量
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_ORIGINS=*

# 使用GPU加速（如果可用）
export OLLAMA_GPU_LAYERS=35
```

### 3. 向量数据库优化

Milvus配置已针对生产环境优化，包括：
- 嵌入式etcd
- 本地存储
- 自动索引

## 监控

### 1. 日志监控

```bash
# 实时查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f rag-web
```

### 2. 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 3. Ollama监控

```bash
# 查看Ollama进程
ps aux | grep ollama

# 查看模型使用情况
ollama list
```

## 备份和恢复

### 1. 数据备份

```bash
# 备份数据目录
tar -czf rag-backup-$(date +%Y%m%d).tar.gz uploads/ data/ logs/

# 备份Docker卷
docker run --rm -v rag-autogen_milvus_data:/data -v $(pwd):/backup alpine tar czf /backup/milvus-backup.tar.gz -C /data .

# 备份Ollama模型（可选）
ollama list > ollama-models.txt
```

### 2. 数据恢复

```bash
# 恢复数据目录
tar -xzf rag-backup-20241201.tar.gz

# 恢复Docker卷
docker run --rm -v rag-autogen_milvus_data:/data -v $(pwd):/backup alpine tar xzf /backup/milvus-backup.tar.gz -C /data
```

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 清理旧镜像
docker image prune -f

# 5. 更新Ollama模型（可选）
ollama pull deepseek-r1:14b
```

## 安全建议

1. 在生产环境中修改默认密码
2. 使用HTTPS代理
3. 限制网络访问
4. 定期更新镜像
5. 监控系统资源使用
6. **保护Ollama服务访问权限**

## 支持

如遇到问题，请检查：
1. Docker和Docker Compose版本
2. 系统资源是否充足
3. 网络连接是否正常
4. 端口是否被占用
5. **外部Ollama服务是否正常运行**

## 配置说明

所有 Milvus/Ollama 配置均通过环境变量和 config/settings.py 统一管理。
- rag-web 连接 milvus-standalone:19530
- 外部 Ollama 服务通过 OLLAMA_HOST 环境变量指定

## 依赖说明

- requirements.txt 已包含所有依赖，无需手动安装 PyPDF2。
- 文档处理仅需 pdfplumber。 