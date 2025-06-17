import re
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

class TextUtils:
    """文本处理工具类"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """初始化文本处理工具
        
        Args:
            model_name: 使用的嵌入模型名称
        """
        self.model = SentenceTransformer(model_name)
    
    def split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """将长文本分割成较小的块
        
        Args:
            text: 要分割的文本
            max_length: 每个块的最大长度
            
        Returns:
            文本块列表
        """
        # 按段落分割
        paragraphs = text.split('\n\n')
        blocks = []
        current_block = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果段落本身超过最大长度，需要进一步分割
            if len(para) > max_length:
                # 如果当前块不为空，先保存
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                    current_length = 0
                
                # 按句子分割长段落
                sentences = re.split(r'([.!?。！？])', para)
                temp_sentences = []
                for i in range(0, len(sentences)-1, 2):
                    if i+1 < len(sentences):
                        sentence = sentences[i] + sentences[i+1]
                    else:
                        sentence = sentences[i]
                        
                    if len(sentence) > max_length:
                        # 如果单个句子太长，按逗号分割
                        parts = re.split(r'([,，])', sentence)
                        for j in range(0, len(parts)-1, 2):
                            if j+1 < len(parts):
                                part = parts[j] + parts[j+1]
                            else:
                                part = parts[j]
                                
                            if current_length + len(part) <= max_length:
                                current_block.append(part)
                                current_length += len(part)
                            else:
                                if current_block:
                                    blocks.append('\n'.join(current_block))
                                current_block = [part]
                                current_length = len(part)
                    else:
                        if current_length + len(sentence) <= max_length:
                            current_block.append(sentence)
                            current_length += len(sentence)
                        else:
                            if current_block:
                                blocks.append('\n'.join(current_block))
                            current_block = [sentence]
                            current_length = len(sentence)
            else:
                if current_length + len(para) <= max_length:
                    current_block.append(para)
                    current_length += len(para)
                else:
                    if current_block:
                        blocks.append('\n'.join(current_block))
                    current_block = [para]
                    current_length = len(para)
        
        # 添加最后一个块
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
            
        Returns:
            相似度分数 (0-1)
        """
        # 生成文本的嵌入向量
        embedding1 = self.model.encode([text1])[0]
        embedding2 = self.model.encode([text2])[0]
        
        # 计算余弦相似度
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return float(similarity)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量数组
        """
        return self.model.encode(texts) 