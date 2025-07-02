"""
基于智能体协作的RAG问答系统
====================================

功能特性:
- 多智能体协作：检索智能体、分析智能体、回答智能体
- 智能体间通信：通过消息传递进行协作
- 角色分工：每个智能体负责特定任务
- 可扩展性：易于添加新的智能体角色
- 并发处理：支持多个智能体并行工作
- 父页面检索：支持返回文档的具体页面信息

智能体架构:
1. RetrievalAgent: 检索智能体，负责文档检索
2. AnalysisAgent: 分析智能体，负责内容分析
3. AnswerAgent: 回答智能体，负责生成最终答案
4. CoordinatorAgent: 协调智能体，管理整个流程

作者: RAG系统开发团队
版本: 2.1.0
更新日期: 2024
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import ollama
from dotenv import load_dotenv

# 导入现有模块
from src.processors.document_processor import DocumentProcessor
from src.utils.text_utils import TextUtils
from src.utils.vector_store import VectorStore
from src.utils.ui_utils import print_info, print_warning, print_success, print_error
from src.utils.logger import logger

# 导入配置
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

# 加载环境变量
load_dotenv()

class Agent:
    """基础智能体类"""
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
    
    def process(self, message: str, context: str = "") -> str:
        """处理消息并返回回复"""
        logger.info(f"🤖 {self.name} 开始处理消息...")
        logger.info(f"📝 消息内容: {message[:100]}...")
        logger.info(f"📋 上下文长度: {len(context)} 字符")
        
        try:
            prompt = f"{self.system_prompt}\n\n上下文信息:\n{context}\n\n用户消息:\n{message}\n\n请以{self.role}的身份回复:"
            
            logger.info(f"🔄 {self.name} 调用Ollama API...")
            response = self.client.chat(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response['message']['content']
            logger.info(f"✅ {self.name} 处理完成，结果长度: {len(result)} 字符")
            logger.info(f"📄 {self.name} 结果预览: {result[:100]}...")
            
            return result
        except Exception as e:
            logger.error(f"❌ {self.name} 处理失败: {str(e)}")
            print_error(f"{self.name} 处理失败: {str(e)}")
            return f"处理失败: {str(e)}"

class RetrievalAgent(Agent):
    """检索智能体"""
    
    def __init__(self):
        system_prompt = """你是检索智能体，专门负责从知识库中检索相关信息。

你的职责：
1. 理解用户问题的核心需求
2. 从知识库中检索最相关的信息
3. 确保检索结果的准确性和完整性
4. 过滤无关或低质量的信息
5. 为后续分析提供高质量的检索结果
6. 记录每个片段的来源信息

检索要求：
- 检索结果要全面覆盖问题涉及的各个方面
- 优先选择高质量、权威的信息源
- 确保信息的时效性和准确性
- 避免重复或冗余的信息
- 每个片段的来源信息
- 检索结果要便于后续处理和分析"""
        
        super().__init__("retrieval_agent", "检索智能体", system_prompt)

class AnalysisAgent(Agent):
    """分析智能体"""
    
    def __init__(self):
        system_prompt = """你是分析智能体，专门负责分析检索到的信息。

你的职责：
1. 深入分析检索到的文档内容
2. 识别关键信息和重要观点
3. 评估信息的可信度和时效性
4. 发现信息间的关联和矛盾
5. 为回答智能体提供分析结果
6. 验证信息来源的准确性

分析维度：
- 内容准确性
- 信息完整性
- 逻辑一致性
- 时效性
- 可信度
- 信息来源准确性

输出格式要求：
- 使用markdown格式
- 段落之间用空行分隔
- 重要信息用**粗体**标记
- 列表使用- 格式
- 关键信息摘要
- 信息质量评估
- 潜在问题或矛盾
- 建议的回答方向
- 信息来源验证"""
        
        super().__init__("analysis_agent", "分析智能体", system_prompt)

class AnswerAgent(Agent):
    """回答智能体"""
    
    def __init__(self):
        system_prompt = """你是回答智能体，专门负责生成最终的用户答案。

你的职责：
1. 基于检索和分析结果生成准确、完整的答案
2. 确保答案的逻辑性和可读性
3. 使用合适的语言风格和表达方式
4. 处理复杂问题和多角度分析
5. 标注信息来源
6. 确保答案的可信度和权威性

回答要求：
- 答案要准确、完整、有条理
- 使用markdown格式，结构清晰
- 重要信息用**粗体**标记
- 列表使用- 或1. 格式
- 代码用`代码`格式
- 用中文回答，语言要自然流畅
- 标注信息来源"""
        
        super().__init__("answer_agent", "回答智能体", system_prompt)

class CoordinatorAgent(Agent):
    """协调智能体"""
    
    def __init__(self):
        system_prompt = """你是协调智能体，负责协调整个智能体协作流程。

你的职责：
1. 接收用户问题并分发给相应智能体
2. 协调智能体间的协作
3. 确保流程的完整性和质量
4. 处理异常情况和错误
5. 整合最终结果
6. 验证信息来源的准确性

工作流程：
1. 接收用户问题
2. 启动检索智能体
3. 启动分析智能体
4. 启动回答智能体
5. 整合并返回最终答案

注意事项：
- 确保每个智能体都完成其任务
- 处理智能体间的依赖关系
- 监控整个流程的进度
- 处理异常和错误情况
- 验证信息来源的准确性"""
        
        super().__init__("coordinator", "协调智能体", system_prompt)

class AutoGenRAGSystem:
    """基于智能体协作的RAG问答系统"""
    
    def __init__(self):
        """初始化智能体系统"""
        logger.info("=" * 60)
        logger.info("🚀 开始初始化AutoGen智能体协作系统...")
        print_info("正在初始化智能体协作系统...")
        
        # 初始化基础组件
        logger.info("📦 初始化基础组件...")
        self.vector_store = VectorStore()
        self.text_utils = TextUtils()
        self.doc_processor = DocumentProcessor()
        logger.info("✅ 基础组件初始化完成")
        
        # 创建智能体
        logger.info("🤖 创建智能体...")
        self.retrieval_agent = RetrievalAgent()
        logger.info("  - 检索智能体创建完成")
        self.analysis_agent = AnalysisAgent()
        logger.info("  - 分析智能体创建完成")
        self.answer_agent = AnswerAgent()
        logger.info("  - 回答智能体创建完成")
        self.coordinator = CoordinatorAgent()
        logger.info("  - 协调智能体创建完成")
        
        logger.info("🎉 AutoGen智能体协作系统初始化完成")
        logger.info("=" * 60)
        print_success("智能体协作系统初始化完成")
    
    def add_document(self, file_path: str):
        """添加文档到知识库"""
        logger.info(f"📄 开始处理文档: {file_path}")
        try:
            print_info(f"正在处理文档: {file_path}")
            
            # 获取文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                # 使用新的PDF处理方法，保持页面信息
                logger.info("🔧 使用PDF页面处理方法...")
                processed_data = self.doc_processor.process_pdf_with_pages(file_path)
                
                if not processed_data or not processed_data.get('chunks'):
                    logger.warning(f"⚠️ PDF文档 {file_path} 处理结果为空")
                    print_warning(f"PDF文档 {file_path} 处理结果为空")
                    return False
                
                # 添加带页面信息的chunks到向量数据库
                logger.info("💾 添加到向量存储...")
                success = self.vector_store.add_texts_with_pages(
                    texts=processed_data['chunks'],
                    source=os.path.basename(file_path)
                )
                
                if success:
                    logger.info(f"✅ PDF文档 {file_path} 添加成功，共 {len(processed_data['chunks'])} 个chunks，{len(processed_data['pages'])} 页")
                    print_success(f"PDF文档 {file_path} 添加成功")
                    return True
                else:
                    logger.error(f"❌ PDF文档 {file_path} 添加失败")
                    print_error(f"PDF文档 {file_path} 添加失败")
                    return False
            else:
                # 对于非PDF文件，使用原有方法
                logger.info("🔧 使用原有文档处理方法...")
                processed_texts = self.doc_processor.process_file(file_path)
                
                if not processed_texts:
                    logger.warning(f"⚠️ 文档 {file_path} 处理结果为空")
                    print_warning(f"文档 {file_path} 处理结果为空")
                    return False
                
                logger.info(f"📝 文档处理完成，共生成 {len(processed_texts)} 个文本片段")
                
                # 添加到向量存储
                logger.info("💾 添加到向量存储...")
                success = self.vector_store.add_texts(
                    texts=processed_texts,
                    source=os.path.basename(file_path)
                )
                
                if success:
                    logger.info(f"✅ 文档 {file_path} 添加成功")
                    print_success(f"文档 {file_path} 添加成功")
                    return True
                else:
                    logger.error(f"❌ 文档 {file_path} 添加失败")
                    print_error(f"文档 {file_path} 添加失败")
                    return False
                
        except Exception as e:
            logger.error(f"❌ 处理文档 {file_path} 时出错: {str(e)}")
            print_error(f"处理文档 {file_path} 时出错: {str(e)}")
            return False

    def add_knowledge(self, texts: List[str], source: str = "manual_input"):
        """添加知识到知识库"""
        logger.info(f"📚 开始添加知识，来源: {source}，数量: {len(texts)} 条")
        try:
            print_info(f"正在添加知识，来源: {source}")
            
            # 添加到向量存储
            logger.info("💾 添加到向量存储...")
            success = self.vector_store.add_texts(texts=texts, source=source)
            
            if success:
                logger.info(f"✅ 知识添加成功，共 {len(texts)} 条")
                print_success(f"知识添加成功，共 {len(texts)} 条")
                return True
            else:
                logger.error("❌ 知识添加失败")
                print_error("知识添加失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 添加知识时出错: {str(e)}")
            print_error(f"添加知识时出错: {str(e)}")
            return False

    def search_similar(self, query_text: str, top_k: int = 20) -> List[Dict]:
        """搜索相似文档，父页面检索默认开启"""
        logger.info(f"🔍 开始搜索相似文档，查询: {query_text[:50]}...，top_k: {top_k}")
        try:
            results = self.vector_store.search_similar(query_text, top_k, return_parent_pages=True)
            logger.info(f"✅ 搜索完成，找到 {len(results)} 个相关文档")
            return results
        except Exception as e:
            logger.error(f"❌ 搜索失败: {str(e)}")
            print_error(f"搜索失败: {str(e)}")
            return []

    def search_knowledge_base(self, query: str, top_k: int = 20, use_reranking: bool = True, llm_weight: float = 0.7) -> List[Dict]:
        """搜索知识库
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_reranking: 是否使用LLM重排序
            llm_weight: LLM重排序权重
            
        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"搜索知识库: {query[:50]}...")
            results = self.vector_store.search_similar(
                query, 
                top_k=top_k, 
                return_parent_pages=True,
                use_reranking=use_reranking,
                llm_weight=llm_weight
            )
            logger.info(f"找到 {len(results)} 个相关文档")
            return results
        except Exception as e:
            logger.error(f"搜索知识库时出错: {str(e)}")
            return []

    async def answer_question_async(self, question: str, fast_mode: bool = True, use_reranking: bool = True, llm_weight: float = 0.7) -> Dict[str, Any]:
        """异步回答问题，父页面检索默认开启"""
        logger.info(f"🔄 异步回答问题: {question}")
        try:
            if fast_mode:
                # 快速模式：直接使用RAG系统
                logger.info("⚡ 使用快速模式")
                
                # 搜索相关文档
                similar_docs = self.search_knowledge_base(
                    question, 
                    top_k=20,
                    use_reranking=use_reranking,
                    llm_weight=llm_weight
                )
                
                if not similar_docs:
                    logger.warning("未找到相关文档")
                    return {
                        "answer": "抱歉，我在文档中没有找到与您问题相关的信息。",
                        "context": "",
                        "analysis": "",
                        "framework": "AutoGen快速模式",
                        "agents_involved": ["retrieval_agent"],
                        "sources": []
                    }
                
                # 构建上下文
                context_parts = []
                sources = []
                
                for i, doc in enumerate(similar_docs[:5]):  # 只使用前5个最相关的文档
                    context_parts.append(f"文档片段 {i+1}:\n{doc['text']}")
                    sources.append(doc.get('source', doc.get('document_name', '未知文档')))
                
                context = "\n\n".join(context_parts)
                sources_text = "、".join(list(set(sources)))
                
                # 构建用户提示词
                user_prompt = f"""基于以下文档内容，请回答用户的问题：

文档内容：
{context}

用户问题：{question}

请提供详细的分析过程和准确的答案。如果文档中没有相关信息，请明确说明。

在回答末尾请标注信息来源的文档名称：{sources_text}"""

                # 调用LLM生成答案
                logger.info("正在生成答案...")
                response = self.ollama_client.chat(
                    model='deepseek-r1:14b',
                    messages=[
                        {"role": "system", "content": """你是一个专业的金融分析师助手，专门回答基于上传文档的金融相关问题。

你的任务是根据提供的文档内容，准确回答用户的问题。请遵循以下原则：

1. **严格基于文档内容**：只使用提供的文档内容来回答问题，不要使用外部知识
2. **准确引用**：在回答中明确指出信息来源的文档名称
3. **详细分析**：提供详细的分析过程，解释如何从文档中得出答案
4. **诚实回答**：如果文档中没有相关信息，请明确说明"根据提供的文档，无法找到相关信息"
5. **保持客观**：保持客观中立的分析态度，避免主观判断

请确保你的回答准确、详细且基于文档内容。"""},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                answer = response['message']['content']
                logger.info("✅ 快速模式回答完成")
                
                return {
                    "answer": answer,
                    "context": context,
                    "analysis": "快速模式：直接基于检索结果生成答案",
                    "framework": "AutoGen快速模式",
                    "agents_involved": ["retrieval_agent", "answer_agent"],
                    "sources": list(set(sources))
                }
            else:
                # 完整模式：使用多智能体协作
                logger.info("🤖 使用完整模式 - 多智能体协作")
                
                # 创建用户代理
                user_proxy = autogen.UserProxyAgent(
                    name="user_proxy",
                    human_input_mode="NEVER",
                    max_consecutive_auto_reply=10,
                    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                    code_execution_config={"work_dir": "workspace"},
                    llm_config=self.llm_config,
                    system_message="用户代理，负责接收用户问题并协调其他智能体。"
                )
                
                # 创建检索智能体
                retrieval_agent = autogen.AssistantAgent(
                    name="retrieval_agent",
                    llm_config=self.llm_config,
                    system_message=f"""你是检索智能体，负责从知识库中检索相关信息。

当前知识库统计：
- 文档数量：{self.get_stats().get('total_documents', 0)}
- 向量数量：{self.get_stats().get('total_vectors', 0)}

检索策略：
1. 使用语义搜索找到最相关的文档片段
2. 支持LLM重排序（权重：{llm_weight}）
3. 返回最相关的5个文档片段作为上下文

请根据用户问题，从知识库中检索相关信息。"""
                )
                
                # 创建分析智能体
                analysis_agent = autogen.AssistantAgent(
                    name="analysis_agent",
                    llm_config=self.llm_config,
                    system_message="""你是分析智能体，负责分析检索到的信息。

分析任务：
1. 评估检索结果的相关性和可靠性
2. 识别关键信息和数据点
3. 分析信息之间的关联性
4. 提供分析见解和建议

请对检索到的信息进行深入分析。"""
                )
                
                # 创建回答智能体
                answer_agent = autogen.AssistantAgent(
                    name="answer_agent",
                    llm_config=self.llm_config,
                    system_message="""你是回答智能体，负责生成最终答案。

回答要求：
1. 基于检索和分析结果生成准确答案
2. 使用markdown格式，结构清晰
3. 重要信息用**粗体**标记
4. 提供详细的分析过程
5. 标注信息来源
6. 用中文回答，语言自然流畅

请生成专业、准确的答案。"""
                )
                
                # 创建协调者智能体
                coordinator = autogen.AssistantAgent(
                    name="coordinator",
                    llm_config=self.llm_config,
                    system_message="""你是协调者智能体，负责协调整个问答流程。

协调任务：
1. 接收用户问题
2. 协调检索、分析、回答三个智能体
3. 确保流程顺利进行
4. 整合最终答案

流程：
1. 检索智能体：从知识库检索相关信息
2. 分析智能体：分析检索结果
3. 回答智能体：生成最终答案
4. 协调者：整合并返回结果

请协调整个问答流程。"""
                )
                
                # 执行智能体协作
                logger.info("🚀 开始智能体协作")
                
                # 首先进行检索
                similar_docs = self.search_knowledge_base(
                    question, 
                    top_k=20,
                    use_reranking=use_reranking,
                    llm_weight=llm_weight
                )
                
                if not similar_docs:
                    logger.warning("未找到相关文档")
                    return {
                        "answer": "抱歉，我在文档中没有找到与您问题相关的信息。",
                        "context": "",
                        "analysis": "",
                        "framework": "AutoGen完整模式",
                        "agents_involved": ["retrieval_agent", "analysis_agent", "answer_agent", "coordinator"],
                        "sources": []
                    }
                
                # 构建上下文
                context_parts = []
                sources = []
                
                for i, doc in enumerate(similar_docs[:5]):
                    context_parts.append(f"文档片段 {i+1}:\n{doc['text']}")
                    sources.append(doc.get('source', doc.get('document_name', '未知文档')))
                
                context = "\n\n".join(context_parts)
                sources_text = "、".join(list(set(sources)))
                
                # 构建协作提示词
                collaboration_prompt = f"""用户问题：{question}

检索到的相关信息（来源：{sources_text}）：
{context}

请按照以下流程协作回答：

1. 检索智能体：评估检索结果的相关性和完整性
2. 分析智能体：深入分析检索到的信息，识别关键点
3. 回答智能体：基于分析结果生成最终答案
4. 协调者：整合所有结果并返回最终答案

最终答案要求：
- 使用markdown格式
- 结构清晰，逻辑严密
- 重要信息用**粗体**标记
- 提供详细的分析过程
- 标注信息来源
- 用中文回答，语言自然流畅

请开始协作。"""
                
                # 启动协作
                chat_result = await user_proxy.a_initiate_chat(
                    coordinator,
                    message=collaboration_prompt
                )
                
                # 提取最终答案
                final_answer = ""
                analysis_content = ""
                
                for message in chat_result.chat_history:
                    if message.get("name") == "answer_agent":
                        final_answer = message.get("content", "")
                    elif message.get("name") == "analysis_agent":
                        analysis_content = message.get("content", "")
                
                # 如果没有找到答案，使用最后一个消息
                if not final_answer and chat_result.chat_history:
                    final_answer = chat_result.chat_history[-1].get("content", "")
                
                logger.info("✅ 完整模式协作完成")
                
                return {
                    "answer": final_answer,
                    "context": context,
                    "analysis": analysis_content,
                    "framework": "AutoGen完整模式",
                    "agents_involved": ["retrieval_agent", "analysis_agent", "answer_agent", "coordinator"],
                    "sources": list(set(sources))
                }
                
        except Exception as e:
            logger.error(f"❌ 异步回答问题失败: {str(e)}")
            return {
                "answer": f"回答失败: {str(e)}",
                "context": "",
                "analysis": "",
                "framework": "AutoGen",
                "agents_involved": [],
                "sources": []
            }

    def answer_question(self, question: str, use_reranking: bool = True, llm_weight: float = 0.7) -> str:
        """回答问题
        
        Args:
            question: 用户问题
            use_reranking: 是否使用LLM重排序
            llm_weight: LLM重排序权重
            
        Returns:
            答案文本
        """
        try:
            logger.info(f"开始回答问题: {question}")
            
            # 搜索相关文档
            similar_docs = self.search_knowledge_base(
                question, 
                top_k=20,
                use_reranking=use_reranking,
                llm_weight=llm_weight
            )
            
            if not similar_docs:
                logger.warning("未找到相关文档")
                return "抱歉，我在文档中没有找到与您问题相关的信息。"
            
            # 构建上下文
            context_parts = []
            sources = []
            
            for i, doc in enumerate(similar_docs[:5]):  # 只使用前5个最相关的文档
                context_parts.append(f"文档片段 {i+1}:\n{doc['text']}")
                sources.append(doc.get('document_name', '未知文档'))
            
            context = "\n\n".join(context_parts)
            sources_text = "、".join(list(set(sources)))
            
            # 构建用户提示词
            user_prompt = f"""基于以下文档内容，请回答用户的问题：

文档内容：
{context}

用户问题：{question}

请提供详细的分析过程和准确的答案。如果文档中没有相关信息，请明确说明。

在回答末尾请标注信息来源的文档名称：{sources_text}"""

            # 调用LLM生成答案
            logger.info("正在生成答案...")
            response = self.ollama_client.chat(
                model='deepseek-r1:14b',
                messages=[
                    {"role": "system", "content": """你是一个专业的金融分析师助手，专门回答基于上传文档的金融相关问题。

你的任务是根据提供的文档内容，准确回答用户的问题。请遵循以下原则：

1. **严格基于文档内容**：只使用提供的文档内容来回答问题，不要使用外部知识
2. **准确引用**：在回答中明确指出信息来源的文档名称
3. **详细分析**：提供详细的分析过程，解释如何从文档中得出答案
4. **诚实回答**：如果文档中没有相关信息，请明确说明"根据提供的文档，无法找到相关信息"
5. **保持客观**：保持客观中立的分析态度，避免主观判断

请确保你的回答准确、详细且基于文档内容。"""},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            answer = response['message']['content']
            logger.info("答案生成完成")
            
            return answer
            
        except Exception as e:
            logger.error(f"回答问题时出错: {str(e)}")
            return f"抱歉，处理您的问题时出现了错误: {str(e)}"

    def clear_knowledge_base(self):
        """清空知识库"""
        logger.info("🗑️ 开始清空知识库...")
        try:
            success = self.vector_store.clear_collection()
            if success:
                logger.info("✅ 知识库清空成功")
                print_success("知识库清空成功")
            else:
                logger.error("❌ 知识库清空失败")
                print_error("知识库清空失败")
            return success
        except Exception as e:
            logger.error(f"❌ 清空知识库时出错: {str(e)}")
            print_error(f"清空知识库时出错: {str(e)}")
            return False

    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体系统状态"""
        logger.info("📊 获取智能体系统状态...")
        try:
            # 获取向量存储统计
            collection_stats = self.vector_store.get_collection_stats()
            logger.info(f"📈 向量存储统计: {collection_stats}")
            
            status = {
                "system_status": "running",
                "agents": [
                    {"name": "retrieval_agent", "status": "ready"},
                    {"name": "analysis_agent", "status": "ready"},
                    {"name": "answer_agent", "status": "ready"},
                    {"name": "coordinator", "status": "ready"}
                ],
                "total_agents": 4,
                "vector_store": collection_stats,
                "ollama_status": "connected"
            }
            
            logger.info("✅ 智能体系统状态获取成功")
            return status
        except Exception as e:
            logger.error(f"❌ 获取智能体系统状态失败: {str(e)}")
            return {
                "system_status": "error",
                "error": str(e),
                "agents": [],
                "total_agents": 0
            }

def main():
    """主函数，用于测试"""
    logger.info("🧪 开始AutoGen系统测试...")
    try:
        # 创建智能体系统
        logger.info("🚀 创建AutoGen智能体系统...")
        system = AutoGenRAGSystem()
        
        # 测试问答
        question = "什么是机器学习？"
        logger.info(f"🤔 测试问题: {question}")
        answer = system.answer_question(question)
        print(f"问题: {question}")
        print(f"答案: {answer}")
        logger.info("✅ 测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        print_error(f"测试失败: {str(e)}")

if __name__ == "__main__":
    main() 