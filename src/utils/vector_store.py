from typing import List, Dict
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from datetime import datetime
import os
import numpy as np
from sentence_transformers import SentenceTransformer

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
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print(f"正在连接到Milvus: {self.host}:{self.port}")
        
        # 连接Milvus，支持重试
        self._connect_with_retry()
        
        # 确保集合存在
        self._ensure_collection()
    
    def _connect_with_retry(self, max_retries: int = 5, retry_delay: int = 3):
        """带重试的Milvus连接"""
        for attempt in range(max_retries):
            try:
                connections.connect(host=self.host, port=self.port)
                print(f"✓ 成功连接到Milvus服务: {self.host}:{self.port}")
                return
            except Exception as e:
                print(f"✗ 尝试第 {attempt+1} 次连接Milvus失败: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"等待 {retry_delay} 秒后重试...")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"✗ 无法连接到Milvus服务，请检查服务是否正在运行")
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
                if not all(field in fields for field in ['source', 'timestamp']):
                    print("检测到集合模式需要更新，正在重新创建...")
                    # 删除旧集合
                    utility.drop_collection(self.collection_name)
                    # 创建新集合
                    self._create_collection()
                else:
                    print("使用现有集合")
                    self.collection = collection
                    self.collection.load()
            else:
                # 创建新集合
                self._create_collection()
        except Exception as e:
            print(f"检查集合时出错: {str(e)}")
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
            FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=32)
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
        print(f"成功创建集合 {self.collection_name} 并建立索引")
    
    def add_texts(self, texts: List[str], source: str = "unknown") -> bool:
        """添加文本到向量数据库
        
        Args:
            texts: 文本列表
            source: 来源信息
            
        Returns:
            是否成功添加
        """
        try:
            if not texts:
                print("文本列表为空")
                return False
            
            # 生成嵌入向量
            embeddings = self.embedding_model.encode(texts)
            embeddings_list = embeddings.tolist()
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamps = [timestamp] * len(texts)
            sources = [source] * len(texts)
            
            # 插入数据
            self.insert_data(texts, embeddings_list, sources, timestamps)
            return True
            
        except Exception as e:
            print(f"添加文本时出错: {str(e)}")
            return False
    
    def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """搜索相似文本
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            # 生成查询向量
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            
            # 执行搜索
            return self.search(query_embedding, top_k)
            
        except Exception as e:
            print(f"搜索相似文本时出错: {str(e)}")
            return []
    
    def insert_data(self, texts: List[str], embeddings: List[List[float]], sources: List[str], timestamps: List[str]):
        """插入数据到向量数据库
        
        Args:
            texts: 文本列表
            embeddings: 嵌入向量列表
            sources: 来源列表
            timestamps: 时间戳列表
        """
        try:
            # 准备插入数据
            entities = [
                texts,  # text
                embeddings,  # embedding
                sources,  # source
                timestamps  # timestamp
            ]
            
            # 插入数据
            self.collection.insert(entities)
            self.collection.flush()
            print(f"成功插入 {len(texts)} 条数据")
        except Exception as e:
            print(f"插入数据时出错: {str(e)}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """搜索相似向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        try:
            # 准备搜索参数
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            # 执行搜索
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "source", "timestamp"]
            )
            
            # 处理搜索结果
            similar_texts = []
            for hits in results:
                for hit in hits:
                    similar_texts.append({
                        "text": hit.entity.get("text"),
                        "source": hit.entity.get("source", "unknown"),
                        "timestamp": hit.entity.get("timestamp", "unknown"),
                        "distance": hit.distance
                    })
            return similar_texts
        except Exception as e:
            print(f"搜索时出错: {str(e)}")
            return []
    
    def clear_collection(self):
        """清空集合并重新创建"""
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                print(f"已删除集合: {self.collection_name}")
                # 重新创建集合
                self._create_collection()
                print(f"已重新创建集合: {self.collection_name}")
                return True
        except Exception as e:
            print(f"删除集合时出错: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息
        
        Returns:
            集合统计信息字典
        """
        try:
            if self.collection:
                # 使用 num_entities 替代 get_statistics
                row_count = self.collection.num_entities
                return {
                    "total_documents": row_count,
                    "total_vectors": row_count,
                    "collection_name": self.collection_name
                }
        except Exception as e:
            print(f"获取集合统计信息时出错: {str(e)}")
        return {"total_documents": 0, "total_vectors": 0, "collection_name": self.collection_name} 