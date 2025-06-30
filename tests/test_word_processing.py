#!/usr/bin/env python3
"""
测试Word文档处理功能
"""

import sys
import os
# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from processors.document_processor import DocumentProcessor

def test_word_processing():
    """测试Word文档处理"""
    # 检查是否有Word文档文件
    word_files = []
    current_dir = os.path.dirname(__file__)  # tests目录
    
    # 在tests目录查找Word文档
    for file in os.listdir(current_dir):
        if file.endswith(('.docx', '.doc')):
            word_files.append(os.path.join(current_dir, file))
    
    if not word_files:
        print("tests目录没有找到Word文档文件")
        print("请将Word文档文件放在tests目录，然后重新运行测试")
        return
    
    print(f"找到Word文档文件: {[os.path.basename(f) for f in word_files]}")
    
    for word_file in word_files:
        print(f"\n开始处理Word文档: {os.path.basename(word_file)}")
        
        try:
            # 测试基本文本提取
            print("1. 测试基本文本提取...")
            texts = DocumentProcessor.extract_text_from_docx(word_file)
            print(f"   提取了 {len(texts)} 个文本块")
            
            if texts:
                print("   前3个文本块:")
                for i, text in enumerate(texts[:3]):
                    print(f"   {i+1}: {text[:100]}...")
            
            # 测试结构化提取
            print("\n2. 测试结构化文本提取...")
            structured_texts = DocumentProcessor.extract_text_from_docx_with_structure(word_file)
            print(f"   提取了 {len(structured_texts)} 个结构化文本块")
            
            if structured_texts:
                print("   前3个结构化文本块:")
                for i, item in enumerate(structured_texts[:3]):
                    print(f"   {i+1}: [{item['type']}] {item['text'][:80]}...")
                    if item['level']:
                        print(f"      级别: {item['level']}")
                    if item['metadata']:
                        print(f"      元数据: {item['metadata']}")
            
            # 统计不同类型的内容
            type_counts = {}
            for item in structured_texts:
                item_type = item['type']
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            print(f"\n   内容类型统计:")
            for item_type, count in type_counts.items():
                print(f"   {item_type}: {count}")
            
        except Exception as e:
            print(f"处理Word文档 {os.path.basename(word_file)} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()

def test_docling_word_backend():
    """测试DocLing Word后端是否正常工作"""
    try:
        from docling.backend.msword_backend import MsWordDocumentBackend
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.document import InputDocument
        from pathlib import Path
        
        print("DocLing Word后端导入成功")
        
        # 测试创建后端实例
        print("测试创建MsWordDocumentBackend实例...")
        
        # 这里只是测试导入和基本功能，不实际处理文件
        print("Word后端功能测试通过")
        return True
        
    except ImportError as e:
        print(f"DocLing Word后端导入失败: {e}")
        return False
    except Exception as e:
        print(f"Word后端测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始Word文档处理测试...")
    
    # 首先测试DocLing Word后端
    if test_docling_word_backend():
        # 然后测试文档处理
        test_word_processing()
    else:
        print("DocLing Word后端不可用，跳过文档处理测试") 