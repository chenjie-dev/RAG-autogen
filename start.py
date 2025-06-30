#!/usr/bin/env python3
"""
金融知识RAG问答系统 - 统一启动脚本
====================================

功能说明:
- 系统状态检查: 检查依赖包、服务连接状态
- 命令行模式: 启动交互式命令行问答界面
- Web UI模式: 启动Flask Web服务器，提供图形化界面
- 统一入口: 提供单一启动点，简化系统使用

使用方法:
    python3 start.py [mode] [options]
    
参数:
    mode: cli(命令行) | web(Web界面) | status(状态检查)
    --check: 仅检查系统状态，不启动服务

示例:
    python3 start.py status      # 检查系统状态
    python3 start.py cli         # 启动命令行模式
    python3 start.py web         # 启动Web界面
    python3 start.py --check     # 仅检查依赖和服务

作者: RAG系统开发团队
版本: 1.0.0
更新日期: 2024
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 导入配置
from config.settings import OLLAMA_BASE_URL, MILVUS_HOST, MILVUS_PORT

def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("🚀 金融知识RAG问答系统 (DocLing增强版)")
    print("=" * 60)
    print("功能特性:")
    print("  • 高级PDF处理 (DocLing精确布局识别)")
    print("  • 多格式文档处理 (PDF, DOCX, MD, PPTX, TXT)")
    print("  • 智能问答系统")
    print("  • 向量数据库存储")
    print("  • Web界面和命令行界面")
    print("=" * 60)

def check_dependencies():
    """检查依赖是否安装"""
    print("📦 检查依赖包...")
    
    # 包名到模块名的映射
    package_mapping = {
        'flask': 'flask',
        'pymilvus': 'pymilvus',
        'sentence_transformers': 'sentence_transformers',
        'ollama': 'ollama',
        'docling-core': 'docling_core',
        'docling': 'docling',
        'pypdfium2': 'pypdfium2',
        'python-docx': 'docx',
        'markdown': 'markdown',
        'beautifulsoup4': 'bs4',
        'python-pptx': 'pptx'
    }
    
    missing_packages = []
    for package, module in package_mapping.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"    - {package}")
        print(f"\n请运行以下命令安装:")
        print(f"pip3 install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖包检查通过")
    return True

def check_services():
    """检查必要服务是否运行"""
    print("\n🔍 检查服务状态...")
    
    # 检查Milvus服务
    try:
        from pymilvus import connections
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        print("  ✅ Milvus服务连接正常")
        connections.disconnect("default")
    except Exception as e:
        print(f"  ❌ Milvus服务连接失败: {e}")
        print("    请确保Milvus服务正在运行")
        return False
    
    # 检查Ollama服务
    try:
        import ollama
        client = ollama.Client(host=OLLAMA_BASE_URL)
        models = client.list()
        print(f"  ✅ Ollama服务连接正常 ({OLLAMA_BASE_URL})")
    except Exception as e:
        print(f"  ❌ Ollama服务连接失败: {e}")
        print(f"    请确保Ollama服务正在运行: {OLLAMA_BASE_URL}")
        return False
    
    return True

def start_cli_mode():
    """启动命令行模式"""
    print("\n🖥️  启动命令行模式...")
    try:
        from core.rag_finance_qa import main
        main()
    except KeyboardInterrupt:
        print("\n👋 命令行模式已退出")
    except Exception as e:
        print(f"❌ 启动命令行模式失败: {e}")

def start_web_ui():
    """启动Web UI模式"""
    print("\n🌐 启动Web UI模式...")
    
    # 检查必要文件
    required_files = ['src/web/web_ui.py', 'templates/index.html']
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少必要文件: {file_path}")
            return False
    
    print("✅ 所有文件检查通过")
    print("🌐 正在启动Web服务器...")
    print("📱 访问地址: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止服务")
    
    try:
        from web.web_ui import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Web UI已停止")
    except Exception as e:
        print(f"❌ 启动Web UI失败: {e}")
        return False
    
    return True

def show_status():
    """显示系统状态"""
    print("\n📊 系统状态:")
    
    # 检查文件
    files = {
        'src/core/rag_finance_qa.py': 'RAG系统核心',
        'src/web/web_ui.py': 'Web UI服务',
        'templates/index.html': 'Web界面模板',
        'src/processors/document_processor.py': '文档处理器',
        'src/utils/text_utils.py': '文本工具',
        'src/utils/vector_store.py': '向量数据库',
        'src/utils/ui_utils.py': 'UI工具'
    }
    
    for file_path, description in files.items():
        status = "✅" if os.path.exists(file_path) else "❌"
        print(f"  {status} {description}: {file_path}")
    
    # 检查依赖和服务
    deps_ok = check_dependencies()
    services_ok = check_services()
    
    if deps_ok and services_ok:
        print("\n🎉 系统状态良好，可以正常启动！")
    else:
        print("\n⚠️  系统存在问题，请先解决上述问题")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='金融知识RAG问答系统启动脚本')
    parser.add_argument('mode', nargs='?', choices=['cli', 'web', 'status'], 
                       default='cli', help='启动模式: cli(命令行), web(Web界面), status(状态检查)')
    parser.add_argument('--check', action='store_true', help='仅检查依赖和服务状态')
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.check:
        show_status()
        return
    
    # 检查依赖和服务
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装缺失的包")
        return
    
    if not check_services():
        print("\n❌ 服务检查失败，请确保Milvus和Ollama服务正在运行")
        return
    
    # 根据模式启动
    if args.mode == 'cli':
        start_cli_mode()
    elif args.mode == 'web':
        start_web_ui()
    elif args.mode == 'status':
        show_status()

if __name__ == "__main__":
    main() 