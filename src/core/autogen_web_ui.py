"""
基于AutoGen智能体框架的Web UI系统
====================================

功能特性:
- 智能体状态监控：实时显示各智能体状态
- 协作流程可视化：展示智能体协作过程
- 流式回答：支持实时显示智能体回答过程
- 智能体管理：可以启动/停止特定智能体
- 性能监控：监控智能体协作效率

作者: RAG系统开发团队
版本: 2.0.0
更新日期: 2024
"""

from flask import Flask, render_template, request, jsonify, Response, stream_template
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import queue
import json
import asyncio
from typing import Dict, Any, List

# 导入AutoGen智能体系统
from core.autogen_rag_system import AutoGenRAGSystem
from utils.ui_utils import print_info, print_warning, print_error, print_success

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'autogen-rag-secret-key'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量
autogen_system = None
processing_queue = queue.Queue()
processing_status = {"status": "idle", "message": "", "progress": 0}
agent_status = {"agents": [], "system_status": "stopped"}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'md', 'pptx', 'txt'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_autogen_system():
    """初始化AutoGen智能体系统"""
    global autogen_system, agent_status
    try:
        autogen_system = AutoGenRAGSystem()
        agent_status = autogen_system.get_agent_status()
        print_success("AutoGen智能体系统初始化成功")
        return True
    except Exception as e:
        print_error(f"AutoGen智能体系统初始化失败: {str(e)}")
        return False

def process_file_background(file_path, filename):
    """后台处理文件"""
    global processing_status, autogen_system
    try:
        if autogen_system is None:
            processing_status = {"status": "error", "message": "AutoGen系统未初始化", "progress": 0}
            return
        processing_status = {"status": "processing", "message": f"正在处理文件: {filename}", "progress": 10}
        
        # 添加文档到知识库
        autogen_system.add_document(file_path)
        
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
    return render_template('autogen_index.html')

@app.route('/api/status')
def get_system_status():
    """获取系统状态"""
    global autogen_system, agent_status
    if autogen_system:
        agent_status = autogen_system.get_agent_status()
    
    return jsonify({
        "system_status": "running" if autogen_system else "stopped",
        "agent_status": agent_status,
        "processing_status": processing_status
    })

@app.route('/api/agents')
def get_agents():
    """获取智能体信息"""
    global autogen_system
    if autogen_system:
        return jsonify(autogen_system.get_agent_status())
    else:
        return jsonify({"error": "AutoGen系统未初始化"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    global processing_status, autogen_system
    
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
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

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """处理问答请求（智能体协作模式）"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    try:
        # 使用智能体协作模式回答问题
        answer = autogen_system.answer_question(question)
        
        return jsonify({
            'answer': answer,
            'status': 'success',
            'framework': 'AutoGen',
            'agents_involved': ['retrieval_agent', 'analysis_agent', 'answer_agent', 'coordinator']
        })
    except Exception as e:
        return jsonify({'error': f'智能体协作失败: {str(e)}'}), 500

@app.route('/api/ask_stream', methods=['POST'])
def ask_question_stream():
    """流式问答接口（智能体协作模式）"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    
    def generate():
        try:
            # 发送开始标记
            yield f"data: {json.dumps({'type': 'start', 'message': '智能体开始协作...'})}\n\n"
            
            # 发送检索智能体状态
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'retrieval_agent', 'status': 'working', 'message': '正在检索相关信息...'})}\n\n"
            
            # 执行智能体协作
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(autogen_system.answer_question_async(question))
            loop.close()
            
            # 发送分析智能体状态
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'analysis_agent', 'status': 'working', 'message': '正在分析检索结果...'})}\n\n"
            
            # 发送回答智能体状态
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': 'answer_agent', 'status': 'working', 'message': '正在生成最终答案...'})}\n\n"
            
            # 发送最终答案
            answer = result.get('answer', '智能体协作未能生成有效答案')
            yield f"data: {json.dumps({'type': 'answer', 'content': answer})}\n\n"
            
            # 发送完成标记
            yield f"data: {json.dumps({'type': 'end', 'message': '智能体协作完成'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'智能体协作失败: {str(e)}'})}\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/api/knowledge', methods=['POST'])
def add_knowledge():
    """添加知识到知识库"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    data = request.get_json()
    texts = data.get('texts', [])
    source = data.get('source', 'manual_input')
    
    if not texts:
        return jsonify({'error': '知识内容不能为空'}), 400
    
    try:
        # 使用原有方法添加知识
        autogen_system.add_knowledge(texts, source)
        return jsonify({'message': '知识添加成功'})
    except Exception as e:
        return jsonify({'error': f'添加知识失败: {str(e)}'}), 500

@app.route('/api/stats')
def get_stats():
    """获取系统统计信息"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    try:
        # 获取向量数据库统计信息
        collection_stats = autogen_system.vector_store.get_collection_stats()
        
        return jsonify({
            'total_documents': collection_stats.get('total_documents', 0),
            'total_vectors': collection_stats.get('total_vectors', 0),
            'framework': 'AutoGen',
            'version': '2.0.0',
            'agents': len(autogen_system.get_agent_status().get('agents', []))
        })
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@app.route('/api/clear', methods=['POST'])
def clear_knowledge_base():
    """清空知识库"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    try:
        success = autogen_system.clear_knowledge_base()
        if success:
            return jsonify({'message': '知识库已清空'})
        else:
            return jsonify({'error': '清空知识库失败'}), 500
    except Exception as e:
        return jsonify({'error': f'清空知识库失败: {str(e)}'}), 500

@app.route('/api/agents/restart', methods=['POST'])
def restart_agents():
    """重启智能体系统"""
    global autogen_system, agent_status
    try:
        # 重新初始化系统
        success = initialize_autogen_system()
        if success:
            return jsonify({'message': '智能体系统重启成功'})
        else:
            return jsonify({'error': '智能体系统重启失败'}), 500
    except Exception as e:
        return jsonify({'error': f'重启失败: {str(e)}'}), 500

@app.route('/api/agents/status/<agent_name>')
def get_agent_status(agent_name):
    """获取特定智能体状态"""
    global autogen_system
    if autogen_system is None:
        return jsonify({'error': 'AutoGen系统未初始化'}), 500
    
    try:
        agent_status = autogen_system.get_agent_status()
        for agent in agent_status.get('agents', []):
            if agent['name'] == agent_name:
                return jsonify(agent)
        
        return jsonify({'error': f'智能体 {agent_name} 不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'获取智能体状态失败: {str(e)}'}), 500

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AutoGen智能体RAG问答系统 - Web UI")
    print("=" * 60)
    
    # 初始化AutoGen系统
    if not initialize_autogen_system():
        print_error("AutoGen系统初始化失败，退出程序")
        return 1
    
    # 启动Web服务器
    print_info("启动Web服务器...")
    print_info("访问地址: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 