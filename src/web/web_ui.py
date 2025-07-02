from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import queue
import re
import json
from flask import Response
import asyncio

# 导入我们的RAG系统
from core.rag_finance_qa import FinanceRAGSystem
from utils.ui_utils import print_info, print_warning, print_error, print_success
from utils.logger import logger

# 尝试导入AutoGen系统
try:
    from core.autogen_rag_system import AutoGenRAGSystem
    AUTOGEN_AVAILABLE = True
    logger.info("AutoGen智能体系统可用")
except ImportError as e:
    AUTOGEN_AVAILABLE = False
    logger.info(f"AutoGen智能体系统不可用: {str(e)}")

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量
rag_system = None
autogen_system = None
processing_queue = queue.Queue()
processing_status = {"status": "idle", "message": "", "progress": 0}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'md', 'pptx', 'txt'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    if not filename or '.' not in filename:
        logger.info(f"文件名无效或没有扩展名: {filename}")
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    logger.info(f"检查文件扩展名: {extension}")
    logger.info(f"允许的扩展名: {ALLOWED_EXTENSIONS}")
    
    is_allowed = extension in ALLOWED_EXTENSIONS
    logger.info(f"文件 {filename} 是否允许: {is_allowed}")
    
    return is_allowed

def initialize_systems():
    """初始化RAG系统"""
    global rag_system, autogen_system
    
    # 初始化传统RAG系统
    try:
        rag_system = FinanceRAGSystem()
        logger.info("传统RAG系统初始化成功")
    except Exception as e:
        logger.info(f"传统RAG系统初始化失败: {str(e)}")
    
    # 初始化AutoGen智能体系统
    if AUTOGEN_AVAILABLE:
        try:
            autogen_system = AutoGenRAGSystem()
            logger.info("AutoGen智能体系统初始化成功")
        except Exception as e:
            logger.info(f"AutoGen智能体系统初始化失败: {str(e)}")

def process_file_background(file_path, filename):
    """后台处理文件"""
    global processing_status, rag_system, autogen_system
    try:
        logger.info(f"开始后台处理文件: {filename}")
        logger.info(f"文件路径: {file_path}")
        
        if rag_system is None:
            logger.info("RAG系统未初始化")
            processing_status = {"status": "error", "message": "RAG系统未初始化", "progress": 0}
            return
        
        processing_status = {"status": "processing", "message": f"正在处理文件: {filename}", "progress": 10}
        
        # 添加文档到传统RAG系统
        logger.info(f"开始添加文档到RAG系统: {file_path}")
        rag_system.add_document(file_path)
        logger.info("文档已添加到RAG系统")
        
        # 如果AutoGen系统可用，也添加到AutoGen系统
        if autogen_system is not None:
            logger.info("开始添加文档到AutoGen系统")
            autogen_system.add_document(file_path)
            logger.info("文档已添加到AutoGen系统")
        
        processing_status = {"status": "completed", "message": f"文件 {filename} 处理完成", "progress": 100}
        logger.info(f"文件处理完成: {filename}")
        
        # 清理临时文件
        try:
            os.remove(file_path)
            logger.info(f"临时文件已清理: {file_path}")
        except Exception as e:
            logger.info(f"清理临时文件失败: {str(e)}")
            
    except Exception as e:
        logger.info(f"处理文件时出错: {str(e)}")
        import traceback
        logger.info(f"错误详情: {traceback.format_exc()}")
        processing_status = {"status": "error", "message": f"处理文件时出错: {str(e)}", "progress": 0}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/system_info')
def get_system_info():
    """获取系统信息"""
    return jsonify({
        'traditional_rag': rag_system is not None,
        'autogen_available': AUTOGEN_AVAILABLE,
        'autogen_system': autogen_system is not None
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    global processing_status, rag_system
    
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 记录原始文件名
    original_filename = file.filename
    logger.info(f"上传文件: {original_filename}")
    
    if file and allowed_file(original_filename):
        # 使用自定义的安全文件名处理函数
        filename = safe_filename(original_filename)
        
        logger.info(f"处理后的文件名: {filename}")
        
        # 保存文件到临时目录
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        logger.info(f"文件保存到: {file_path}")
        
        # 重置处理状态
        processing_status = {"status": "processing", "message": f"开始处理文件: {filename}", "progress": 0}
        
        # 在后台线程中处理文件
        thread = threading.Thread(target=process_file_background, args=(file_path, filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': '文件上传成功，正在处理中...'})
    
    logger.info(f"不支持的文件格式: {original_filename}")
    return jsonify({'error': f'不支持的文件格式: {original_filename}'}), 400

@app.route('/status')
def get_status():
    """获取处理状态"""
    return jsonify(processing_status)

@app.route('/ask', methods=['POST'])
def ask_question():
    """处理问答请求"""
    global rag_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    try:
        context = rag_system.search_similar(question)
        context_text = "\n".join([hit["text"] for hit in context])
        if context:
            # 只显示文档名称，不显示页码
            sources = list(set([hit["source"] for hit in context]))
            sources_text = "、".join(sources)
            prompt = f"""请结合以下检索到的内容和你自己的知识，回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理
7. 用中文回答，语言要自然流畅
8. 在回答末尾标注信息来源的文档名称

检索到的信息：
{context_text}

问题：{question}

答案："""
        else:
            prompt = f"""请结合以下检索到的内容和你自己的知识，回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理

上下文：
{context_text}

问题：{question}

答案："""
        response = rag_system.ollama_client.chat(
            model='deepseek-r1:14b',
            messages=[{'role': 'user', 'content': prompt}]
        )
        answer = response['message']['content']
        think_content, answer_content = separate_think_and_answer(answer)
        result = {
            'think_content': think_content,
            'answer': answer_content,
            'context': context_text[:500] + "..." if len(context_text) > 500 else context_text,
            'sources': [hit["source"] for hit in context],
            'pages': [hit.get("page", 0) for hit in context],
            'return_parent_pages': True
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'生成答案时出错: {str(e)}'}), 500

@app.route('/ask_autogen', methods=['POST'])
def ask_question_autogen():
    """处理AutoGen智能体问答请求"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen智能体系统未初始化'}), 500
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    try:
        answer = autogen_system.answer_question(question)
        result = {
            'answer': answer,
            'status': 'success',
            'framework': 'AutoGen',
            'agents_involved': ['retrieval_agent', 'analysis_agent', 'answer_agent', 'coordinator'],
            'return_parent_pages': True
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'AutoGen智能体协作失败: {str(e)}'}), 500

@app.route('/ask_stream', methods=['POST'])
def ask_question_stream():
    """流式问答接口，支持打字机效果，区分思考内容和正式回答"""
    global rag_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    def generate():
        try:
            # 发送开始标记
            yield f"data: {json.dumps({'type': 'start', 'message': '开始检索相关信息...'})}\n\n"
            
            # 检索相关信息
            context = rag_system.search_similar(question)
            context_text = "\n".join([hit["text"] for hit in context])
            
            # 构建思考过程
            if context:
                # 只显示文档名称，不显示页码
                sources = list(set([hit["source"] for hit in context]))
                sources_text = "、".join(sources)
                think_content = f"检索到的相关信息（来源文档：{sources_text}）：\n{context_text[:300]}...\n\n基于检索结果，我将生成答案。"
            else:
                think_content = f"检索到的相关信息：\n{context_text[:300]}...\n\n基于检索结果，我将生成答案。"
            
            # 发送思考过程
            yield f"data: {json.dumps({'type': 'think', 'content': think_content})}\n\n"
            
            # 构建提示词
            if context:
                # 只显示文档名称，不显示页码
                sources = list(set([hit["source"] for hit in context]))
                sources_text = "、".join(sources)
                prompt = f"""请结合以下检索到的内容和你自己的知识，回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理
7. 用中文回答，语言要自然流畅
8. 在回答末尾标注信息来源的文档名称

检索到的信息：
{context_text}

问题：{question}

答案："""
            else:
                prompt = f"""请结合以下检索到的内容和你自己的知识，回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理

上下文：
{context_text}

问题：{question}

答案："""
            
            # 使用流式输出
            stream = rag_system.ollama_client.chat(
                model='deepseek-r1:14b',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            
            full_answer = ""
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_answer += content
                    
                    # 发送回答内容
                    yield f"data: {json.dumps({'type': 'answer', 'content': content})}\n\n"
            
            # 构建完成数据
            complete_data = {
                'type': 'complete', 
                'answer': full_answer, 
                'think': think_content,
                'sources': [hit["source"] for hit in context]
            }
            
            # 构建完成数据
            complete_data = {
                'type': 'complete',
                'answer': full_answer,
                'think': think_content,
                'status': 'success',
                'framework': 'AutoGen',
                'agents_involved': ['retrieval_agent', 'analysis_agent', 'answer_agent', 'coordinator'],
                'sources': [hit["source"] for hit in context],
                'pages': [hit.get("page", 0) for hit in context],
                'return_parent_pages': True
            }
            
            # 发送完成标记
            yield f"data: {json.dumps(complete_data)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/ask_stream_autogen', methods=['POST'])
def ask_question_stream_autogen():
    """AutoGen智能体流式问答接口"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen智能体系统未初始化'}), 500
    
    data = request.get_json()
    question = data.get('question', '').strip()
    fast_mode = data.get('fast_mode', True)  # 默认使用快速模式
    
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    def generate():
        try:
            # 发送开始标记
            mode_text = "快速模式" if fast_mode else "完整模式"
            page_text = "（启用父页面检索）" if return_parent_pages else ""
            yield f"data: {json.dumps({'type': 'start', 'message': f'智能体开始协作（{mode_text}）{page_text}...'})}\n\n"
            
            # 发送检索智能体状态
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': '检索智能体', 'message': '正在检索相关信息...'})}\n\n"
            
            # 执行智能体协作
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(autogen_system.answer_question_async(question, fast_mode=fast_mode))
            loop.close()
            
            # 构建思考过程
            think_content = ""
            if result.get('context'):
                think_content += f"检索到的相关信息：\n{result.get('context', '')[:500]}...\n\n"
            if result.get('analysis'):
                think_content += f"分析结果：\n{result.get('analysis', '')}\n\n"
            
            if fast_mode:
                think_content += f"使用快速模式，直接基于检索结果生成答案。"
            else:
                think_content += f"使用完整模式，经过多智能体协作生成答案。"
            
            # 发送思考过程
            yield f"data: {json.dumps({'type': 'think', 'content': think_content})}\n\n"
            
            if not fast_mode:
                # 完整模式才显示这些状态
                yield f"data: {json.dumps({'type': 'agent_status', 'agent': '分析智能体', 'message': '正在分析检索结果...'})}\n\n"
                yield f"data: {json.dumps({'type': 'agent_status', 'agent': '回答智能体', 'message': '正在生成最终答案...'})}\n\n"
            
            # 获取答案内容
            answer = result.get('answer', '智能体协作未能生成有效答案')
            
            if fast_mode:
                # 快速模式：使用真正的流式输出
                # 构建提示词
                context_text = result.get('context', '')
                prompt = f"""基于以下检索到的信息，请直接回答用户问题。

要求：
1. 使用markdown格式回答
2. 段落之间用空行分隔
3. 重要信息用**粗体**标记
4. 列表使用- 或1. 格式
5. 代码用`代码`格式
6. 回答要准确、完整、有条理
7. 用中文回答，语言要自然流畅
8. 在回答末尾标注信息来源的文档名称

检索到的信息：
{context_text}

用户问题：{question}

答案："""
                
                # 使用流式输出
                stream = autogen_system.answer_agent.client.chat(
                    model='deepseek-r1:14b',
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True,
                    options={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 1000
                    }
                )
                
                full_answer = ""
                
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        full_answer += content
                        
                        # 发送回答内容
                        yield f"data: {json.dumps({'type': 'answer', 'content': content})}\n\n"
                
                # 发送完成标记
                yield f"data: {json.dumps({'type': 'complete', 'answer': full_answer, 'think': think_content})}\n\n"
            else:
                # 完整模式：逐字符发送（因为答案已经生成完成）
                for char in answer:
                    yield f"data: {json.dumps({'type': 'answer', 'content': char})}\n\n"
                
                # 发送完成标记
                yield f"data: {json.dumps({'type': 'complete', 'answer': answer, 'think': think_content})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'智能体协作失败: {str(e)}'})}\n\n"
    
    return Response(generate(), mimetype='text/plain')

def separate_think_and_answer(text):
    """分离思考内容和正式回答"""
    if not text:
        return "", ""
    
    import re
    
    # 提取<think>...</think>块中的内容
    think_pattern = r'<think>(.*?)</think>'
    think_match = re.search(think_pattern, text, flags=re.DOTALL)
    think_content = think_match.group(1).strip() if think_match else ""
    
    # 移除<think>...</think>块，得到正式回答
    answer_content = re.sub(think_pattern, '', text, flags=re.DOTALL)
    answer_content = re.sub(r'\n\s*\n', '\n\n', answer_content)  # 清理多余的空行
    answer_content = answer_content.strip()
    
    return think_content, answer_content

@app.route('/knowledge', methods=['POST'])
def add_knowledge():
    """添加知识到知识库"""
    global rag_system, autogen_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    data = request.get_json()
    texts = data.get('texts', [])
    source = data.get('source', 'manual_input')
    
    if not texts:
        return jsonify({'error': '知识内容不能为空'}), 400
    
    try:
        # 添加到传统RAG系统
        rag_system.add_knowledge(texts, source)
        
        # 如果AutoGen系统可用，也添加到AutoGen系统
        if autogen_system is not None:
            autogen_system.add_knowledge(texts, source)
        
        return jsonify({'message': '知识添加成功'})
    except Exception as e:
        return jsonify({'error': f'添加知识失败: {str(e)}'}), 500

@app.route('/stats')
def get_stats():
    """获取系统统计信息"""
    global rag_system, autogen_system
    
    try:
        # 获取传统RAG系统统计
        collection_stats = rag_system.vector_store.get_collection_stats()
        
        stats = {
            'total_documents': collection_stats.get('total_documents', 0),
            'total_vectors': collection_stats.get('total_vectors', 0),
            'traditional_rag': True,
            'autogen_available': AUTOGEN_AVAILABLE,
            'autogen_system': autogen_system is not None
        }
        
        # 如果AutoGen系统可用，添加AutoGen统计
        if autogen_system is not None:
            agent_status = autogen_system.get_agent_status()
            stats['autogen_agents'] = len(agent_status.get('agents', []))
            stats['autogen_status'] = agent_status.get('system_status', 'unknown')
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_knowledge_base():
    """清空知识库"""
    global rag_system, autogen_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    try:
        # 清空传统RAG系统
        success = rag_system.clear_knowledge_base()
        
        # 如果AutoGen系统可用，也清空AutoGen系统
        if autogen_system is not None:
            autogen_system.clear_knowledge_base()
        
        if success:
            return jsonify({'message': '知识库已清空'})
        else:
            return jsonify({'error': '清空知识库失败'}), 500
    except Exception as e:
        return jsonify({'error': f'清空知识库失败: {str(e)}'}), 500

def safe_filename(original_filename: str) -> str:
    """安全地处理文件名，保留可读性但确保安全性"""
    import re
    import unicodedata
    
    if not original_filename:
        return "unknown_file"
    
    # 分离文件名和扩展名
    name, ext = os.path.splitext(original_filename)
    
    # 规范化Unicode字符
    name = unicodedata.normalize('NFKC', name)
    
    # 替换不安全字符，但保留中文字符
    # 只替换真正危险的字符，保留空格、中文、数字、字母等
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    
    # 移除首尾的空格和点
    name = name.strip(' .')
    
    # 如果文件名为空，使用默认名称
    if not name:
        name = "document"
    
    # 限制文件名长度（不包括扩展名）
    if len(name) > 100:
        name = name[:100]
    
    # 重新组合文件名和扩展名
    safe_filename = name + ext.lower()
    
    logger.info(f"文件名处理: {original_filename} -> {safe_filename}")
    
    return safe_filename

# 初始化系统
initialize_systems()

if __name__ == '__main__':
    logger.info("Web UI 启动中...")
    app.run(debug=False, host='0.0.0.0', port=5000) 