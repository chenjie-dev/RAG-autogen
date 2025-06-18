# 环境变量配置示例

## 概述

本文档提供了金融知识RAG问答系统的环境变量配置示例，帮助用户正确配置系统。

## 配置文件

### 1. 创建环境变量文件

复制以下内容到 `.env` 文件：

```bash
# 金融知识RAG问答系统 - 环境变量配置
# ============================================

# Milvus向量数据库配置
# ====================
MILVUS_HOST=localhost
MILVUS_PORT=19530
COLLECTION_NAME=finance_knowledge

# Ollama大语言模型配置
# ====================
# 本地部署时使用
OLLAMA_BASE_URL=http://localhost:11434

# Docker部署时使用（连接外部Ollama服务）
# OLLAMA_HOST=http://host.docker.internal:11434

# 使用的模型名称
OLLAMA_MODEL=deepseek-r1:14b

# Web UI配置
# ==========
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False

# 日志配置
# ========
LOG_LEVEL=INFO
LOG_FILE=logs/rag_system.log

# 数据目录配置
# ============
DATA_DIR=data
UPLOADS_DIR=uploads
EXPORTS_DIR=data/exports

# 部署环境配置
# ============
# 生产环境
FLASK_ENV=production

# 开发环境
# FLASK_ENV=development
```

## 配置说明

- 所有配置优先通过环境变量，代码统一读取 config/settings.py。
- requirements.txt 已包含所有依赖，无需手动安装 PyPDF2。

### 本地部署配置

```bash
# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:14b
```

### Docker部署配置

#### 完整部署（包含Milvus）
```bash
# Milvus配置（Docker内部）
MILVUS_HOST=milvus-standalone
MILVUS_PORT=19530

# Ollama配置（外部服务）
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=deepseek-r1:14b
```

#### 仅部署RAG应用
```bash
# Milvus配置（外部服务）
MILVUS_HOST=host.docker.internal
MILVUS_PORT=19530

# Ollama配置（外部服务）
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=deepseek-r1:14b
```

## 配置优先级

系统按以下优先级读取配置：

1. **环境变量** - 最高优先级
2. **.env文件** - 次优先级
3. **默认值** - 最低优先级

## 配置验证

### 1. 检查配置是否正确加载

```python
from config.settings import OLLAMA_BASE_URL, MILVUS_HOST
print(f"Ollama地址: {OLLAMA_BASE_URL}")
print(f"Milvus地址: {MILVUS_HOST}")
```

### 2. 测试服务连接

```bash
# 测试Ollama连接
curl http://localhost:11434/api/tags

# 测试Milvus连接
curl http://localhost:9091/healthz
```

## 常见配置问题

### 1. Docker容器无法访问宿主机服务

**问题**: 容器内无法连接到宿主机上的Ollama服务

**解决方案**:
```bash
# 使用host.docker.internal
OLLAMA_HOST=http://host.docker.internal:11434

# 或在docker-compose.yml中添加
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### 2. 端口冲突

**问题**: 端口被占用

**解决方案**:
```bash
# 修改端口配置
WEB_PORT=5001
MILVUS_PORT=19531
```

### 3. 权限问题

**问题**: 无法访问数据目录

**解决方案**:
```bash
# 设置正确的权限
chmod -R 755 uploads data logs volumes
```

## 生产环境配置

### 1. 安全配置

```bash
# 生产环境设置
FLASK_ENV=production
WEB_DEBUG=False
LOG_LEVEL=WARNING
```

### 2. 性能配置

```bash
# 优化配置
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=100MB
```

### 3. 监控配置

```bash
# 启用详细日志
LOG_LEVEL=DEBUG
LOG_FILE=logs/rag_system.log
```

## 配置更新

### 1. 更新配置后重启服务

```bash
# Docker部署
docker-compose restart

# 本地部署
# 重新启动Python进程
```

### 2. 验证配置生效

```bash
# 检查环境变量
env | grep -E "(OLLAMA|MILVUS|FLASK)"

# 查看应用日志
docker-compose logs rag-web
```

## 支持

如遇到配置问题，请检查：

1. 环境变量名称是否正确
2. 服务地址和端口是否可访问
3. 网络连接是否正常
4. 权限设置是否正确 