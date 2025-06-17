from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import queue
import re

# 导入我们的RAG系统
from core.rag_finance_qa import FinanceRAGSystem
from utils.ui_utils import print_info, print_warning, print_error, print_success

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
try:
    rag_system = FinanceRAGSystem()
    print("RAG系统初始化成功")
except Exception as e:
    print(f"RAG系统初始化失败: {str(e)}")

processing_queue = queue.Queue()
processing_status = {"status": "idle", "message": "", "progress": 0}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'md', 'pptx', 'txt'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file_background(file_path, filename):
    """后台处理文件"""
    global processing_status, rag_system
    try:
        if rag_system is None:
            processing_status = {"status": "error", "message": "RAG系统未初始化", "progress": 0}
            return
        processing_status = {"status": "processing", "message": f"正在处理文件: {filename}", "progress": 10}
        
        # 添加文档到知识库
        rag_system.add_document(file_path)
        
        processing_status = {"status": "completed", "message": f"文件 {filename} 处理完成", "progress": 100}
        
        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass
            
    except Exception as e:
        processing_status = {"status": "error", "message": f"处理文件时出错: {str(e)}", "progress": 0}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

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
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # 保存文件到临时目录
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # 重置处理状态
        processing_status = {"status": "processing", "message": f"开始处理文件: {filename}", "progress": 0}
        
        # 在后台线程中处理文件
        thread = threading.Thread(target=process_file_background, args=(file_path, filename))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': '文件上传成功，正在处理中...'})
    
    return jsonify({'error': '不支持的文件格式'}), 400

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
        prompt = f"请结合以下检索到的内容和你自己的知识，回答用户问题：\n\n上下文：\n{context_text}\n\n问题：{question}\n\n答案："
        response = rag_system.ollama_client.chat(
            model='deepseek-r1:14b',
            messages=[{'role': 'user', 'content': prompt}]
        )
        answer = response['message']['content']
        
        # 分离思考内容和正式回答
        think_content, answer_content = separate_think_and_answer(answer)
        
        return jsonify({
            'think_content': think_content,
            'answer': answer_content,
            'context': context_text[:500] + "..." if len(context_text) > 500 else context_text,
            'sources': [hit["source"] for hit in context]
        })
    except Exception as e:
        return jsonify({'error': f'生成答案时出错: {str(e)}'}), 500

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
    
    try:
        context = rag_system.search_similar(question)
        context_text = "\n".join([hit["text"] for hit in context])
        prompt = f"请结合以下检索到的内容和你自己的知识，回答用户问题：\n\n上下文：\n{context_text}\n\n问题：{question}\n\n答案："
        
        def generate():
            try:
                # 使用流式输出
                stream = rag_system.ollama_client.chat(
                    model='deepseek-r1:14b',
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True
                )
                
                full_answer = ""
                in_think_block = False
                think_content = ""
                answer_content = ""
                think_complete = False
                buffer = ""  # 用于累积字符
                
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        
                        # 检测思考块的开始
                        if '<think>' in content:
                            in_think_block = True
                            # 发送思考开始标记
                            yield f"data: [THINK_START]\n\n"
                            # 移除<think>标签
                            content = content.replace('<think>', '')
                        
                        # 检测思考块的结束
                        if '</think>' in content:
                            in_think_block = False
                            think_complete = True
                            # 发送思考结束标记
                            yield f"data: [THINK_END]\n\n"
                            # 发送正式回答开始标记
                            yield f"data: [ANSWER_START]\n\n"
                            # 移除</think>标签
                            content = content.replace('</think>', '')
                        
                        # 处理缓冲区
                        buffer += content
                        
                        # 如果缓冲区中有完整的词或标点，就发送出去
                        while True:
                            # 查找下一个分割点
                            next_split = -1
                            for char in '，。！？、；：""''（）《》【】\n':
                                pos = buffer.find(char)
                                if pos != -1 and (next_split == -1 or pos < next_split):
                                    next_split = pos + 1
                            
                            # 如果没有找到分割点，并且缓冲区不够长，就继续等待
                            if next_split == -1 and len(buffer) < 5:
                                break
                            
                            # 如果没有找到分割点，但缓冲区足够长，就取前面的部分
                            if next_split == -1:
                                next_split = 5
                            
                            # 提取要发送的内容
                            to_send = buffer[:next_split].strip()
                            buffer = buffer[next_split:]
                            
                            # 如果有内容要发送
                            if to_send:
                                if in_think_block:
                                    think_content += to_send
                                    yield f"data: [THINK] {to_send}\n\n"
                                else:
                                    answer_content += to_send
                                    yield f"data: [ANSWER] {to_send}\n\n"
                        
                # 处理剩余的缓冲区内容
                if buffer.strip():
                    if in_think_block:
                        think_content += buffer
                        yield f"data: [THINK] {buffer.strip()}\n\n"
                    else:
                        answer_content += buffer
                        yield f"data: [ANSWER] {buffer.strip()}\n\n"
                
                # 如果没有检测到思考块，但已经开始回答，发送回答开始标记
                if not think_complete and answer_content.strip():
                    yield f"data: [ANSWER_START]\n\n"
                
                # 发送结束标记
                yield f"data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return app.response_class(
            generate(),
            mimetype='text/plain'
        )
        
    except Exception as e:
        return jsonify({'error': f'生成答案时出错: {str(e)}'}), 500

@app.route('/knowledge', methods=['POST'])
def add_knowledge():
    """添加知识"""
    global rag_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    data = request.get_json()
    text = data.get('text', '').strip()
    source = data.get('source', 'manual_input')
    
    if not text:
        return jsonify({'error': '文本内容不能为空'}), 400
    
    try:
        rag_system.add_knowledge([text], source=source)
        return jsonify({'message': '知识添加成功'})
    except Exception as e:
        return jsonify({'error': f'添加知识时出错: {str(e)}'}), 500

@app.route('/stats')
def get_stats():
    """获取系统统计信息"""
    global rag_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    try:
        stats = rag_system.vector_store.get_collection_stats()
        return jsonify(stats)
    except Exception as e:
        # 如果是集合不存在的错误，返回空集合状态
        if "collection not found" in str(e).lower():
            return jsonify({'row_count': 0, 'collection_name': rag_system.vector_store.collection_name})
        return jsonify({'error': f'获取统计信息时出错: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_knowledge_base():
    """清空知识库"""
    global rag_system
    if rag_system is None:
        return jsonify({'error': 'RAG系统未初始化'}), 500
    
    try:
        success = rag_system.clear_knowledge_base()
        if success:
            return jsonify({'message': '知识库已清空'})
        else:
            return jsonify({'error': '清空知识库失败'}), 500
    except Exception as e:
        return jsonify({'error': f'清空知识库时出错: {str(e)}'}), 500

if __name__ == '__main__':
    print("Web UI 启动中...")
    app.run(debug=False, host='0.0.0.0', port=5000) 