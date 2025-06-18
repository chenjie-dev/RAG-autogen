# 金融知识RAG问答系统

一个基于RAG（检索增强生成）的智能问答系统，支持多格式文档处理和Web界面。

## 🚀 快速启动

### 方式一：Kubernetes部署（推荐生产环境）

详细部署说明请参考 [K8S_DEPLOYMENT.md](K8S_DEPLOYMENT.md)

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

#### 1. 检查系统状态
```bash
python3 start.py status
```

#### 2. 启动命令行模式
```bash
python3 start.py cli
```

#### 3. 启动Web界面
```bash
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

## 🔧 环境要求

### Kubernetes部署
- Kubernetes 1.20+
- kubectl 命令行工具
- 外部Ollama服务

### Docker部署
- Docker & Docker Compose
- 外部Ollama服务（可选，用于大模型）

### 本地部署
- Python 3.8+
- Milvus服务
- Ollama服务

## 🛠 依赖安装

### Docker部署
无需手动安装依赖，Docker会自动处理。

### 本地部署
```bash
pip3 install -r requirements.txt
```

> 注意：不再需要 PyPDF2，仅需 pdfplumber。

## 🎯 使用示例

### Docker部署
```bash
# 启动服务
docker-compose up -d

# 访问Web界面
# http://localhost:5000

# 查看日志
docker-compose logs -f rag-web
```

### 命令行模式
```bash
python3 start.py cli
# 然后输入问题，如："什么是RAG技术？"
```

### Web界面
```bash
python3 start.py web
# 访问 http://localhost:5000
# 上传文档，开始问答
```

## 📁 项目结构

```
RAG-autogen/
├── start.py                    # 🚀 统一启动脚本
├── start_web_ui.py            # 🌐 Web UI独立启动脚本
├── requirements.txt            # 📦 依赖包列表
├── README.md                   # 📖 说明文档
├── DOCKER_DEPLOYMENT.md        # 🐳 Docker部署文档
├── K8S_DEPLOYMENT.md          # ⎈ Kubernetes部署文档
├── k8s/                       # ⎈ Kubernetes配置目录
│   ├── namespace.yaml         # 命名空间定义
│   ├── rag-config.yaml        # ConfigMap配置
│   ├── rag-web-deployment.yaml # Web服务部署
│   ├── rag-web-pvc.yaml       # 持久化存储声明
│   └── milvus-deployment.yaml # Milvus服务部署
├── .gitignore                  # 🚫 Git忽略文件
├── .dockerignore               # 🐳 Docker忽略文件
├── Dockerfile                  # 🐳 Docker镜像构建文件
├── docker-compose.yml          # 🐳 Docker Compose配置
├── docker-compose.simple.yml   # 🐳 简化版Docker配置
├── docker-entrypoint.sh        # 🐳 Docker入口脚本
├── start-docker.sh             # 🐳 Docker快速启动脚本
├── config/
│   └── settings.py             # ⚙️ 系统配置
├── src/                        # 📁 源代码目录
│   ├── __init__.py
│   ├── core/                   # 🧠 核心模块
│   │   ├── __init__.py
│   │   └── rag_finance_qa.py   # RAG系统核心
│   ├── web/                    # 🌐 Web模块
│   │   ├── __init__.py
│   │   └── web_ui.py          # Web UI服务
│   ├── processors/             # 📄 处理器模块
│   │   ├── __init__.py
│   │   └── document_processor.py # 文档处理器
│   └── utils/                  # 🛠️ 工具模块
│       ├── __init__.py
│       ├── text_utils.py       # 文本工具
│       ├── vector_store.py     # 向量数据库
│       └── ui_utils.py         # UI工具
├── templates/                  # 🎨 模板目录
│   └── index.html             # Web界面模板
├── static/                     # 📱 静态资源
│   ├── css/
│   ├── js/
│   └── img/
├── data/                       # 💾 数据目录
│   ├── uploads/               # 上传文件
│   └── exports/               # 导出文件
├── uploads/                    # 📤 上传目录
├── logs/                       # 📝 日志目录
├── volumes/                    # 💾 Docker卷目录
└── tests/                      # 🧪 测试目录
```

## ⚙️ 配置说明

### Kubernetes环境
所有配置通过 ConfigMap 统一管理（k8s/rag-config.yaml），包括：
- Milvus连接配置
- Ollama服务配置
- Web服务配置
- 数据目录配置
- 日志配置

### Docker环境
所有服务均通过环境变量（如 MILVUS_HOST, MILVUS_PORT, OLLAMA_HOST）配置，代码已统一读取 config/settings.py。

- Docker Compose 内 rag-web 通过 `milvus-standalone:19530` 访问 Milvus。
- 外部服务通过 `localhost` 或 `host.docker.internal`。

## 🐛 常见问题

### Kubernetes部署问题
- Pod无法调度：检查命名空间是否正确（rag-system）
- ConfigMap未找到：确保ConfigMap在正确的命名空间中
- PVC绑定失败：检查存储类和PVC配置
- 服务无法访问：检查NodePort端口（30500）是否被占用

### Docker部署问题
- 若遇到"连接 localhost:19530 失败"，请检查环境变量和 config/settings.py 配置。
- 若遇到"PyPDF2 缺失"报错，升级代码后无需再安装 PyPDF2。

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

详细部署说明请参考 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

## 🛠️ 故障排除

### Kubernetes部署
```bash
# 查看所有资源
kubectl get all -n rag-system

# 查看Pod日志
kubectl logs -n rag-system -l app=rag-web

# 查看Pod详情
kubectl describe pod -n rag-system -l app=rag-web

# 检查配置
kubectl describe configmap -n rag-system rag-config
```

### Docker部署
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f rag-web

# 重启服务
docker-compose restart

# 检查外部Ollama服务
curl http://localhost:11434/api/tags
```

## 🔄 开发指南

### Kubernetes开发
```bash
# 更新配置
kubectl apply -f k8s/rag-config.yaml
kubectl rollout restart deployment rag-web -n rag-system

# 查看日志
kubectl logs -f -n rag-system -l app=rag-web

# 进入容器
kubectl exec -it -n rag-system $(kubectl get pod -n rag-system -l app=rag-web -o name) -- bash
```

### Docker开发
```bash
# 构建开发镜像
docker build -t rag-system:dev .

# 运行开发环境
docker run -it -v $(pwd):/app rag-system:dev bash
```

### 添加新功能
1. 在相应模块中添加代码
2. 更新配置文件
3. 添加测试用例
4. 更新文档

### 模块说明
- **core**: RAG系统核心逻辑
- **web**: Web界面相关代码
- **processors**: 文档处理模块
- **utils**: 通用工具函数

## �� 许可证

MIT License 