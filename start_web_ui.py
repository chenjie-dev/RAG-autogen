#!/usr/bin/env python3
"""
Web UI独立启动脚本
==================

功能说明:
- 独立启动Web界面服务
- 提供图形化的文档上传和问答界面
- 支持流式回答和实时交互
- 可作为独立服务运行

使用方法:
    python3 start_web_ui.py

主要功能:
1. 文档上传和管理
2. 知识库查询和问答
3. 流式回答显示
4. 用户友好的Web界面

注意:
- 此脚本已被 start.py 统一管理
- 建议使用 start.py web 启动Web界面
- 保留此文件用于独立测试和开发

作者: RAG系统开发团队
版本: 1.0.0
更新日期: 2024
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import queue

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入配置
from config.settings import OLLAMA_BASE_URL, MILVUS_HOST, MILVUS_PORT

def check_dependencies():
    """检查依赖是否安装"""
    # 包名到模块名的映射
    package_mapping = {
        'flask': 'flask',
        'pymilvus': 'pymilvus',
        'sentence_transformers': 'sentence_transformers',
        'ollama': 'ollama',
        'pdfplumber': 'pdfplumber',
        'python-docx': 'docx',
        'markdown': 'markdown',
        'beautifulsoup4': 'bs4',
        'python-pptx': 'pptx'
    }
    
    missing_packages = []
    for package, module in package_mapping.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装:")
        print(f"pip3 install {' '.join(missing_packages)}")
        return False
    
    return True

def check_services():
    """检查必要服务是否运行"""
    print("检查服务状态...")
    
    # 检查Milvus服务
    try:
        from pymilvus import connections
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        print("✓ Milvus服务连接正常")
        connections.disconnect("default")
    except Exception as e:
        print(f"✗ Milvus服务连接失败: {e}")
        print("请确保Milvus服务正在运行")
        return False
    
    # 检查Ollama服务
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_BASE_URL)
        # 尝试列出模型
        models = client.list()
        print(f"✓ Ollama服务连接正常 ({OLLAMA_BASE_URL})")
    except Exception as e:
        print(f"✗ Ollama服务连接失败: {e}")
        print(f"请确保Ollama服务正在运行: {OLLAMA_BASE_URL}")
        return False
    
    return True

def start_web_ui():
    """启动Web UI"""
    print("启动Web UI...")
    
    # 检查web_ui.py是否存在
    if not os.path.exists('src/web/web_ui.py'):
        print("错误: src/web/web_ui.py 文件不存在")
        return False
    
    # 检查templates目录是否存在
    if not os.path.exists('templates'):
        print("错误: templates 目录不存在")
        return False
    
    # 检查index.html是否存在
    if not os.path.exists('templates/index.html'):
        print("错误: templates/index.html 文件不存在")
        return False
    
    print("✓ 所有文件检查通过")
    print("\n正在启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    
    try:
        # 启动Flask应用
        from src.web.web_ui import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("金融知识RAG问答系统 - Web UI")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖...")
    if not check_dependencies():
        return 1
    
    # 检查服务
    if not check_services():
        return 1
    
    # 启动Web UI
    if not start_web_ui():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 