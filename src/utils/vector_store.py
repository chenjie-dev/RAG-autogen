from typing import List, Dict
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from datetime import datetime

class VectorStore:
    """向量数据库管理类"""
    
    def __init__(self, host: str = "localhost", port: str = "19530", collection_name: str = "finance_knowledge"):
        """初始化向量数据库
        
        Args:
            host: Milvus主机地址
            port: Milvus端口
            collection_name: 集合名称
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.collection = None
        
        # 连接Milvus
        self._connect()
        
        # 确保集合存在
        self._ensure_collection()
    
    def _connect(self):
        """连接到Milvus数据库"""
        try:
            connections.connect(host=self.host, port=self.port)
            print("已连接 Milvus 服务。")
        except Exception as e:
            print(f"连接Milvus失败: {str(e)}")
            raise
    
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
        """清空集合"""
        try:
            if utility.has_collection(self.collection_name):
                utility.drop_collection(self.collection_name)
                print(f"已删除集合: {self.collection_name}")
        except Exception as e:
            print(f"删除集合时出错: {str(e)}")
    
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
                    "row_count": row_count,
                    "collection_name": self.collection_name
                }
        except Exception as e:
            print(f"获取集合统计信息时出错: {str(e)}")
        return {"row_count": 0, "collection_name": self.collection_name} 