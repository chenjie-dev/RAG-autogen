from typing import List, Dict, Any
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from datetime import datetime
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from src.utils.logger import logger
from src.utils.reranker import LLMReranker

class VectorStore:
    """向量数据库管理类"""
    
    def __init__(self, host: str = None, port: str = None, collection_name: str = None):
        """初始化向量数据库
        
        Args:
            host: Milvus主机地址
            port: Milvus端口
            collection_name: 集合名称
        """
        # 支持环境变量配置
        self.host = host or os.getenv("MILVUS_HOST", "localhost")
        self.port = port or os.getenv("MILVUS_PORT", "19530")
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "finance_knowledge")
        self.collection = None
        
        # 初始化文本嵌入模型
        logger.info("正在初始化文本嵌入模型...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("文本嵌入模型初始化完成")
        
        # 初始化LLM重排序器（可选，失败时不影响基本功能）
        logger.info("正在初始化LLM重排序器...")
        try:
            self.reranker = LLMReranker()
            logger.info("LLM重排序器初始化完成")
        except Exception as e:
            logger.warning(f"LLM重排序器初始化失败，将禁用重排序功能: {str(e)}")
            self.reranker = None
        
        logger.info(f"正在连接到Milvus: {self.host}:{self.port}")
        
        # 连接Milvus，支持重试
        self._connect_with_retry()
        
        # 确保集合存在
        self._ensure_collection()
    
    def _connect_with_retry(self, max_retries: int = 5, retry_delay: int = 3):
        """带重试的Milvus连接"""
        for attempt in range(max_retries):
            try:
                connections.connect(host=self.host, port=self.port)
                logger.info(f"成功连接到Milvus服务: {self.host}:{self.port}")
                return
            except Exception as e:
                logger.info(f"尝试第 {attempt+1} 次连接Milvus失败: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    import time
                    time.sleep(retry_delay)
                else:
                    logger.info(f"无法连接到Milvus服务，请检查服务是否正在运行")
                    raise e
    
    def _connect(self):
        """连接到Milvus数据库（保留原方法以兼容）"""
        self._connect_with_retry()
    
    def _ensure_collection(self):
        """确保集合存在并具有正确的模式"""
        try:
            # 检查集合是否存在
            if utility.has_collection(self.collection_name):
                # 获取现有集合
                collection = Collection(self.collection_name)
                # 获取现有字段
                fields = [field.name for field in collection.schema.fields]
                # 检查是否需要更新
                if not all(field in fields for field in ['source', 'timestamp', 'page']):
                    logger.info("检测到集合模式需要更新，正在重新创建...")
                    # 删除旧集合
                    utility.drop_collection(self.collection_name)
                    # 创建新集合
                    self._create_collection()
                else:
                    logger.info("使用现有集合")
                    self.collection = collection
                    self.collection.load()
            else:
                # 创建新集合
                self._create_collection()
        except Exception as e:
            logger.info(f"检查集合时出错: {str(e)}")
            # 如果出错，尝试重新创建集合
            try:
                utility.drop_collection(self.collection_name)
            except:
                pass
            self._create_collection()
    
    def _create_collection(self):
        """创建具有完整模式的集合"""
        # 定义集合字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="page", dtype=DataType.INT64)  # 添加页面字段
        ]
        
        # 创建集合模式
        schema = CollectionSchema(fields=fields, description="金融知识库")
        
        # 创建集合
        self.collection = Collection(name=self.collection_name, schema=schema)
        
        # 创建索引
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        # 加载集合到内存
        self.collection.load()
        logger.info(f"成功创建集合 {self.collection_name} 并建立索引")
    
    def add_texts(self, texts: List[str], source: str = "unknown") -> bool:
        """添加文本到向量数据库
        
        Args:
            texts: 文本列表
            source: 来源信息
            
        Returns:
            是否成功添加
        """
        try:
            logger.info(f"开始添加 {len(texts)} 个文本到向量数据库...")
            
            if not texts:
                logger.info("文本列表为空，跳过添加")
                return True
            
            # 生成嵌入向量
            logger.info("正在生成嵌入向量...")
            embeddings = self.embedding_model.encode(texts)
            embeddings_list = embeddings.tolist()
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamps = [timestamp] * len(texts)
            sources = [source] * len(texts)
            pages = [0] * len(texts)  # 默认页面为0
            
            # 插入数据
            self.insert_data(texts, embeddings_list, sources, timestamps, pages)
            
            logger.info(f"成功添加 {len(texts)} 个文本到向量数据库")
            return True
            
        except Exception as e:
            logger.info(f"添加文本时出错: {str(e)}")
            return False

    def add_texts_with_pages(self, texts: List[Dict[str, Any]], source: str = "unknown") -> bool:
        """添加带页面信息的文本到向量数据库
        
        Args:
            texts: 包含页面信息的文本字典列表，每个字典包含 'text' 和 'page' 字段
            source: 来源信息
            
        Returns:
            是否成功添加
        """
        try:
            logger.info(f"开始添加 {len(texts)} 个带页面信息的文本到向量数据库...")
            
            if not texts:
                logger.info("文本列表为空，跳过添加")
                return True
            
            # 提取文本和页面信息
            text_list = [item['text'] for item in texts]
            pages = [item.get('page', 0) for item in texts]
            
            # 生成嵌入向量
            logger.info("正在生成嵌入向量...")
            embeddings = self.embedding_model.encode(text_list)
            embeddings_list = embeddings.tolist()
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamps = [timestamp] * len(texts)
            sources = [source] * len(texts)
            
            # 插入数据
            self.insert_data(text_list, embeddings_list, sources, timestamps, pages)
            
            logger.info(f"成功添加 {len(texts)} 个带页面信息的文本到向量数据库")
            return True
            
        except Exception as e:
            logger.info(f"添加带页面信息的文本时出错: {str(e)}")
            return False
    
    def search_similar(self, query_text: str, top_k: int = 20, return_parent_pages: bool = False, use_reranking: bool = True, llm_weight: float = 0.7) -> List[Dict]:
        """搜索相似文本
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            return_parent_pages: 是否返回父页面而不是chunks
            use_reranking: 是否使用LLM重排序
            llm_weight: LLM重排序权重 (0-1)
            
        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"搜索相似文本: {query_text[:50]}...")
            
            # 生成查询向量
            query_embedding = self.embedding_model.encode([query_text])[0]
            
            # 执行搜索
            results = self.search(query_embedding, top_k, return_parent_pages)
            
            # 如果启用重排序，对结果进行重新排序
            if use_reranking and results and self.reranker:
                logger.info("启用LLM重排序...")
                try:
                    # 增加初始检索数量以获得更好的重排序效果
                    initial_top_k = min(top_k * 2, 50)  # 最多检索50个
                    if len(results) < initial_top_k:
                        # 如果结果不够，重新检索更多
                        more_results = self.search(query_embedding, initial_top_k, return_parent_pages)
                        results = more_results
                    
                    # 执行重排序
                    reranked_results = self.reranker.rerank_documents(
                        query=query_text,
                        documents=results,
                        documents_batch_size=4,
                        llm_weight=llm_weight
                    )
                    
                    # 返回重排序后的前top_k个结果
                    results = reranked_results[:top_k]
                    logger.info(f"重排序完成，返回前 {len(results)} 个结果")
                except Exception as e:
                    logger.warning(f"重排序过程中出错，使用原始搜索结果: {str(e)}")
                    # 如果重排序失败，使用原始结果
                    results = results[:top_k]
            else:
                if not self.reranker:
                    logger.info("重排序器未初始化，跳过LLM重排序")
                else:
                    logger.info("跳过LLM重排序")
            
            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"搜索相似文本时出错: {str(e)}")
            return []
    
    def insert_data(self, texts: List[str], embeddings: List[List[float]], sources: List[str], timestamps: List[str], pages: List[int] = None):
        """插入数据到向量数据库
        
        Args:
            texts: 文本列表
            embeddings: 嵌入向量列表
            sources: 来源列表
            timestamps: 时间戳列表
            pages: 页面列表
        """
        try:
            logger.info(f"开始插入 {len(texts)} 条数据到向量数据库...")
            
            # 如果没有提供页面信息，使用默认值
            if pages is None:
                pages = [0] * len(texts)
            
            # 准备插入数据
            entities = [
                texts,  # text
                embeddings,  # embedding
                sources,  # source
                timestamps,  # timestamp
                pages  # page
            ]
            
            # 插入数据
            self.collection.insert(entities)
            
            # 立即刷新集合以确保数据持久化
            self.collection.flush()
            
            logger.info(f"成功插入 {len(texts)} 条数据到向量数据库")
            
        except Exception as e:
            logger.error(f"插入数据时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise e
    
    def search(self, query_embedding: np.ndarray, top_k: int = 20, return_parent_pages: bool = False) -> List[Dict]:
        """搜索相似向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            return_parent_pages: 是否返回父页面而不是chunks
            
        Returns:
            搜索结果列表
        """
        try:
            # 执行搜索
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "source", "timestamp", "page"]
            )
            
            # 处理搜索结果
            search_results = []
            seen_pages = set()  # 用于去重页面
            
            for hits in results:
                for hit in hits:
                    result = {
                        "distance": float(hit.distance),
                        "text": hit.entity.get("text", ""),
                        "source": hit.entity.get("source", ""),
                        "timestamp": hit.entity.get("timestamp", ""),
                        "page": hit.entity.get("page", 0)
                    }
                    
                    if return_parent_pages:
                        # 如果返回父页面，需要去重
                        page = result["page"]
                        if page not in seen_pages:
                            seen_pages.add(page)
                            search_results.append(result)
                    else:
                        search_results.append(result)
            
            return search_results
            
        except Exception as e:
            logger.info(f"搜索时出错: {str(e)}")
            return []
    
    def clear_collection(self):
        """清空集合并重新创建"""
        try:
            logger.info(f"正在清空集合: {self.collection_name}")
            utility.drop_collection(self.collection_name)
            logger.info("集合清空成功")
            # 重新创建集合
            self._create_collection()
            return True
        except Exception as e:
            logger.info(f"清空集合时出错: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息
        
        Returns:
            集合统计信息字典
        """
        try:
            if self.collection:
                # 刷新集合以确保获取最新数据
                self.collection.flush()
                
                # 使用 num_entities 获取实体数量
                row_count = self.collection.num_entities
                
                # 添加调试日志
                logger.info(f"集合 {self.collection_name} 当前实体数量: {row_count}")
                
                return {
                    "total_documents": row_count,
                    "total_vectors": row_count,
                    "collection_name": self.collection_name
                }
        except Exception as e:
            logger.error(f"获取集合统计信息时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
        
        return {"total_documents": 0, "total_vectors": 0, "collection_name": self.collection_name} 