# Web UI使用指南
==================

## 📋 文档说明

本文档详细介绍金融知识RAG问答系统的Web界面使用方法。

### 🎯 主要功能
- **文档上传**: 支持多种格式的文档上传和处理
- **知识管理**: 查看和管理已上传的知识库
- **智能问答**: 基于上传文档的智能问答系统
- **流式回答**: 实时显示回答内容，提供更好的用户体验

### 🌐 访问方式
- 启动Web服务: `python3 start.py web`
- 访问地址: http://localhost:5000
- 支持所有现代浏览器

### 📱 界面特性
- 响应式设计，支持移动设备
- 现代化的用户界面
- 实时交互反馈
- 打字机效果的答案显示

# 金融知识RAG问答系统 - Web UI

这是一个基于Flask的Web界面，为金融知识RAG问答系统提供了友好的用户界面。

## 功能特性

### 🚀 核心功能
- **文档上传**: 支持拖拽上传PDF、DOCX、MD、PPTX、TXT格式文件
- **智能问答**: 基于上传文档的智能问答系统
- **知识管理**: 手动添加知识内容
- **实时状态**: 显示处理进度和系统状态
- **响应式设计**: 支持桌面和移动设备

### 📁 支持的文件格式
- PDF (.pdf)
- Word文档 (.docx)
- Markdown文件 (.md)
- PowerPoint演示文稿 (.pptx)
- 文本文件 (.txt)

## 安装和运行

### 1. 环境要求
- Python 3.8+
- Milvus服务运行中
- Ollama服务运行中

### 2. 安装依赖
```bash
pip3 install flask pymilvus sentence_transformers ollama pdfplumber python-docx markdown beautifulsoup4 python-pptx
```

### 3. 启动Web UI
```bash
python3 start_web_ui.py
```

或者直接运行：
```bash
python3 web_ui.py
```

### 4. 访问界面
打开浏览器访问: http://localhost:5000

## 使用说明

### 文档上传
1. 点击"选择文件"按钮或直接拖拽文件到上传区域
2. 系统会自动处理文档并添加到知识库
3. 处理过程中会显示进度条和状态信息

### 智能问答
1. 在右侧问答区域输入问题
2. 点击"发送"按钮或按回车键
3. 系统会基于知识库内容生成答案
4. 答案下方会显示信息来源

### 知识管理
1. 在左侧"添加知识"区域输入文本内容
2. 可选择添加来源信息
3. 点击"添加知识"按钮保存

### 系统状态
- **知识库统计**: 显示当前知识库中的文档总数
- **处理状态**: 显示文件处理进度
- **系统状态**: 显示系统运行状态

## 文件结构

```
RAG-autogen/
├── web_ui.py              # Web UI主程序
├── start_web_ui.py        # 启动脚本
├── templates/
│   └── index.html         # 主页模板
├── uploads/               # 文件上传目录
├── document_processor.py  # 文档处理模块
├── text_utils.py          # 文本处理工具
├── vector_store.py        # 向量数据库管理
├── ui_utils.py            # UI工具函数
└── rag_finance_qa.py      # RAG系统核心
```

## API接口

### 文件上传
- **POST** `/upload`
- 上传文档文件

### 问答接口
- **POST** `/ask`
- 发送问题并获取答案

### 知识管理
- **POST** `/knowledge`
- 添加知识内容

### 状态查询
- **GET** `/status`
- 获取处理状态
- **GET** `/stats`
- 获取系统统计信息

## 配置说明

### 服务配置
在 `web_ui.py` 中可以修改以下配置：

```python
# Ollama服务地址
OLLAMA_BASE_URL = "http://106.52.6.69:11434"

# Milvus服务配置
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

# 文件上传配置
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
```

### 支持的文件格式
```python
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'md', 'pptx', 'txt'}
```

## 故障排除

### 常见问题

1. **Milvus连接失败**
   - 确保Milvus服务正在运行
   - 检查端口19530是否可访问

2. **Ollama连接失败**
   - 确保Ollama服务正在运行
   - 检查服务地址和端口

3. **文件上传失败**
   - 检查文件格式是否支持
   - 检查文件大小是否超过限制

4. **处理进度不更新**
   - 刷新页面重新连接
   - 检查浏览器控制台错误信息

### 日志查看
Web UI会在控制台输出详细的日志信息，包括：
- 系统初始化状态
- 文件处理进度
- 错误信息

## 开发说明

### 添加新功能
1. 在 `web_ui.py` 中添加新的路由
2. 在 `templates/index.html` 中添加对应的UI元素
3. 在JavaScript中添加相应的交互逻辑

### 自定义样式
修改 `templates/index.html` 中的CSS样式来自定义界面外观。

### 扩展文件格式支持
1. 在 `document_processor.py` 中添加新的处理方法
2. 在 `web_ui.py` 中更新 `ALLOWED_EXTENSIONS`
3. 在HTML模板中更新支持格式说明

## 许可证

本项目采用MIT许可证。 