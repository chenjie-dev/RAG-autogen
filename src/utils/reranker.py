import os
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import ollama
from src.utils.logger import logger
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

class LLMReranker:
    """LLM重排序器，使用大语言模型对检索结果进行重新排序"""
    
    def __init__(self):
        """初始化LLM重排序器"""
        try:
            self.client = ollama.Client(host=OLLAMA_BASE_URL)
            self.model = OLLAMA_MODEL
            # 测试连接
            self.client.list()
            logger.info(f"成功连接到Ollama服务: {OLLAMA_BASE_URL}")
        except Exception as e:
            logger.error(f"无法连接到Ollama服务: {str(e)}")
            raise e
        
        # 重排序提示词
        self.system_prompt_single = """你是一个RAG检索结果重排序专家。

你的任务是对检索到的文本块进行相关性评分，评估它们与用户查询的匹配程度。

评分标准（0-1分，0.1为增量）：
- 0.0: 完全不相关 - 文本与查询毫无关系
- 0.1-0.3: 轻微相关 - 只有很少的相关信息
- 0.4-0.6: 中等相关 - 包含部分相关信息
- 0.7-0.8: 高度相关 - 包含大量相关信息
- 0.9-1.0: 完全相关 - 直接回答查询问题

请分析文本内容，给出详细理由和评分。"""

        self.system_prompt_multiple = """你是一个RAG检索结果重排序专家。

你的任务是对多个检索到的文本块进行相关性评分，评估它们与用户查询的匹配程度。

评分标准（0-1分，0.1为增量）：
- 0.0: 完全不相关 - 文本与查询毫无关系
- 0.1-0.3: 轻微相关 - 只有很少的相关信息
- 0.4-0.6: 中等相关 - 包含部分相关信息
- 0.7-0.8: 高度相关 - 包含大量相关信息
- 0.9-1.0: 完全相关 - 直接回答查询问题

请为每个文本块分析内容，给出详细理由和评分。"""

    def get_rank_for_single_block(self, query: str, retrieved_document: Dict[str, Any]) -> Dict[str, Any]:
        """对单个文本块进行重排序"""
        try:
            user_prompt = f"""查询: "{query}"

检索到的文本块:
```
{retrieved_document['text']}
```

请分析这个文本块与查询的相关性，给出评分和理由。

请以JSON格式返回结果：
{{
    "reasoning": "详细的分析理由",
    "relevance_score": 0.8
}}"""

            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt_single},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = response['message']['content']
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    # 如果找不到JSON，使用默认值
                    result = {
                        "reasoning": "无法解析LLM响应",
                        "relevance_score": 0.5
                    }
            except json.JSONDecodeError:
                logger.warning(f"LLM响应不是有效的JSON: {content}")
                result = {
                    "reasoning": "LLM响应格式错误",
                    "relevance_score": 0.5
                }
            
            return result
            
        except Exception as e:
            logger.error(f"重排序单个文本块时出错: {str(e)}")
            return {
                "reasoning": f"重排序失败: {str(e)}",
                "relevance_score": 0.5
            }

    def get_rank_for_multiple_blocks(self, query: str, retrieved_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对多个文本块进行重排序"""
        try:
            formatted_blocks = "\n\n---\n\n".join([
                f'文本块 {i+1}:\n```\n{doc["text"]}\n```' 
                for i, doc in enumerate(retrieved_documents)
            ])
            
            user_prompt = f"""查询: "{query}"

检索到的文本块:
{formatted_blocks}

请分析每个文本块与查询的相关性，给出评分和理由。

请以JSON格式返回结果：
{{
    "block_rankings": [
        {{
            "reasoning": "文本块1的分析理由",
            "relevance_score": 0.8
        }},
        {{
            "reasoning": "文本块2的分析理由", 
            "relevance_score": 0.6
        }}
    ]
}}

请确保返回的block_rankings数组长度与文本块数量相同。"""

            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt_multiple},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = response['message']['content']
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    # 如果找不到JSON，使用默认值
                    result = {
                        "block_rankings": [
                            {
                                "reasoning": "无法解析LLM响应",
                                "relevance_score": 0.5
                            } for _ in retrieved_documents
                        ]
                    }
            except json.JSONDecodeError:
                logger.warning(f"LLM响应不是有效的JSON: {content}")
                result = {
                    "block_rankings": [
                        {
                            "reasoning": "LLM响应格式错误",
                            "relevance_score": 0.5
                        } for _ in retrieved_documents
                    ]
                }
            
            return result
            
        except Exception as e:
            logger.error(f"重排序多个文本块时出错: {str(e)}")
            return {
                "block_rankings": [
                    {
                        "reasoning": f"重排序失败: {str(e)}",
                        "relevance_score": 0.5
                    } for _ in retrieved_documents
                ]
            }

    def rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]], 
        documents_batch_size: int = 4, 
        llm_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序
        
        Args:
            query: 用户查询
            documents: 检索到的文档列表
            documents_batch_size: 批处理大小
            llm_weight: LLM评分权重 (0-1)
            
        Returns:
            重排序后的文档列表
        """
        try:
            logger.info(f"开始重排序 {len(documents)} 个文档，批处理大小: {documents_batch_size}")
            
            if not documents:
                return []
            
            # 创建文档批次
            doc_batches = [
                documents[i:i + documents_batch_size] 
                for i in range(0, len(documents), documents_batch_size)
            ]
            
            vector_weight = 1 - llm_weight
            
            if documents_batch_size == 1:
                # 单个文档处理
                def process_single_doc(doc):
                    # 获取单个文档的重排序评分
                    ranking = self.get_rank_for_single_block(query, doc)
                    
                    doc_with_score = doc.copy()
                    doc_with_score["relevance_score"] = ranking["relevance_score"]
                    doc_with_score["reasoning"] = ranking["reasoning"]
                    
                    # 计算综合评分（注意距离越小越好，所以需要转换）
                    # 将距离转换为相似度分数 (1 - distance)
                    similarity_score = 1 - doc.get('distance', 0)
                    doc_with_score["combined_score"] = round(
                        llm_weight * ranking["relevance_score"] + 
                        vector_weight * similarity_score,
                        4
                    )
                    return doc_with_score

                # 并行处理所有文档
                with ThreadPoolExecutor() as executor:
                    all_results = list(executor.map(process_single_doc, documents))
                    
            else:
                # 批量处理
                def process_batch(batch):
                    rankings = self.get_rank_for_multiple_blocks(query, batch)
                    results = []
                    block_rankings = rankings.get('block_rankings', [])
                    
                    # 确保有足够的评分结果
                    if len(block_rankings) < len(batch):
                        logger.warning(f"期望 {len(batch)} 个评分，但只得到 {len(block_rankings)} 个")
                        for i in range(len(block_rankings), len(batch)):
                            block_rankings.append({
                                "relevance_score": 0.5,
                                "reasoning": "默认评分（LLM响应不完整）"
                            })
                    
                    for doc, rank in zip(batch, block_rankings):
                        doc_with_score = doc.copy()
                        doc_with_score["relevance_score"] = rank["relevance_score"]
                        doc_with_score["reasoning"] = rank.get("reasoning", "")
                        
                        # 计算综合评分
                        similarity_score = 1 - doc.get('distance', 0)
                        doc_with_score["combined_score"] = round(
                            llm_weight * rank["relevance_score"] + 
                            vector_weight * similarity_score,
                            4
                        )
                        results.append(doc_with_score)
                    return results

                # 并行处理批次
                with ThreadPoolExecutor() as executor:
                    batch_results = list(executor.map(process_batch, doc_batches))
                
                # 展平结果
                all_results = []
                for batch in batch_results:
                    all_results.extend(batch)
            
            # 按综合评分降序排序
            all_results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            logger.info(f"重排序完成，返回 {len(all_results)} 个结果")
            return all_results
            
        except Exception as e:
            logger.error(f"重排序文档时出错: {str(e)}")
            # 如果重排序失败，返回原始结果
            return documents 