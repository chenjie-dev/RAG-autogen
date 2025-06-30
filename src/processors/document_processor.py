import os
from typing import List
from pathlib import Path
import docx
import markdown
from bs4 import BeautifulSoup
from pptx import Presentation

# DocLing imports
from docling_core.types.doc import BoundingBox
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument

# 导入日志模块
from utils.logger import logger

class DocumentProcessor:
    """文档处理器，支持多种文件格式，使用DocLing处理PDF"""
    
    @staticmethod
    def _get_docling_backend(pdf_path: str) -> PyPdfiumDocumentBackend:
        """获取DocLing PDF后端"""
        # 将字符串路径转换为Path对象
        pdf_path_obj = Path(pdf_path)
        in_doc = InputDocument(
            path_or_stream=pdf_path_obj,
            format=InputFormat.PDF,
            backend=PyPdfiumDocumentBackend,
        )
        return in_doc._backend

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[str]:
        """从PDF文件中提取文本，使用DocLing"""
        texts = []
        try:
            doc_backend = DocumentProcessor._get_docling_backend(file_path)
            
            for page_index in range(doc_backend.page_count()):
                page_backend = doc_backend.load_page(page_index)
                
                # 获取页面中的所有文本单元格
                text_cells = list(page_backend.get_text_cells())
                
                # 按位置排序文本单元格（从上到下，从左到右）
                # 添加安全检查，确保cell有bbox属性
                sorted_cells = []
                for cell in text_cells:
                    if hasattr(cell, 'bbox') and cell.bbox is not None:
                        sorted_cells.append(cell)
                    else:
                        # 如果没有bbox，直接添加到列表末尾
                        sorted_cells.append(cell)
                
                # 尝试按位置排序，如果失败则保持原顺序
                try:
                    sorted_cells = sorted(sorted_cells, key=lambda cell: (cell.bbox.t, cell.bbox.l) if hasattr(cell, 'bbox') and cell.bbox else (0, 0))
                except Exception as sort_error:
                    logger.info(f"排序文本单元格时出错，保持原顺序: {sort_error}")
                
                # 提取文本内容
                page_texts = []
                for cell in sorted_cells:
                    if cell.text.strip():
                        page_texts.append(cell.text.strip())
                
                # 将页面文本合并为一个段落
                if page_texts:
                    page_content = " ".join(page_texts)
                    # 按自然段落分割
                    paragraphs = [p.strip() for p in page_content.split('\n\n') if p.strip()]
                    if not paragraphs:
                        # 如果没有自然段落，将整个页面作为一个段落
                        paragraphs = [page_content]
                    texts.extend(paragraphs)
                    
        except Exception as e:
            logger.info(f"使用DocLing处理PDF文件时出错: {str(e)}")
            # 如果DocLing失败，尝试使用备用方法
            try:
                texts = DocumentProcessor._extract_text_from_pdf_fallback(file_path)
            except Exception as fallback_error:
                logger.info(f"备用PDF处理方法也失败: {str(fallback_error)}")
        return texts

    @staticmethod
    def _extract_text_from_pdf_fallback(file_path: str) -> List[str]:
        """PDF处理的备用方法"""
        # 这里可以添加其他PDF处理库作为备用
        # 例如使用PyPDF2或pdfplumber
        texts = []
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        texts.extend(paragraphs)
        except ImportError:
            logger.info("pdfplumber未安装，无法使用备用PDF处理方法")
        except Exception as e:
            logger.info(f"备用PDF处理方法出错: {str(e)}")
        return texts

    @staticmethod
    def extract_text_from_pdf_with_layout(file_path: str) -> List[dict]:
        """从PDF文件中提取文本和布局信息，使用DocLing"""
        results = []
        try:
            doc_backend = DocumentProcessor._get_docling_backend(file_path)
            
            for page_index in range(doc_backend.page_count()):
                page_backend = doc_backend.load_page(page_index)
                
                # 获取页面中的所有文本单元格
                text_cells = list(page_backend.get_text_cells())
                
                page_data = {
                    'page_index': page_index,
                    'cells': []
                }
                
                for cell in text_cells:
                    if cell.text.strip():
                        cell_data = {
                            'text': cell.text.strip(),
                            'bbox': {
                                'left': cell.bbox.l,
                                'top': cell.bbox.t,
                                'right': cell.bbox.r,
                                'bottom': cell.bbox.b
                            },
                            'font_size': getattr(cell, 'font_size', None),
                            'font_name': getattr(cell, 'font_name', None)
                        }
                        page_data['cells'].append(cell_data)
                
                results.append(page_data)
                    
        except Exception as e:
            logger.info(f"使用DocLing提取PDF布局信息时出错: {str(e)}")
        return results

    @staticmethod
    def extract_text_from_pdf_in_region(file_path: str, bbox: BoundingBox, page_index: int = 0) -> str:
        """从PDF文件的指定区域提取文本"""
        try:
            doc_backend = DocumentProcessor._get_docling_backend(file_path)
            page_backend = doc_backend.load_page(page_index)
            
            text = page_backend.get_text_in_rect(bbox=bbox)
            return text.strip()
        except Exception as e:
            logger.info(f"从PDF区域提取文本时出错: {str(e)}")
            return ""

    @staticmethod
    def extract_text_from_docx(file_path: str) -> List[str]:
        """从Word文档中提取文本，使用DocLing"""
        texts = []
        try:
            logger.info(f"开始处理Word文档: {os.path.basename(file_path)}")
            
            # 使用DocLing的MsWordDocumentBackend
            from docling.backend.msword_backend import MsWordDocumentBackend
            from docling.datamodel.document import DoclingDocument, TextItem, SectionHeaderItem
            
            # 创建输入文档
            in_doc = InputDocument(
                path_or_stream=Path(file_path),
                format=InputFormat.DOCX,
                backend=MsWordDocumentBackend,
            )
            
            # 创建后端并转换文档
            backend = MsWordDocumentBackend(
                in_doc=in_doc,
                path_or_stream=Path(file_path),
            )
            doc: DoclingDocument = backend.convert()
            
            logger.info(f"DocLing文档转换成功，开始提取文本...")
            
            # 遍历文档中的所有项目
            item_count = 0
            for item, _ in doc.iterate_items():
                item_count += 1
                
                if isinstance(item, TextItem):
                    # 处理普通文本
                    if item.text.strip():
                        texts.append(item.text.strip())
                elif isinstance(item, SectionHeaderItem):
                    # 处理标题，添加标题级别信息
                    header_text = f"[标题{item.level}] {item.text.strip()}"
                    if header_text:
                        texts.append(header_text)
                else:
                    # 处理其他类型的项目
                    if hasattr(item, 'text') and item.text.strip():
                        texts.append(item.text.strip())
            
            logger.info(f"使用DocLing处理Word文档，遍历了 {item_count} 个项目，提取了 {len(texts)} 个文本块")
            
            # 验证提取结果
            if not texts:
                logger.info("警告: DocLing没有提取到任何文本，尝试备用方法")
                raise Exception("DocLing提取结果为空")
            
            # 显示提取的文本示例
            if texts:
                logger.info("提取的文本示例:")
                for i, text in enumerate(texts[:3]):
                    logger.info(f"  {i+1}: {text[:100]}...")
            
        except Exception as e:
            logger.info(f"使用DocLing处理Word文档时出错: {str(e)}")
            # 如果DocLing失败，使用备用方法
            try:
                logger.info("尝试使用备用方法处理Word文档...")
                texts = DocumentProcessor._extract_text_from_docx_fallback(file_path)
                logger.info(f"备用方法成功，提取了 {len(texts)} 个文本块")
            except Exception as fallback_error:
                logger.info(f"备用Word文档处理方法也失败: {str(fallback_error)}")
                texts = []
        
        return texts

    @staticmethod
    def _extract_text_from_docx_fallback(file_path: str) -> List[str]:
        """Word文档处理的备用方法"""
        texts = []
        try:
            logger.info(f"使用python-docx备用方法处理Word文档...")
            doc = docx.Document(file_path)
            
            # 提取段落文本
            paragraph_count = 0
            for para in doc.paragraphs:
                if para.text.strip():
                    texts.append(para.text.strip())
                    paragraph_count += 1
            
            logger.info(f"从段落中提取了 {paragraph_count} 个文本块")
            
            # 提取表格文本
            table_count = 0
            for table in doc.tables:
                table_texts = []
                for row in table.rows:
                    row_texts = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_texts.append(cell.text.strip())
                    if row_texts:
                        table_texts.append(" | ".join(row_texts))
                if table_texts:
                    texts.append("表格: " + " | ".join(table_texts))
                    table_count += 1
            
            logger.info(f"从表格中提取了 {table_count} 个文本块")
            logger.info(f"使用备用方法处理Word文档，总共提取了 {len(texts)} 个文本块")
            
            # 显示提取的文本示例
            if texts:
                logger.info("备用方法提取的文本示例:")
                for i, text in enumerate(texts[:3]):
                    logger.info(f"  {i+1}: {text[:100]}...")
            
        except Exception as e:
            logger.info(f"备用Word文档处理方法出错: {str(e)}")
            import traceback
            logger.info(f"错误详情: {traceback.format_exc()}")
        
        return texts

    @staticmethod
    def extract_text_from_docx_with_structure(file_path: str) -> List[dict]:
        """从Word文档中提取文本和结构信息，使用DocLing"""
        results = []
        try:
            # 使用DocLing的MsWordDocumentBackend
            from docling.backend.msword_backend import MsWordDocumentBackend
            from docling.datamodel.document import DoclingDocument, TextItem, SectionHeaderItem
            
            # 创建输入文档
            in_doc = InputDocument(
                path_or_stream=Path(file_path),
                format=InputFormat.DOCX,
                backend=MsWordDocumentBackend,
            )
            
            # 创建后端并转换文档
            backend = MsWordDocumentBackend(
                in_doc=in_doc,
                path_or_stream=Path(file_path),
            )
            doc: DoclingDocument = backend.convert()
            
            # 遍历文档中的所有项目
            for item, _ in doc.iterate_items():
                item_data = {
                    'text': '',
                    'type': 'unknown',
                    'level': None,
                    'metadata': {}
                }
                
                if isinstance(item, TextItem):
                    item_data['text'] = item.text.strip()
                    item_data['type'] = 'text'
                    if hasattr(item, 'font_size'):
                        item_data['metadata']['font_size'] = getattr(item, 'font_size', None)
                    if hasattr(item, 'font_name'):
                        item_data['metadata']['font_name'] = getattr(item, 'font_name', None)
                        
                elif isinstance(item, SectionHeaderItem):
                    item_data['text'] = item.text.strip()
                    item_data['type'] = 'header'
                    item_data['level'] = item.level
                    
                else:
                    # 处理其他类型的项目
                    if hasattr(item, 'text'):
                        item_data['text'] = item.text.strip()
                    item_data['type'] = type(item).__name__
                
                # 只添加有文本内容的项目
                if item_data['text']:
                    results.append(item_data)
            
            logger.info(f"使用DocLing处理Word文档，提取了 {len(results)} 个结构化文本块")
            
        except Exception as e:
            logger.info(f"使用DocLing处理Word文档结构时出错: {str(e)}")
            # 如果DocLing失败，返回简单的文本列表
            try:
                simple_texts = DocumentProcessor._extract_text_from_docx_fallback(file_path)
                results = [{'text': text, 'type': 'text', 'level': None, 'metadata': {}} for text in simple_texts]
            except Exception as fallback_error:
                logger.info(f"备用Word文档处理方法也失败: {str(fallback_error)}")
        return results

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
            logger.info(f"处理Markdown文件时出错: {str(e)}")
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
            logger.info(f"处理PowerPoint文件时出错: {str(e)}")
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
            logger.info(f"处理文本文件时出错: {str(e)}")
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