import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import time
import ollama
import sys
from datetime import datetime

# 导入自定义模块
from src.processors.document_processor import DocumentProcessor
from src.utils.text_utils import TextUtils
from src.utils.vector_store import VectorStore
from src.utils.query_rewriter import QueryRewriter
from src.utils.ui_utils import print_section, typewriter_print, print_info, print_warning, print_success, print_error
from src.utils.logger import logger

# 导入配置
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

# 加载环境变量
load_dotenv()

class FinanceRAGSystem:
    """金融知识RAG问答系统"""
    
    def __init__(self):
        """初始化系统"""
        logger.info(f"正在连接到Ollama服务: {OLLAMA_BASE_URL}")
        
        # 初始化组件
        self.vector_store = VectorStore()
        self.text_utils = TextUtils()
        self.doc_processor = DocumentProcessor()
        self.query_rewriter = QueryRewriter()
        
        # 初始化Ollama客户端，支持重试
        max_retries = 5
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
                # 测试连接
                models = self.ollama_client.list()
                logger.info(f"成功连接到Ollama服务，可用模型: {len(models['models'])} 个")
                break
            except Exception as e:
                logger.info(f"尝试第 {attempt+1} 次连接Ollama失败: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.info("无法连接到Ollama服务，系统初始化失败")
                    raise e
        
        logger.info("系统初始化完成")

    def add_document(self, file_path: str):
        """添加文档到知识库"""
        try:
            logger.info(f"=== 开始处理文档: {file_path} ===")
            
            if not os.path.exists(file_path):
                logger.info(f"文件不存在 - {file_path}")
                return

            # 获取文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            logger.info(f"文件类型: {file_ext}")

            if file_ext == '.pdf':
                # 使用新的PDF处理方法，保持页面信息
                logger.info("使用PDF页面处理方法...")
                processed_data = self.doc_processor.process_pdf_with_pages(file_path)
                
                if not processed_data or not processed_data.get('chunks'):
                    logger.info("PDF处理结果为空，无法添加到知识库")
                    return
                
                # 添加带页面信息的chunks到向量数据库
                logger.info(f"准备添加 {len(processed_data['chunks'])} 个带页面信息的chunks")
                success = self.vector_store.add_texts_with_pages(
                    texts=processed_data['chunks'],
                    source=os.path.basename(file_path)
                )
                
                if success:
                    logger.info(f"成功添加PDF文档，共 {len(processed_data['chunks'])} 个chunks，{len(processed_data['pages'])} 页")
                    # 获取更新后的统计信息
                    collection_stats = self.vector_store.get_collection_stats()
                    logger.info(f"知识库统计: {collection_stats}")
                else:
                    logger.info("添加PDF文档失败")
                
            else:
                # 对于非PDF文件，使用原有方法
                logger.info("使用原有文档处理方法...")
                text_blocks = self.doc_processor.process_file(file_path)
                logger.info(f"文档处理器返回了 {len(text_blocks)} 个文本块")
                
                if not text_blocks:
                    logger.info("提取的文本为空，无法添加到知识库")
                    return

                # 将文本列表合并为单个字符串，然后重新分割
                full_text = "\n\n".join(text_blocks)
                logger.info(f"合并后的文本长度: {len(full_text)} 字符")

                # 将文本分割成较小的块
                logger.info("开始分割文本...")
                text_blocks = self.text_utils.split_text(full_text)
                logger.info(f"文本分割完成，共 {len(text_blocks)} 个块")

                # 检查每个文本块是否已存在
                logger.info("开始检查重复内容...")
                new_texts = []
                duplicate_count = 0
                
                for i, block in enumerate(text_blocks):
                    if not block.strip():
                        continue
                    
                    logger.info(f"检查第 {i+1}/{len(text_blocks)} 个文本块...")
                    
                    # 检查相似性
                    try:
                        query_embedding = self.text_utils.generate_embeddings([block])[0]
                        similar_texts = self.vector_store.search(query_embedding, top_k=1)
                        
                        if similar_texts and self.text_utils.calculate_similarity(block, similar_texts[0]["text"]) > 0.8:
                            logger.info(f"跳过相似内容: {block[:100]}...")
                            duplicate_count += 1
                            continue
                        
                        new_texts.append({
                            "text": block,
                            "source": os.path.basename(file_path),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        logger.info(f"添加新文本块: {block[:100]}...")
                        
                    except Exception as e:
                        logger.info(f"检查文本块时出错: {str(e)}")
                        # 如果检查失败，直接添加
                        new_texts.append({
                            "text": block,
                            "source": os.path.basename(file_path),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                logger.info(f"重复检查完成: 跳过 {duplicate_count} 个重复内容，新增 {len(new_texts)} 个文本块")

                if not new_texts:
                    logger.info("所有内容都已存在于知识库中")
                    return

                logger.info(f"准备添加 {len(new_texts)} 个新文本块到数据库")

                # 为新的文本生成嵌入向量
                try:
                    logger.info("开始生成嵌入向量...")
                    embeddings = self.text_utils.generate_embeddings([item["text"] for item in new_texts])
                    logger.info(f"成功生成 {len(embeddings)} 个嵌入向量")
                except Exception as e:
                    logger.info(f"生成嵌入向量时出错: {str(e)}")
                    return

                # 准备插入数据
                texts = [item["text"] for item in new_texts]
                embedding_list = embeddings.tolist()
                sources = [item["source"] for item in new_texts]
                timestamps = [item["timestamp"] for item in new_texts]

                # 插入数据到向量数据库
                try:
                    logger.info("开始插入数据到向量数据库...")
                    self.vector_store.insert_data(texts, embedding_list, sources, timestamps)
                    logger.info(f"成功添加 {len(new_texts)} 条新知识到数据库")
                    
                    # 获取更新后的统计信息
                    collection_stats = self.vector_store.get_collection_stats()
                    logger.info(f"知识库统计: {collection_stats}")
                    
                except Exception as e:
                    logger.info(f"插入数据到数据库时出错: {str(e)}")
                    import traceback
                    logger.info(f"错误详情: {traceback.format_exc()}")
                    return

            logger.info(f"=== 文档处理完成: {file_path} ===")

        except Exception as e:
            logger.info(f"处理文档时发生错误: {str(e)}")
            import traceback
            logger.info(f"错误详情: {traceback.format_exc()}")

    def add_knowledge(self, texts: List[str], source: str = "manual_input"):
        """添加知识到向量数据库"""
        # 检查每条文本是否已存在类似内容
        new_texts = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for text in texts:
            # 搜索相似内容
            query_embedding = self.text_utils.generate_embeddings([text])[0]
            similar_texts = self.vector_store.search(query_embedding, top_k=1)
            
            if not similar_texts or self.text_utils.calculate_similarity(text, similar_texts[0]["text"]) < 0.8:
                new_texts.append({
                    "text": text,
                    "source": source,
                    "timestamp": timestamp
                })
            else:
                print_warning(f"发现类似内容，跳过添加：\n{text}\n")
        
        if not new_texts:
            print_info("所有内容都已存在于知识库中")
            return
            
        # 为新的文本生成嵌入向量
        embeddings = self.text_utils.generate_embeddings([item["text"] for item in new_texts])
        
        # 准备插入数据
        texts = [item["text"] for item in new_texts]
        embedding_list = embeddings.tolist()
        sources = [item["source"] for item in new_texts]
        timestamps = [item["timestamp"] for item in new_texts]
        
        # 插入数据
        self.vector_store.insert_data(texts, embedding_list, sources, timestamps)
        print_success(f"成功添加 {len(new_texts)} 条新知识到数据库")

    def search_similar(self, query_text: str, top_k: int = 20, use_reranking: bool = True, llm_weight: float = 0.7, use_query_rewrite: bool = True) -> List[Dict]:
        """搜索相似文本，父页面检索默认开启，支持查询重写"""
        try:
            # 如果启用查询重写，先重写查询
            if use_query_rewrite:
                logger.info("启用查询重写功能...")
                rewrite_result = self.query_rewriter.rewrite_query(query_text, strategy="auto")
                
                if rewrite_result["success"] and len(rewrite_result["rewritten_queries"]) > 1:
                    # 使用重写后的查询进行搜索
                    rewritten_queries = rewrite_result["rewritten_queries"]
                    logger.info(f"查询重写完成，生成 {len(rewritten_queries)} 个版本")
                    
                    # 使用第一个重写版本进行搜索
                    rewritten_query = rewritten_queries[0]
                    logger.info(f"使用重写查询: {rewritten_query}")
                    
                    # 使用重写后的查询进行搜索
                    results = self.vector_store.search_similar(rewritten_query, top_k, return_parent_pages=True, use_reranking=use_reranking, llm_weight=llm_weight)
                    
                    # 添加查询重写信息到结果中
                    for result in results:
                        result["original_query"] = query_text
                        result["rewritten_query"] = rewritten_query
                        result["query_rewrite_success"] = True
                    
                    return results
                else:
                    logger.warning("查询重写失败，使用原始查询")
            
            # 使用原始查询进行搜索
            results = self.vector_store.search_similar(query_text, top_k, return_parent_pages=True, use_reranking=use_reranking, llm_weight=llm_weight)
            
            # 添加查询重写信息
            for result in results:
                result["original_query"] = query_text
                result["rewritten_query"] = query_text
                result["query_rewrite_success"] = False
            
            return results
            
        except Exception as e:
            print_error(f"搜索相似文本时出错: {str(e)}")
            return []

    def answer_question(self, question: str, use_reranking: bool = True, llm_weight: float = 0.7, use_query_rewrite: bool = True) -> Dict[str, Any]:
        """回答问题，父页面检索默认开启，支持查询重写"""
        try:
            logger.info(f"开始处理问题: {question}")
            
            # 搜索相关文档
            similar_docs = self.search_similar(question, use_reranking=use_reranking, llm_weight=llm_weight, use_query_rewrite=use_query_rewrite)
            
            if not similar_docs:
                logger.warning("未找到相关文档")
                return {
                    "answer": "抱歉，我在文档中没有找到与您问题相关的信息。",
                    "context": [],
                    "sources": []
                }
            
            # 构建上下文
            context_parts = []
            sources = []
            
            for i, doc in enumerate(similar_docs[:5]):  # 只使用前5个最相关的文档
                context_parts.append(f"文档片段 {i+1}:\n{doc['text']}")
                sources.append(doc.get('source', doc.get('document_name', '未知文档')))
            
            context = "\n\n".join(context_parts)
            
            # 构建用户提示词
            user_prompt = f"""基于以下文档内容，请回答用户的问题：

文档内容：
{context}

用户问题：{question}

请提供详细的分析过程和准确的答案。如果文档中没有相关信息，请明确说明。"""

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
            
            return {
                "answer": answer,
                "context": similar_docs[:5],  # 返回前5个最相关的文档
                "sources": list(set(sources))  # 去重的文档来源
            }
            
        except Exception as e:
            logger.error(f"回答问题时出错: {str(e)}")
            return {
                "answer": f"抱歉，处理您的问题时出现了错误: {str(e)}",
                "context": [],
                "sources": []
            }

    def clear_knowledge_base(self):
        """清空知识库"""
        try:
            self.vector_store.clear_collection()
            print_success("知识库已清空")
            return True
        except Exception as e:
            print_error(f"清空知识库时出错: {str(e)}")
            return False

    def get_query_suggestions(self, query: str) -> Dict[str, Any]:
        """获取查询建议和重写选项
        
        Args:
            query: 原始查询
            
        Returns:
            包含查询建议和重写选项的字典
        """
        try:
            logger.info(f"获取查询建议: {query[:50]}...")
            
            # 分析查询意图
            intent_analysis = self.query_rewriter.analyze_query_intent(query)
            
            # 获取查询建议
            suggestions = self.query_rewriter.get_query_suggestions(query)
            
            # 尝试重写查询
            rewrite_result = self.query_rewriter.rewrite_query(query, strategy="auto")
            
            return {
                "original_query": query,
                "intent_analysis": intent_analysis,
                "suggestions": suggestions,
                "rewrite_result": rewrite_result,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"获取查询建议时出错: {str(e)}")
            return {
                "original_query": query,
                "intent_rewrite_success": False,
                "intent_analysis": {"type": "general", "confidence": 0.5, "keywords": [], "suggestions": []},
                "suggestions": [],
                "rewrite_result": {"success": False, "error": str(e)},
                "success": False,
                "error": str(e)
            }

def main():
    """主函数"""
    try:
        # 初始化系统
        rag_system = FinanceRAGSystem()
        
        # 添加示例知识
        example_knowledge = [
            "test1。",
            "test2。"
        ]
        rag_system.add_knowledge(example_knowledge, source="国际关系分析")
        
        # 添加文档
        rag_system.add_document("/Users/chenjie/Documents/Retrieval-Augmented Generation for Large Language Models- A Survey.pdf")
        rag_system.add_document("/Users/chenjie/Documents/贵州茅台酒股份有限公司2025 年第一季度报告.pdf")

        print_section("欢迎", "金融知识RAG问答系统已启动！\n输入 'quit' 或 'exit' 退出系统")
        
        while True:
            # 获取用户输入的问题
            question = input("\n请输入您的问题: ").strip()
            
            # 检查是否退出
            if question.lower() in ['quit', 'exit']:
                print_success("感谢使用，再见！")
                break
                
            # 如果问题为空，继续下一轮
            if not question:
                print_warning("问题不能为空，请重新输入！")
                continue
            
            # 回答问题
            print_info("正在思考...")
            result = rag_system.answer_question(question)
            
            # 打印结果
            print("\n" + "=" * 80)
            print(f"答案: {result['answer']}")
            print(f"上下文: {result['context']}")
            print(f"来源: {result['sources']}")
            print("\n" + "=" * 80)
            
    except Exception as e:
        print_error(f"系统运行出错: {str(e)}")

if __name__ == "__main__":
    main() 