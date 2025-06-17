from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import queue

# 导入我们的RAG系统
from core.rag_finance_qa import FinanceRAGSystem
from utils.ui_utils import print_info, print_warning, print_error, print_success

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
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
        return jsonify({
            'answer': answer,
            'context': context_text[:500] + "..." if len(context_text) > 500 else context_text,
            'sources': [hit["source"] for hit in context]
        })
    except Exception as e:
        return jsonify({'error': f'生成答案时出错: {str(e)}'}), 500

@app.route('/ask_stream', methods=['POST'])
def ask_question_stream():
    """流式问答接口，支持打字机效果"""
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
                for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        # 跳过思考过程
                        if content.startswith('<think>'):
                            continue
                        full_answer += content
                        # 发送每个字符
                        yield f"data: {content}\n\n"
                
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
        return jsonify({'error': f'获取统计信息时出错: {str(e)}'}), 500

if __name__ == '__main__':
    print("Web UI 启动中...")
    app.run(debug=False, host='0.0.0.0', port=5000) 