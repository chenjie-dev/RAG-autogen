"""
查询重写工具类
用于优化用户问题输入，使其更适合检索
"""

import re
import ollama
from typing import List, Dict, Any, Optional
from src.utils.logger import logger
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL


class QueryRewriter:
    """查询重写工具类"""
    
    def __init__(self):
        """初始化查询重写器"""
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        
        # 查询重写提示词模板
        self.rewrite_prompt_template = """你是一个专业的查询重写专家，专门优化用户问题以提升检索效果。

任务：将用户的自然语言问题重写为更适合检索的形式。

重写原则：
1. **保持原意**：确保重写后的查询与原始问题语义一致
2. **增加关键词**：添加相关的专业术语、同义词或相关概念
3. **结构化表达**：将复杂问题拆分为更具体的查询
4. **去除冗余**：移除不必要的修饰词，保留核心信息
5. **考虑上下文**：如果是金融相关问题，添加金融相关术语

重写策略：
- 对于"是什么"类问题：添加相关概念和术语
- 对于"如何"类问题：添加步骤、方法、流程等关键词
- 对于"为什么"类问题：添加原因、影响、因素等关键词
- 对于比较类问题：明确比较对象和维度
- 对于数据类问题：添加具体的数据类型、指标等

请将以下用户问题重写为更适合检索的形式：

原始问题：{original_query}

请提供3个不同角度的重写版本，每个版本用不同的策略：

1. 扩展版本（添加相关术语）：
2. 结构化版本（拆分为具体查询）：
3. 简化版本（保留核心信息）：

请确保重写后的查询更适合在文档库中进行语义检索。"""

        # 查询扩展提示词模板
        self.expand_prompt_template = """你是一个查询扩展专家，负责为用户的查询添加相关的同义词、近义词和相关概念。

任务：为给定的查询添加相关的词汇，以提升检索的召回率。

扩展原则：
1. **同义词扩展**：添加与查询词意思相同或相近的词汇
2. **上位词扩展**：添加更广泛的概念
3. **下位词扩展**：添加更具体的概念
4. **相关概念扩展**：添加语义相关的词汇
5. **专业术语扩展**：如果是专业领域，添加相关术语

请为以下查询进行扩展：

原始查询：{original_query}

请提供扩展后的查询，包含原始词汇和相关词汇，用空格分隔：

扩展查询："""

    def rewrite_query(self, original_query: str, strategy: str = "auto") -> Dict[str, Any]:
        """重写用户查询
        
        Args:
            original_query: 原始用户查询
            strategy: 重写策略 ("auto", "expand", "structure", "simplify")
            
        Returns:
            重写结果字典
        """
        try:
            logger.info(f"🔄 开始重写查询: {original_query}")
            logger.info(f"📋 使用策略: {strategy}")
            
            if strategy == "auto":
                # 自动选择策略，生成多个版本
                result = self._rewrite_with_multiple_strategies(original_query)
            else:
                # 使用指定策略
                result = self._rewrite_with_single_strategy(original_query, strategy)
            
            # 打印重写结果
            if result["success"]:
                logger.info(f"✅ 查询重写成功")
                logger.info(f"📝 原始查询: {result['original_query']}")
                logger.info(f"🔄 重写版本数量: {len(result['rewritten_queries'])}")
                for i, query in enumerate(result['rewritten_queries'], 1):
                    logger.info(f"   {i}. {query}")
            else:
                logger.warning(f"⚠️ 查询重写失败: {result.get('error', '未知错误')}")
            
            return result
                
        except Exception as e:
            logger.error(f"❌ 重写查询时出错: {str(e)}")
            return {
                "original_query": original_query,
                "rewritten_queries": [original_query],
                "strategy": strategy,
                "success": False,
                "error": str(e)
            }

    def _rewrite_with_multiple_strategies(self, original_query: str) -> Dict[str, Any]:
        """使用多种策略重写查询"""
        try:
            logger.info(f"🤖 使用多策略重写查询...")
            
            # 构建提示词
            prompt = self.rewrite_prompt_template.format(original_query=original_query)
            logger.info(f"📝 构建提示词完成，长度: {len(prompt)} 字符")
            
            # 调用LLM进行重写
            logger.info(f"🔄 调用LLM进行查询重写...")
            response = self.ollama_client.chat(
                model='deepseek-r1:14b',
                messages=[
                    {"role": "system", "content": "你是一个专业的查询重写专家。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response['message']['content']
            logger.info(f"📄 LLM响应长度: {len(content)} 字符")
            logger.info(f"📄 LLM响应预览: {content[:200]}...")
            
            # 解析重写结果
            logger.info(f"🔍 解析LLM响应...")
            rewritten_queries = self._parse_rewrite_response(content)
            
            # 如果没有解析到结果，使用原始查询
            if not rewritten_queries:
                logger.warning(f"⚠️ 解析失败，使用原始查询")
                rewritten_queries = [original_query]
            
            logger.info(f"✅ 多策略重写完成，生成 {len(rewritten_queries)} 个版本")
            
            return {
                "original_query": original_query,
                "rewritten_queries": rewritten_queries,
                "strategy": "multiple",
                "success": True,
                "llm_response": content
            }
            
        except Exception as e:
            logger.error(f"❌ 多策略重写失败: {str(e)}")
            return {
                "original_query": original_query,
                "rewritten_queries": [original_query],
                "strategy": "multiple",
                "success": False,
                "error": str(e)
            }

    def _rewrite_with_single_strategy(self, original_query: str, strategy: str) -> Dict[str, Any]:
        """使用单一策略重写查询"""
        try:
            logger.info(f"🎯 使用单策略重写查询，策略: {strategy}")
            
            if strategy == "expand":
                # 扩展策略
                prompt = self.expand_prompt_template.format(original_query=original_query)
            else:
                # 其他策略使用通用提示词
                prompt = f"""请使用{strategy}策略重写以下查询：

原始查询：{original_query}

重写后的查询："""
            
            logger.info(f"📝 构建提示词完成，长度: {len(prompt)} 字符")
            
            # 调用LLM进行重写
            logger.info(f"🔄 调用LLM进行查询重写...")
            response = self.ollama_client.chat(
                model='deepseek-r1:14b',
                messages=[
                    {"role": "system", "content": "你是一个专业的查询重写专家。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response['message']['content']
            logger.info(f"📄 LLM响应长度: {len(content)} 字符")
            logger.info(f"📄 LLM响应预览: {content[:200]}...")
            
            # 提取重写后的查询
            logger.info(f"🔍 提取重写后的查询...")
            rewritten_query = self._extract_rewritten_query(content)
            
            if not rewritten_query:
                logger.warning(f"⚠️ 提取失败，使用原始查询")
                rewritten_query = original_query
            
            logger.info(f"✅ 单策略重写完成，策略: {strategy}")
            
            return {
                "original_query": original_query,
                "rewritten_queries": [rewritten_query],
                "strategy": strategy,
                "success": True,
                "llm_response": content
            }
            
        except Exception as e:
            logger.error(f"❌ 单策略重写失败: {str(e)}")
            return {
                "original_query": original_query,
                "rewritten_queries": [original_query],
                "strategy": strategy,
                "success": False,
                "error": str(e)
            }

    def _parse_rewrite_response(self, content: str) -> List[str]:
        """解析LLM的重写响应"""
        try:
            logger.info(f"🔍 开始解析LLM响应...")
            queries = []
            
            # 尝试提取不同版本的重写结果
            lines = content.split('\n')
            logger.info(f"📄 响应行数: {len(lines)}")
            
            current_query = ""
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 跳过空行和标题行
                if not line or line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    continue
                
                # 如果行以冒号结尾，说明是标题
                if line.endswith('：') or line.endswith(':'):
                    continue
                
                # 提取查询内容
                if line and not line.startswith('-') and not line.startswith('•'):
                    # 清理查询文本
                    query = self._clean_query_text(line)
                    if query and len(query) > 5:  # 过滤太短的查询
                        queries.append(query)
                        logger.info(f"   📝 提取到查询 {len(queries)}: {query}")
            
            # 去重并限制数量
            unique_queries = list(dict.fromkeys(queries))  # 保持顺序的去重
            logger.info(f"🔄 去重后查询数量: {len(unique_queries)}")
            
            result = unique_queries[:5]  # 最多返回5个版本
            logger.info(f"✅ 最终返回查询数量: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 解析重写响应失败: {str(e)}")
            return []

    def _extract_rewritten_query(self, content: str) -> str:
        """从LLM响应中提取重写后的查询"""
        try:
            logger.info(f"🔍 开始提取重写后的查询...")
            lines = content.split('\n')
            logger.info(f"📄 响应行数: {len(lines)}")
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 跳过空行和标题
                if not line or line.startswith('扩展查询：') or line.startswith('重写后的查询：'):
                    continue
                
                # 提取第一个非空的有效查询
                query = self._clean_query_text(line)
                if query and len(query) > 5:
                    logger.info(f"✅ 提取到重写查询: {query}")
                    return query
            
            logger.warning(f"⚠️ 未找到有效的重写查询")
            return ""
            
        except Exception as e:
            logger.error(f"❌ 提取重写查询失败: {str(e)}")
            return ""

    def _clean_query_text(self, text: str) -> str:
        """清理查询文本"""
        try:
            original_text = text
            logger.debug(f"🧹 开始清理查询文本: {text}")
            
            # 移除多余的标点符号
            text = re.sub(r'^[：:]\s*', '', text)
            text = re.sub(r'^\d+\.\s*', '', text)
            
            # 移除引号
            text = text.strip('"\'')
            
            # 清理多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            if text != original_text:
                logger.debug(f"🧹 文本清理完成: '{original_text}' -> '{text}'")
            
            return text
            
        except Exception as e:
            logger.error(f"❌ 清理查询文本失败: {str(e)}")
            return text

    def expand_query_keywords(self, query: str) -> List[str]:
        """扩展查询关键词
        
        Args:
            query: 原始查询
            
        Returns:
            扩展后的关键词列表
        """
        try:
            logger.info(f"🔍 开始扩展查询关键词: {query}")
            
            # 简单的关键词扩展规则
            keywords = []
            
            # 基础关键词
            base_keywords = query.split()
            keywords.extend(base_keywords)
            logger.info(f"📝 基础关键词: {base_keywords}")
            
            # 金融相关扩展
            financial_terms = {
                '投资': ['投资', '投资策略', '投资组合', '投资风险', '投资收益'],
                '股票': ['股票', '股价', '股票市场', '股票投资', '股票分析'],
                '基金': ['基金', '投资基金', '基金净值', '基金收益', '基金风险'],
                '债券': ['债券', '债券投资', '债券收益', '债券风险', '债券市场'],
                '风险': ['风险', '风险管理', '风险评估', '风险控制', '投资风险'],
                '收益': ['收益', '收益率', '投资收益', '收益分析', '收益预测'],
                '市场': ['市场', '市场分析', '市场趋势', '市场风险', '市场预测'],
                '分析': ['分析', '财务分析', '技术分析', '基本面分析', '投资分析'],
                '报告': ['报告', '财务报告', '年度报告', '季度报告', '分析报告'],
                '财务': ['财务', '财务状况', '财务指标', '财务分析', '财务报表']
            }
            
            # 检查查询中的关键词并扩展
            expanded_count = 0
            for keyword in base_keywords:
                for term, expansions in financial_terms.items():
                    if term in keyword or keyword in term:
                        logger.info(f"📝 发现金融术语 '{term}'，扩展关键词")
                        keywords.extend(expansions[:2])  # 只添加前2个扩展词
                        expanded_count += 2
            
            logger.info(f"📝 扩展了 {expanded_count} 个关键词")
            
            # 去重并限制数量
            unique_keywords = list(dict.fromkeys(keywords))
            logger.info(f"🔄 去重后关键词数量: {len(unique_keywords)}")
            
            result = unique_keywords[:10]  # 最多返回10个关键词
            logger.info(f"✅ 关键词扩展完成，最终关键词: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 扩展查询关键词失败: {str(e)}")
            return query.split()

    def get_query_suggestions(self, query: str) -> List[str]:
        """获取查询建议
        
        Args:
            query: 原始查询
            
        Returns:
            查询建议列表
        """
        try:
            logger.info(f"💡 开始生成查询建议: {query}")
            suggestions = []
            
            # 更智能的查询类型识别和建议生成
            if '什么' in query or '是什么' in query or '定义' in query or '概念' in query:
                logger.info(f"📝 识别为定义类查询，生成相关建议")
                suggestions.extend([
                    f"{query} 详细说明",
                    f"{query} 具体含义",
                    f"{query} 相关概念",
                    f"{query} 背景介绍"
                ])
            elif '如何' in query or '怎么' in query:
                # 进一步细分"如何"类查询
                if any(word in query for word in ['表现', '业绩', '情况', '状态', '趋势']):
                    logger.info(f"📝 识别为表现分析类查询，生成相关建议")
                    suggestions.extend([
                        f"{query} 详细分析",
                        f"{query} 数据对比",
                        f"{query} 趋势分析",
                        f"{query} 影响因素"
                    ])
                else:
                    logger.info(f"📝 识别为方法类查询，生成相关建议")
                    suggestions.extend([
                        f"{query} 具体方法",
                        f"{query} 操作步骤",
                        f"{query} 实施流程",
                        f"{query} 注意事项"
                    ])
            elif '为什么' in query:
                logger.info(f"📝 识别为原因类查询，生成相关建议")
                suggestions.extend([
                    f"{query} 具体原因",
                    f"{query} 影响因素",
                    f"{query} 背景分析",
                    f"{query} 相关数据"
                ])
            elif any(word in query for word in ['表现', '业绩', '数据', '财务', '营收', '利润']):
                logger.info(f"📝 识别为数据分析类查询，生成相关建议")
                suggestions.extend([
                    f"{query} 详细数据",
                    f"{query} 对比分析",
                    f"{query} 趋势变化",
                    f"{query} 行业对比"
                ])
            elif any(word in query for word in ['比较', '对比', '差异', '区别']):
                logger.info(f"📝 识别为比较类查询，生成相关建议")
                suggestions.extend([
                    f"{query} 详细对比",
                    f"{query} 差异分析",
                    f"{query} 优劣势",
                    f"{query} 选择建议"
                ])
            else:
                logger.info(f"📝 识别为通用类查询，生成通用建议")
                # 通用建议
                suggestions.extend([
                    f"{query} 详细分析",
                    f"{query} 相关数据",
                    f"{query} 背景信息",
                    f"{query} 发展趋势"
                ])
            
            result = suggestions[:5]  # 最多返回5个建议
            logger.info(f"✅ 生成查询建议完成，共 {len(result)} 个建议")
            logger.info(f"📝 建议列表: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 生成查询建议失败: {str(e)}")
            return []

    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            查询意图分析结果
        """
        try:
            logger.info(f"🧠 开始分析查询意图: {query}")
            
            intent = {
                "type": "general",
                "confidence": 0.5,
                "keywords": [],
                "entities": [],
                "suggestions": []
            }
            
            # 分析查询类型
            logger.info(f"🔍 分析查询类型...")
            if any(word in query for word in ['什么', '是什么', '定义', '概念']):
                intent["type"] = "definition"
                intent["confidence"] = 0.8
                logger.info(f"📝 识别为定义类查询")
            elif any(word in query for word in ['如何', '怎么', '方法', '步骤']):
                intent["type"] = "how_to"
                intent["confidence"] = 0.8
                logger.info(f"📝 识别为方法类查询")
            elif any(word in query for word in ['为什么', '原因', '影响']):
                intent["type"] = "why"
                intent["confidence"] = 0.8
                logger.info(f"📝 识别为原因类查询")
            elif any(word in query for word in ['比较', '对比', '差异']):
                intent["type"] = "comparison"
                intent["confidence"] = 0.8
                logger.info(f"📝 识别为比较类查询")
            elif any(word in query for word in ['数据', '数字', '统计']):
                intent["type"] = "data"
                intent["confidence"] = 0.8
                logger.info(f"📝 识别为数据类查询")
            else:
                logger.info(f"📝 识别为通用类查询")
            
            # 提取关键词
            logger.info(f"🔍 提取关键词...")
            intent["keywords"] = self.expand_query_keywords(query)
            logger.info(f"📝 提取到关键词: {intent['keywords']}")
            
            # 生成建议
            logger.info(f"💡 生成查询建议...")
            intent["suggestions"] = self.get_query_suggestions(query)
            logger.info(f"📝 生成建议: {intent['suggestions']}")
            
            logger.info(f"✅ 查询意图分析完成")
            logger.info(f"📊 分析结果: {intent}")
            
            return intent
            
        except Exception as e:
            logger.error(f"❌ 分析查询意图失败: {str(e)}")
            return {
                "type": "general",
                "confidence": 0.5,
                "keywords": query.split(),
                "entities": [],
                "suggestions": []
            } 