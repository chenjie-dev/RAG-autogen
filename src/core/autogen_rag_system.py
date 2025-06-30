"""
基于智能体协作的RAG问答系统
====================================

功能特性:
- 多智能体协作：检索智能体、分析智能体、回答智能体
- 智能体间通信：通过消息传递进行协作
- 角色分工：每个智能体负责特定任务
- 可扩展性：易于添加新的智能体角色
- 并发处理：支持多个智能体并行工作

智能体架构:
1. RetrievalAgent: 检索智能体，负责文档检索
2. AnalysisAgent: 分析智能体，负责内容分析
3. AnswerAgent: 回答智能体，负责生成最终答案
4. CoordinatorAgent: 协调智能体，管理整个流程

作者: RAG系统开发团队
版本: 2.0.0
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
from processors.document_processor import DocumentProcessor
from utils.text_utils import TextUtils
from utils.vector_store import VectorStore
from utils.ui_utils import print_info, print_warning, print_success, print_error
from utils.logger import logger

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
1. 分析用户问题，提取关键检索词
2. 从向量数据库中检索相关文档片段
3. 评估检索结果的相关性和质量
4. 将检索到的信息传递给分析智能体

检索策略：
- 使用语义相似度搜索
- 考虑问题的多个方面
- 确保检索结果的多样性
- 过滤低质量或不相关的内容

输出格式：
- 检索到的文档片段（按相关性排序）
- 每个片段的来源信息
- 检索质量评估"""
        
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

分析维度：
- 内容准确性
- 信息完整性
- 逻辑一致性
- 时效性
- 可信度

输出格式要求：
- 使用markdown格式
- 段落之间用空行分隔
- 重要信息用**粗体**标记
- 列表使用- 格式
- 关键信息摘要
- 信息质量评估
- 潜在问题或矛盾
- 建议的回答方向"""
        
        super().__init__("analysis_agent", "分析智能体", system_prompt)

class AnswerAgent(Agent):
    """回答智能体"""
    
    def __init__(self):
        system_prompt = """你是回答智能体，专门负责生成最终答案。

你的职责：
1. 综合检索和分析结果
2. 生成准确、完整、易懂的答案
3. 确保答案的逻辑性和一致性
4. 提供必要的解释和背景信息
5. 标注信息来源

回答原则：
- 基于检索到的信息
- 保持客观中立
- 语言清晰易懂
- 结构合理有序
- 提供可信来源

输出格式要求：
- 使用markdown格式
- 段落之间用空行分隔
- 重要信息用**粗体**标记
- 列表使用- 或1. 格式
- 代码用`代码`格式
- 直接答案
- 详细解释
- 相关背景信息
- 信息来源
- 补充建议（如适用）"""
        
        super().__init__("answer_agent", "回答智能体", system_prompt)

class CoordinatorAgent(Agent):
    """协调智能体"""
    
    def __init__(self):
        system_prompt = """你是协调智能体，负责管理整个问答流程。

你的职责：
1. 接收用户问题并分发给相应智能体
2. 协调智能体间的协作
3. 确保流程的完整性和质量
4. 处理异常情况和错误
5. 整合最终结果

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
- 处理异常和错误情况"""
        
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
            
            # 使用文档处理器处理文件
            logger.info("🔧 使用文档处理器处理文件...")
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

    def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """搜索相似文档"""
        logger.info(f"🔍 开始搜索相似文档，查询: {query_text[:50]}...，top_k: {top_k}")
        try:
            results = self.vector_store.search_similar(query_text, top_k)
            logger.info(f"✅ 搜索完成，找到 {len(results)} 个相关文档")
            return results
        except Exception as e:
            logger.error(f"❌ 搜索失败: {str(e)}")
            print_error(f"搜索失败: {str(e)}")
            return []

    async def answer_question_async(self, question: str, fast_mode: bool = True) -> Dict[str, Any]:
        """异步回答问题"""
        logger.info("=" * 60)
        logger.info(f"🤔 开始处理用户问题: {question}")
        logger.info(f"⚙️ 模式: {'快速模式' if fast_mode else '完整模式'}")
        try:
            print_info(f"智能体开始处理问题: {question}")
            
            # 步骤1: 检索智能体工作
            logger.info("🔍 步骤1: 检索智能体开始工作...")
            print_info("检索智能体正在检索相关信息...")
            retrieval_results = self.search_similar(question, top_k=5)
            
            if not retrieval_results:
                logger.warning("⚠️ 未找到相关信息，返回默认答案")
                return {
                    "answer": "抱歉，我在知识库中没有找到相关信息来回答您的问题。",
                    "sources": [],
                    "status": "no_results"
                }
            
            # 构建检索上下文
            logger.info(f"📋 构建检索上下文，共 {len(retrieval_results)} 条结果")
            retrieval_context = "\n".join([hit["text"] for hit in retrieval_results])
            sources = [hit["source"] for hit in retrieval_results]
            logger.info(f"📄 来源文档: {list(set(sources))}")
            
            if fast_mode:
                # 快速模式：直接生成答案，跳过分析和协调步骤
                logger.info("⚡ 使用快速模式，跳过分析和协调步骤")
                print_info("使用快速模式，直接生成答案...")
                try:
                    # 使用优化的提示词直接生成答案
                    logger.info("📝 构建快速模式提示词...")
                    optimized_prompt = f"""基于以下检索到的信息，请直接回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理
7. 用中文回答，语言要自然流畅

检索到的信息：
{retrieval_context}

用户问题：{question}

答案："""
                    
                    # 在快速模式下，只返回检索上下文，不生成答案
                    # 答案生成将在web层通过流式输出处理
                    logger.info("🔄 快速模式：答案将在web层通过流式输出生成")
                    final_result = "快速模式：答案将通过流式输出生成"
                    
                    # 构建简化的思考过程
                    analysis_result = f"基于检索到的{len(retrieval_results)}条相关信息，将使用流式输出生成答案。"
                    logger.info("✅ 快速模式处理完成")
                    
                except Exception as e:
                    logger.error(f"❌ 快速模式生成答案失败: {str(e)}")
                    print_error(f"快速模式生成答案失败: {str(e)}")
                    final_result = "抱歉，智能体系统暂时无法生成答案，请稍后重试。"
                    analysis_result = "快速模式失败"
            else:
                # 完整模式：使用所有智能体
                logger.info("🔄 使用完整模式，启动所有智能体协作")
                
                # 步骤2: 分析智能体工作
                logger.info("🧠 步骤2: 分析智能体开始工作...")
                print_info("分析智能体正在分析检索结果...")
                try:
                    analysis_result = self.analysis_agent.process(
                        message=f"请分析以下信息以回答用户问题: {question}",
                        context=retrieval_context
                    )
                    logger.info(f"✅ 分析智能体工作完成，结果长度: {len(analysis_result)} 字符")
                    print_info(f"分析结果: {analysis_result[:100]}...")
                except Exception as e:
                    logger.error(f"❌ 分析智能体失败: {str(e)}")
                    print_error(f"分析智能体失败: {str(e)}")
                    analysis_result = "分析失败，将直接基于检索结果生成答案"
                
                # 步骤3: 回答智能体工作
                logger.info("💬 步骤3: 回答智能体开始工作...")
                print_info("回答智能体正在生成最终答案...")
                try:
                    answer_result = self.answer_agent.process(
                        message=f"基于检索和分析结果，请回答用户问题: {question}",
                        context=f"检索到的信息:\n{retrieval_context}\n\n分析结果:\n{analysis_result}"
                    )
                    logger.info(f"✅ 回答智能体工作完成，结果长度: {len(answer_result)} 字符")
                    print_info(f"回答结果: {answer_result[:100]}...")
                except Exception as e:
                    logger.error(f"❌ 回答智能体失败: {str(e)}")
                    print_error(f"回答智能体失败: {str(e)}")
                    # 如果回答智能体失败，使用简单的提示生成答案
                    try:
                        logger.info("🔄 尝试使用简单提示生成答案...")
                        simple_prompt = f"基于以下信息回答用户问题: {question}\n\n相关信息:\n{retrieval_context}"
                        response = self.answer_agent.client.chat(
                            model=OLLAMA_MODEL,
                            messages=[{"role": "user", "content": simple_prompt}]
                        )
                        answer_result = response['message']['content']
                        logger.info("✅ 简单提示生成答案成功")
                    except Exception as e2:
                        logger.error(f"❌ 简单回答也失败: {str(e2)}")
                        print_error(f"简单回答也失败: {str(e2)}")
                        answer_result = "抱歉，智能体系统暂时无法生成答案，请稍后重试。"
                
                # 步骤4: 协调智能体整合结果（可选）
                logger.info("🤝 步骤4: 协调智能体开始整合结果...")
                print_info("协调智能体正在整合最终结果...")
                try:
                    final_result = self.coordinator.process(
                        message=f"请整合以下结果并生成最终答案:\n\n问题: {question}\n\n检索结果: {retrieval_context}\n\n分析结果: {analysis_result}\n\n回答结果: {answer_result}",
                        context=""
                    )
                    logger.info(f"✅ 协调智能体工作完成，最终结果长度: {len(final_result)} 字符")
                    print_info(f"最终结果: {final_result[:100]}...")
                except Exception as e:
                    logger.error(f"❌ 协调智能体失败: {str(e)}")
                    print_error(f"协调智能体失败: {str(e)}")
                    final_result = answer_result  # 使用回答智能体的结果作为最终结果
            
            logger.info("🎉 智能体协作完成")
            logger.info("=" * 60)
            
            return {
                "answer": final_result,
                "sources": sources,
                "context": retrieval_context,
                "analysis": analysis_result,
                "status": "success",
                "mode": "fast" if fast_mode else "full"
            }
            
        except Exception as e:
            logger.error(f"❌ 智能体协作失败: {str(e)}")
            print_error(f"智能体协作失败: {str(e)}")
            return {
                "answer": f"智能体协作过程中出现错误: {str(e)}",
                "sources": [],
                "status": "error"
            }

    def answer_question(self, question: str) -> str:
        """同步回答问题"""
        logger.info(f"🔄 同步回答问题: {question}")
        try:
            # 使用异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.answer_question_async(question))
            loop.close()
            
            answer = result.get("answer", "无法生成答案")
            logger.info(f"✅ 同步回答完成，答案长度: {len(answer)} 字符")
            return answer
            
        except Exception as e:
            logger.error(f"❌ 同步回答问题失败: {str(e)}")
            print_error(f"回答问题失败: {str(e)}")
            return f"回答失败: {str(e)}"

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