# 金融知识RAG问答系统

这是一个基于AutoGen、Milvus和DeepSeek-R1:14B的金融知识检索增强生成（RAG）问答系统。

## 功能特点

- 使用Milvus向量数据库存储和检索金融知识
- 基于本地Ollama服务运行DeepSeek-R1:14B大语言模型
- 使用AutoGen框架实现智能对话
- 支持中文金融知识问答

## 系统要求

- Python 3.8+
- Milvus 2.3.0+
- Ollama服务（运行DeepSeek-R1:14B模型）

## 安装步骤

1. 克隆仓库：
```bash
git clone [repository-url]
cd [repository-name]
```

2. 安装依赖：
```bash
pip3 install -r requirements.txt
```

3. 确保Ollama服务正在运行：
```bash
# 检查Ollama服务是否运行
curl http://106.52.6.69:11434
```

4. 启动Milvus服务：
```bash
docker run -d --name milvus_standalone -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
```

## 使用方法

1. 运行示例程序：
```bash
python3 rag_finance_qa.py
```

2. 自定义使用：
```python
from rag_finance_qa import FinanceRAGSystem

# 初始化系统
rag_system = FinanceRAGSystem()

# 添加知识
knowledge = [
    "你的金融知识文本1",
    "你的金融知识文本2",
    # ...
]
rag_system.add_knowledge(knowledge)

# 提问
question = "你的问题"
answer = rag_system.answer_question(question)
print(answer)
```

## 注意事项

- 确保Milvus服务正在运行
- 确保Ollama服务正在运行并可访问
- 建议使用虚拟环境运行项目

## 许可证

MIT License 