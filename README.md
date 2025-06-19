# 金融知识RAG问答系统

一个基于RAG（检索增强生成）的智能问答系统，支持多格式文档处理和Web界面。

## 🚀 快速启动

### 方式一：Kubernetes部署（推荐生产环境）

```bash
# 1. 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 2. 创建配置
kubectl apply -f k8s/rag-config.yaml

# 3. 创建存储
kubectl apply -f k8s/rag-web-pvc.yaml

# 4. 部署服务
kubectl apply -f k8s/milvus-deployment.yaml
kubectl apply -f k8s/rag-web-deployment.yaml

# 5. 访问服务
# 本地访问：http://localhost:30500
# 局域网访问：http://<NodeIP>:30500
```

### 方式二：Docker部署（推荐开发环境）

#### 完整部署（包含Milvus，连接外部Ollama）
```bash
# 1. 确保外部Ollama服务正在运行
ollama serve

# 2. 使用快速启动脚本
chmod +x start-docker.sh
./start-docker.sh

# 或手动启动
docker-compose up -d
```

#### 仅部署RAG应用（连接外部服务）
```bash
# 确保外部服务正在运行：
# - Milvus: localhost:19530
# - Ollama: localhost:11434

docker-compose -f docker-compose.simple.yml up -d
```

### 方式三：本地部署

```bash
# 1. 检查系统状态
python3 start.py status

# 2. 启动命令行模式
python3 start.py cli

# 3. 启动Web界面
python3 start.py web
```

## 📋 功能特性

- **多格式文档支持**: PDF, DOCX, MD, PPTX, TXT
- **智能问答**: 基于文档内容的智能问答
- **向量数据库**: 使用Milvus存储文档向量
- **双界面**: 命令行和Web界面
- **流式输出**: 支持打字机效果的实时回答
- **容器化部署**: 支持Docker和Kubernetes部署
- **配置管理**: 支持ConfigMap统一管理配置
- **数据持久化**: 支持PVC持久化存储
- **实时统计**: 知识库文档数量实时显示
- **文件处理**: 支持拖拽上传和批量处理

## 🔧 环境要求

### Kubernetes部署
- Kubernetes 1.20+
- kubectl 命令行工具
- 外部Ollama服务

### Docker部署
- Docker & Docker Compose
- 外部Ollama服务

### 本地部署
- Python 3.9+
- Milvus向量数据库
- Ollama大语言模型服务

## 📁 项目结构

```
RAG-autogen/
├── 🚀 启动和配置文件
│   ├── start.py                    # 统一启动脚本
│   ├── start_web_ui.py            # Web UI独立启动脚本
│   ├── docker-compose.yml         # Docker服务配置
│   ├── requirements.txt           # Python依赖包列表
│   └── .gitignore                 # Git忽略文件配置
│
├── ⚙️ 配置目录
│   └── config/
│       └── settings.py            # 系统配置文件
│
├── 📁 源代码目录
│   └── src/
│       ├── core/                  # 核心模块
│       │   └── rag_finance_qa.py  # RAG系统核心
│       ├── web/                   # Web模块
│       │   └── web_ui.py         # Web UI服务
│       ├── processors/            # 处理器模块
│       │   └── document_processor.py # 文档处理器
│       └── utils/                 # 工具模块
│           ├── text_utils.py      # 文本工具
│           ├── vector_store.py    # 向量数据库
│           └── ui_utils.py        # UI工具
│
├── 🎨 界面资源
│   ├── templates/                 # HTML模板
│   │   └── index.html            # Web界面模板
│   └── static/                    # 静态资源(CSS/JS/图片)
│
├── 💾 数据目录
│   ├── data/                      # 应用数据
│   ├── uploads/                   # 上传文件
│   ├── volumes/                   # Docker数据卷
│   └── logs/                      # 日志文件
│
├── 🐳 Docker和K8S配置
│   ├── k8s/                       # Kubernetes部署文件
│   ├── Dockerfile                 # Docker镜像构建
│   └── docker-entrypoint.sh      # Docker入口脚本
│
└── 🧪 测试目录
    └── tests/                     # 测试文件
```

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# Milvus向量数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
COLLECTION_NAME=finance_knowledge

# Ollama大语言模型配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:14b

# Web UI配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/rag_system.log

# 数据目录配置
DATA_DIR=data
UPLOADS_DIR=uploads
EXPORTS_DIR=data/exports

# 部署环境配置
FLASK_ENV=production
```

### 配置优先级

1. **环境变量** - 最高优先级
2. **.env文件** - 次优先级
3. **默认值** - 最低优先级

## 🐳 Docker部署详解

### 服务架构
- **RAG Web应用**: Flask Web服务
- **Milvus**: 向量数据库（容器内）
- **外部Ollama**: 大语言模型服务（宿主机）

### 端口映射
- `5000`: Web界面
- `19530`: Milvus API
- `9091`: Milvus管理端口

### 数据持久化
- `./uploads`: 上传文件
- `./data`: 系统数据
- `./logs`: 日志文件
- `./volumes`: Docker卷数据

## 🛠️ 故障排除

### 常见问题

#### 1. Milvus连接失败
```bash
# 检查Milvus服务状态
docker ps | grep milvus

# 查看Milvus日志
docker logs milvus-standalone
```

#### 2. Ollama服务连接失败
```bash
# 检查Ollama服务
curl http://localhost:11434/api/tags

# 启动Ollama服务
ollama serve
```

#### 3. 文件上传失败
```bash
# 检查上传目录权限
ls -la uploads/

# 检查磁盘空间
df -h
```

#### 4. 向量数据库初始化失败
```bash
# 检查Milvus连接
python3 -c "from src.utils.vector_store import VectorStore; vs = VectorStore(); print('连接成功')"
```

### 日志查看
```bash
# 查看应用日志
tail -f logs/rag_system.log

# 查看Docker容器日志
docker logs rag-autogen-rag-web-1
```

## 📊 系统监控

### Web界面状态
- **知识库统计**: 显示当前文档总数
- **处理状态**: 显示文件处理进度
- **系统状态**: 显示系统运行状态

### 健康检查
```bash
# 检查Web服务
curl http://localhost:5000/health

# 检查Milvus服务
curl http://localhost:9091/healthz
```

## 🔒 安全建议

1. **生产环境部署**
   - 使用HTTPS
   - 配置防火墙规则
   - 定期备份数据

2. **访问控制**
   - 限制文件上传大小
   - 配置访问日志
   - 监控异常访问

3. **数据安全**
   - 加密敏感数据
   - 定期清理临时文件
   - 备份重要文档

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**注意**: 请确保在生产环境中正确配置所有安全设置和备份策略。 