# 金融知识RAG问答系统

一个基于RAG（检索增强生成）的智能问答系统，支持多格式文档处理和Web界面。

## 🚀 快速启动

### 1. 检查系统状态
```bash
python3 start.py status
```

### 2. 启动命令行模式
```bash
python3 start.py cli
```

### 3. 启动Web界面
```bash
python3 start.py web
```

## 📋 功能特性

- **多格式文档支持**: PDF, DOCX, MD, PPTX, TXT
- **智能问答**: 基于文档内容的智能问答
- **向量数据库**: 使用Milvus存储文档向量
- **双界面**: 命令行和Web界面
- **流式输出**: 支持打字机效果的实时回答

## 🔧 环境要求

- Python 3.8+
- Milvus服务
- Ollama服务

## 📦 依赖安装

```bash
pip3 install -r requirements.txt
```

## 🎯 使用示例

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
├── requirements.txt            # 📦 依赖包列表
├── README.md                   # 📖 说明文档
├── .gitignore                  # 🚫 Git忽略文件
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
├── logs/                       # 📝 日志目录
└── tests/                      # 🧪 测试目录
```

## ⚙️ 配置说明

### 环境变量配置
创建 `.env` 文件：
```bash
# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
COLLECTION_NAME=finance_knowledge

# Ollama配置
OLLAMA_BASE_URL=http://106.52.6.69:11434
OLLAMA_MODEL=deepseek-r1:14b

# Web UI配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False
```

### 系统配置
主要配置在 `config/settings.py` 中：
- 向量数据库配置
- 文件处理参数
- 重试机制设置

## 🛠️ 故障排除

### 检查系统状态
```bash
python3 start.py --check
```

### 常见问题
1. **Milvus连接失败**: 确保Milvus服务正在运行
2. **Ollama连接失败**: 检查Ollama服务地址和端口
3. **依赖缺失**: 运行 `pip3 install -r requirements.txt`

### 日志查看
- 系统日志: `logs/` 目录
- Web UI日志: 控制台输出

## 🔄 开发指南

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