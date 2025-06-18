import os
from typing import List
import docx
import markdown
from bs4 import BeautifulSoup
from pptx import Presentation
import pdfplumber

class DocumentProcessor:
    """文档处理器，支持多种文件格式"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[str]:
        """从PDF文件中提取文本"""
        texts = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # 分段处理
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        texts.extend(paragraphs)
        except Exception as e:
            print(f"处理PDF文件时出错: {str(e)}")
        return texts

    @staticmethod
    def extract_text_from_docx(file_path: str) -> List[str]:
        """从Word文档中提取文本"""
        texts = []
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    texts.append(para.text.strip())
        except Exception as e:
            print(f"处理Word文档时出错: {str(e)}")
        return texts

    @staticmethod
    def extract_text_from_markdown(file_path: str) -> List[str]:
        """从Markdown文件中提取文本"""
        texts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
                # 转换为HTML
                html = markdown.markdown(md_content)
                # 使用BeautifulSoup提取文本
                soup = BeautifulSoup(html, 'html.parser')
                # 获取所有段落
                paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text:
                        texts.append(text)
        except Exception as e:
            print(f"处理Markdown文件时出错: {str(e)}")
        return texts

    @staticmethod
    def extract_text_from_pptx(file_path: str) -> List[str]:
        """从PowerPoint文件中提取文本"""
        texts = []
        try:
            prs = Presentation(file_path)
            for slide in prs.slides:
                slide_texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text = shape.text.strip()
                        if text:
                            slide_texts.append(text)
                if slide_texts:
                    texts.append(" | ".join(slide_texts))  # 将同一页的文本合并
        except Exception as e:
            print(f"处理PowerPoint文件时出错: {str(e)}")
        return texts

    @staticmethod
    def extract_text_from_txt(file_path: str) -> List[str]:
        """从文本文件中提取文本"""
        texts = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # 按段落分割
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                texts.extend(paragraphs)
        except Exception as e:
            print(f"处理文本文件时出错: {str(e)}")
        return texts

    @staticmethod
    def process_file(file_path: str) -> List[str]:
        """处理各种格式的文件并提取文本"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        processors = {
            '.pdf': DocumentProcessor.extract_text_from_pdf,
            '.docx': DocumentProcessor.extract_text_from_docx,
            '.md': DocumentProcessor.extract_text_from_markdown,
            '.pptx': DocumentProcessor.extract_text_from_pptx,
            '.txt': DocumentProcessor.extract_text_from_txt
        }
        
        if file_ext not in processors:
            raise ValueError(f"不支持的文件格式: {file_ext}")
            
        return processors[file_ext](file_path) 