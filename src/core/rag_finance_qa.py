import os
from typing import List, Dict
from dotenv import load_dotenv
import time
import ollama
import sys
from datetime import datetime

# 导入自定义模块
from processors.document_processor import DocumentProcessor
from utils.text_utils import TextUtils
from utils.vector_store import VectorStore
from utils.ui_utils import print_section, typewriter_print, print_info, print_warning, print_success, print_error
from utils.logger import logger

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

            # 提取文本
            logger.info("开始提取文档文本...")
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

    def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """搜索相似文本"""
        try:
            # 生成查询文本的向量
            query_embedding = self.text_utils.generate_embeddings([query_text])[0]
            
            # 执行搜索
            results = self.vector_store.search(query_embedding, top_k)
            return results
        except Exception as e:
            print_error(f"搜索相似文本时出错: {str(e)}")
            return []

    def answer_question(self, question: str) -> str:
        """回答问题"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 搜索相关上下文
                context = self.search_similar(question)
                context_text = "\n".join([hit["text"] for hit in context])
                
                # 构建提示
                prompt = f"请结合以下检索到的内容和你自己的知识，回答用户问题：\n\n上下文：\n{context_text}\n\n问题：{question}\n\n答案："
                
                # 使用流式输出
                stream = self.ollama_client.chat(
                    model='deepseek-r1:14b',
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True
                )
                
                # 实时打印响应内容，使用打字机效果
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        # 跳过思考过程
                        if content.startswith('<think>'):
                            continue
                        typewriter_print(content)
                print("\n" + "=" * 80)  # 打印结束分隔线
                return "回答完成"
            except Exception as e:
                print_error(f"尝试第 {attempt+1} 次回答问题时出错: {str(e)}")
                time.sleep(retry_delay)
        return "多次尝试后仍未能生成答案。"

    def clear_knowledge_base(self):
        """清空知识库"""
        try:
            self.vector_store.clear_collection()
            print_success("知识库已清空")
            return True
        except Exception as e:
            print_error(f"清空知识库时出错: {str(e)}")
            return False

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
            rag_system.answer_question(question)
            
    except Exception as e:
        print_error(f"系统运行出错: {str(e)}")

if __name__ == "__main__":
    main() 