# RAG-AutoGen 智能问答系统

一个集成了传统RAG和AutoGen智能体框架的金融知识问答系统，支持多格式文档处理、智能问答和Web界面。

## 🚀 项目特性

### 核心功能
- **双系统架构**: 传统RAG + AutoGen智能体协作
- **多格式文档支持**: PDF, DOCX, MD, PPTX, TXT
- **高级PDF处理**: 基于DocLing的精确布局识别和文本提取
- **高级Word处理**: 基于DocLing的完整文档结构解析
- **智能问答**: 基于知识库的精准回答
- **Web界面**: 现代化的用户界面，支持流式回答
- **打字机效果**: 优化的聊天体验，实时显示思考过程
- **LLM重排序**: 支持基于大模型的检索结果重排序，提升答案相关性和准确性
- **中文优化嵌入**: 使用BAAI/bge-large-zh-v1.5模型，专为中文文本优化，支持跨语言检索

### AutoGen智能体系统
- **多智能体协作**: 检索、分析、回答、协调智能体
- **快速模式**: 优化性能，响应速度提升2-3倍
- **完整模式**: 多智能体深度协作，适合复杂问题
- **实时状态监控**: 智能体工作状态可视化

### 技术栈
- **后端**: Python, Flask, Milvus, Ollama
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI模型**: DeepSeek R1 14B (通过Ollama)
- **向量数据库**: Milvus
- **嵌入模型**: BAAI/bge-large-zh-v1.5 (1024维中文优化模型)
- **文档处理**: DocLing (PDF/Word), python-docx, markdown 

## 📁 项目结构

```
RAG-autogen/
├── src/                          # 源代码目录
│   ├── core/                     # 核心模块
│   │   ├── autogen_rag_system.py # AutoGen智能体系统
│   │   ├── autogen_web_ui.py     # AutoGen Web UI
│   │   └── rag_finance_qa.py     # 传统RAG系统
│   ├── processors/               # 文档处理器
│   │   └── document_processor.py # 多格式文档处理（DocLing集成）
│   ├── utils/                    # 工具模块
│   │   ├── text_utils.py         # 文本处理工具
│   │   ├── ui_utils.py           # UI工具
│   │   ├── vector_store.py       # 向量存储
│   │   └── reranker.py           # LLM重排序器
│   └── web/                      # Web服务
│       └── web_ui.py             # 统一Web界面
├── templates/                    # HTML模板
│   └── index.html               # 主界面模板
├── static/                       # 静态资源
│   ├── css/                     # 样式文件
│   ├── js/                      # JavaScript文件
│   └── img/                     # 图片资源
├── config/                       # 配置文件
│   └── settings.py              # 系统配置
├── data/                         # 数据目录
│   ├── exports/                 # 导出数据
│   └── uploads/                 # 上传文件
├── logs/                         # 日志目录
├── volumes/                      # Docker卷
├── k8s/                         # Kubernetes配置
├── tests/                        # 测试目录
│   ├── test_word_processing.py  # Word文档处理测试
│   └── test_backend_pdfium.py   # PDF处理测试
├── start.py                     # 统一启动脚本
├── requirements.txt             # Python依赖
├── Dockerfile                   # Docker配置
├── docker-compose.yml           # Docker Compose配置
└── README.md                    # 项目文档
```

## 🛠️ 快速开始

### 环境要求
- Python 3.8+
- Docker & Docker Compose
- Milvus 2.3+
- Ollama (支持DeepSeek R1 14B模型)
- 至少8GB可用内存 (用于BAAI/bge-large-zh-v1.5模型)

### 1. 克隆项目
```bash
git clone <repository-url>
cd RAG-autogen
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 测试系统功能（可选）
```bash
# 测试嵌入模型
python test_bge_embedding.py

# 测试PDF处理功能
python tests/test_backend_pdfium.py

# 测试Word文档处理功能
python tests/test_word_processing.py
```

### 4. 启动服务

#### 方式一：Docker启动（推荐）
```bash
# 启动所有服务
./start-docker.sh

# 或使用Docker Compose
docker-compose up -d
```

#### 方式二：本地启动
```bash
# 启动Web界面
python start.py web

# 启动命令行模式
python start.py cli

# 检查系统状态
python start.py status
```

### 5. 访问系统
- **Web界面**: http://localhost:5000
- **API文档**: http://localhost:5000/api

## 🎯 使用指南

### Web界面使用

1. **系统选择**
   - 传统RAG: 快速检索和回答
   - AutoGen智能体: 多智能体协作，支持快速/完整模式

2. **文档上传**
   - 支持拖拽上传
   - 支持多种格式: PDF, DOCX, MD, PPTX, TXT
   - **PDF处理**: 使用DocLing进行精确布局识别
   - **Word处理**: 使用DocLing进行完整结构解析
   - 实时显示上传进度

3. **智能问答**
   - 输入问题，系统自动选择最佳回答方式
   - 实时显示思考过程和答案生成
   - 支持流式回答，打字机效果
   - **LLM重排序**: 可在界面开启/关闭，支持调整LLM权重，提升答案相关性

### LLM重排序功能说明

- **功能简介**：
  - 检索到的文本块会先按向量相似度排序，再通过大模型（如DeepSeek R1 14B）对每个文本块与问题的相关性进行评分。
  - 最终结果为"向量分数+LLM分数"加权排序，权重可调。
  - 支持传统RAG和AutoGen两种模式。

- **参数说明**：
  - `use_reranking`：是否启用LLM重排序（前端可控，后端默认开启）
  - `llm_weight`：LLM分数权重（0~1），越高LLM影响越大，越低越依赖向量相似度

- **异常处理**：
  - LLM重排序器初始化失败或重排序过程出错时，系统自动回退为普通向量检索，不影响主流程。

- **前端交互**：
  - Web界面可一键切换是否启用LLM重排序，并可拖动滑块调整LLM权重。

### 测试说明

- 主要测试脚本已删除，建议通过Web界面或API端到端验证。
- 文档处理相关测试仍保留在`tests/`目录下。
- 如需自定义测试，可参考`src/utils/reranker.py`和`src/utils/vector_store.py`中的方法。

## ⚙️ 配置说明

### 主要配置项 (`config/settings.py`)

```python
# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "deepseek-r1:14b"

# Milvus配置
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION_NAME = "rag_documents"

# 嵌入模型配置
EMBEDDING_DIM = 1024  # BAAI/bge-large-zh-v1.5的嵌入维度
EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"

# 系统配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_FORMATS = ['.pdf', '.docx', '.md', '.pptx', '.txt']

# DocLing配置
DOCLING_ENABLE_LAYOUT_EXTRACTION = True  # 启用布局信息提取
DOCLING_FALLBACK_TO_PDFPLUMBER = True    # 启用备用PDF处理
DOCLING_WORD_STRUCTURE_EXTRACTION = True # 启用Word结构提取
```

### 环境变量
```bash
# Ollama服务地址
export OLLAMA_BASE_URL=http://your-ollama-server:11434

# Milvus配置
export MILVUS_HOST=your-milvus-host
export MILVUS_PORT=19530
```

## 🔧 部署指南

### Docker部署
```bash
# 构建镜像
docker build -t rag-autogen .

# 运行容器
docker run -d -p 5000:5000 rag-autogen
```

### Kubernetes部署
```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 部署Milvus
kubectl apply -f k8s/milvus-deployment.yaml

# 部署RAG应用
kubectl apply -f k8s/rag-web-deployment.yaml
```

### 生产环境配置
1. **反向代理**: 使用Nginx配置SSL和负载均衡
2. **数据库**: 使用外部Milvus集群
3. **监控**: 集成Prometheus和Grafana
4. **日志**: 配置ELK日志收集

## 🧪 测试

### 连接测试
```bash
# 测试嵌入模型
python test_bge_embedding.py

# 测试Ollama连接
python test_ollama_connection.py
```

### 文档处理测试
```bash
# 测试PDF处理功能
python tests/test_backend_pdfium.py

# 测试Word文档处理功能
python tests/test_word_processing.py
```

### 功能测试
1. **文档上传测试**: 上传不同格式文档
2. **问答测试**: 测试不同类型问题
3. **性能测试**: 比较传统RAG和AutoGen模式

## 🔍 故障排除

### 常见问题

1. **Milvus连接失败**
   ```bash
   # 检查Milvus服务状态
   docker ps | grep milvus
   
   # 重启Milvus服务
   docker-compose restart milvus
   ```

2. **Ollama服务不可用**
   ```bash
   # 检查Ollama服务
   curl http://localhost:11434/api/tags
   
   # 启动Ollama服务
   ollama serve
   ```

3. **模型下载失败**
   ```bash
   # 手动下载Ollama模型
   ollama pull deepseek-r1:14b
   
   # 手动下载嵌入模型
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-zh-v1.5')"
   ```

4. **文档处理失败**
   ```bash
   # 检查DocLing安装
   python -c "import docling; print('DocLing installed')"
   
   # 测试文档处理
   python tests/test_word_processing.py
   ```

5. **内存不足**
   - 减少并发请求数
   - 使用更小的模型
   - 增加系统内存
   - 检查BAAI/bge-large-zh-v1.5模型内存占用（约2-3GB）

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker logs rag-autogen-container
```

## 📊 性能优化

### 已实现的优化
1. **AutoGen快速模式**: 减少LLM调用次数
2. **流式输出**: 实时显示回答过程
3. **打字机效果**: 提升用户体验
4. **智能体状态监控**: 可视化处理过程
5. **DocLing文档处理**: 高效的文档解析和文本提取
6. **中文优化嵌入**: BAAI/bge-large-zh-v1.5模型，专为中文文本优化，支持跨语言检索

### 进一步优化建议
1. **缓存机制**: 缓存常见问题答案
2. **异步处理**: 大文档异步处理
3. **负载均衡**: 多实例部署
4. **模型量化**: 使用量化模型减少内存占用

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Milvus](https://milvus.io/) - 向量数据库
- [Ollama](https://ollama.ai/) - 本地LLM服务
- [AutoGen](https://microsoft.github.io/autogen/) - 智能体框架
- [DocLing](https://github.com/DS4SD/docling) - 文档处理框架
- [BAAI/bge-large-zh-v1.5](https://huggingface.co/BAAI/bge-large-zh-v1.5) - 中文嵌入模型
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - UI框架

## 📞 联系方式

- 项目维护者: RAG系统开发团队
- 邮箱: [your-email@example.com]
- 项目地址: [repository-url]

---

**更新内容**: 
- ✅ 增强PDF处理：修复文本单元格排序问题，提升提取准确性
- ✅ 新增Word处理：集成DocLing MsWord后端，支持完整文档结构解析
- ✅ 改进错误处理：完善的备用方案和异常处理机制
- ✅ 新增测试套件：PDF和Word文档处理功能测试
- ✅ 升级嵌入模型：使用BAAI/bge-large-zh-v1.5，专为中文优化，支持跨语言检索