import os
from typing import List
from pathlib import Path
import docx
import markdown
from bs4 import BeautifulSoup
from pptx import Presentation

# DocLing imports
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.document_converter import DocumentConverter, FormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode, EasyOcrOptions
from docling.datamodel.base_models import InputFormat
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.base_models import ConversionStatus
from docling.datamodel.document import ConversionResult, InputDocument

# 导入日志模块
from utils.logger import logger

class DocumentProcessor:
    """文档处理器，支持多种文件格式，使用DocLing处理PDF"""
    
    @staticmethod
    def _create_document_converter():
        """创建文档转换器，使用DocLingParseV2DocumentBackend"""
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        ocr_options = EasyOcrOptions(lang=['en'], force_full_page_ocr=False)
        pipeline_options.ocr_options = ocr_options
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        
        format_options = {
            InputFormat.PDF: FormatOption(
                pipeline_cls=StandardPdfPipeline,
                pipeline_options=pipeline_options,
                backend=DoclingParseV2DocumentBackend
            )
        }
        
        return DocumentConverter(format_options=format_options)

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[str]:
        """从PDF文件中提取文本，使用DocLingParseV2DocumentBackend"""
        texts = []
        try:
            logger.info(f"开始处理PDF文件: {os.path.basename(file_path)}")
            
            # 创建文档转换器
            doc_converter = DocumentProcessor._create_document_converter()
            
            # 转换文档
            input_path = Path(file_path)
            conv_results = doc_converter.convert_all(source=[input_path])
            
            for conv_result in conv_results:
                if conv_result.status == ConversionStatus.SUCCESS:
                    # 获取文档数据
                    data = conv_result.document.export_to_dict()
                    
                    # 处理文本内容
                    if 'texts' in data:
                        for text_item in data['texts']:
                            if 'text' in text_item and text_item['text'].strip():
                                texts.append(text_item['text'].strip())
                    
                    # 处理表格内容
                    if 'tables' in data:
                        for table_item in data['tables']:
                            if 'data' in table_item and 'grid' in table_item['data']:
                                for row in table_item['data']['grid']:
                                    row_texts = []
                                    for cell in row:
                                        if 'text' in cell and cell['text'].strip():
                                            row_texts.append(cell['text'].strip())
                                    if row_texts:
                                        texts.append(" | ".join(row_texts))
                    
                    logger.info(f"使用DocLing处理PDF文件，提取了 {len(texts)} 个文本块")
                    
                    # 显示提取的文本示例
                    if texts:
                        logger.info("提取的文本示例:")
                        for i, text in enumerate(texts[:3]):
                            logger.info(f"  {i+1}: {text[:100]}...")
                    
                else:
                    logger.error(f"PDF文档转换失败: {conv_result.status}")
                    
        except Exception as e:
            logger.error(f"使用DocLing处理PDF文件时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
        return texts

    @staticmethod
    def extract_text_from_pdf_with_layout(file_path: str) -> List[dict]:
        """从PDF文件中提取文本和布局信息，使用DocLingParseV2DocumentBackend"""
        results = []
        try:
            logger.info(f"开始处理PDF文件布局: {os.path.basename(file_path)}")
            
            # 创建文档转换器
            doc_converter = DocumentProcessor._create_document_converter()
            
            # 转换文档
            input_path = Path(file_path)
            conv_results = doc_converter.convert_all(source=[input_path])
            
            for conv_result in conv_results:
                if conv_result.status == ConversionStatus.SUCCESS:
                    # 获取文档数据
                    data = conv_result.document.export_to_dict()
                    
                    # 处理文本内容
                    if 'texts' in data:
                        for text_item in data['texts']:
                            if 'text' in text_item and text_item['text'].strip():
                                item_data = {
                                    'text': text_item['text'].strip(),
                                    'type': 'text'
                                }
                                
                                # 添加位置信息
                                if 'prov' in text_item and text_item['prov']:
                                    prov = text_item['prov'][0]
                                    item_data['page'] = prov.get('page_no')
                                    if 'bbox' in prov:
                                        item_data['bbox'] = {
                                            'left': prov['bbox'].get('l'),
                                            'top': prov['bbox'].get('t'),
                                            'right': prov['bbox'].get('r'),
                                            'bottom': prov['bbox'].get('b')
                                        }
                                
                                # 添加字体信息
                                if 'font_size' in text_item:
                                    item_data['font_size'] = text_item['font_size']
                                if 'font_name' in text_item:
                                    item_data['font_name'] = text_item['font_name']
                                
                                results.append(item_data)
                    
                    logger.info(f"使用DocLing处理PDF文件布局，提取了 {len(results)} 个文本块")
                    
                else:
                    logger.error(f"PDF文档转换失败: {conv_result.status}")
                    
        except Exception as e:
            logger.error(f"使用DocLing处理PDF文件布局时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
        return results

    @staticmethod
    def extract_text_from_pdf_in_region(file_path: str, bbox: dict, page_index: int = 0) -> str:
        """从PDF文件的指定区域提取文本"""
        try:
            logger.info(f"从PDF区域提取文本: {os.path.basename(file_path)}")
            
            # 创建文档转换器
            doc_converter = DocumentProcessor._create_document_converter()
            
            # 转换文档
            input_path = Path(file_path)
            conv_results = doc_converter.convert_all(source=[input_path])
            
            for conv_result in conv_results:
                if conv_result.status == ConversionStatus.SUCCESS:
                    # 获取文档数据
                    data = conv_result.document.export_to_dict()
                    
                    # 查找指定页面和区域的文本
                    if 'texts' in data:
                        for text_item in data['texts']:
                            if 'prov' in text_item and text_item['prov']:
                                prov = text_item['prov'][0]
                                if prov.get('page_no') == page_index:
                                    # 检查文本是否在指定区域内
                                    if 'bbox' in prov:
                                        text_bbox = prov['bbox']
                                        # 简单的区域重叠检查
                                        if (text_bbox['l'] >= bbox['left'] and 
                                            text_bbox['t'] >= bbox['top'] and
                                            text_bbox['r'] <= bbox['right'] and
                                            text_bbox['b'] <= bbox['bottom']):
                                            if 'text' in text_item and text_item['text'].strip():
                                                return text_item['text'].strip()
                    
                else:
                    logger.error(f"PDF文档转换失败: {conv_result.status}")
                    
        except Exception as e:
            logger.error(f"从PDF区域提取文本时出错: {str(e)}")
            
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
                logger.warning("DocLing没有提取到任何文本")
                raise Exception("DocLing提取结果为空")
            
            # 显示提取的文本示例
            if texts:
                logger.info("提取的文本示例:")
                for i, text in enumerate(texts[:3]):
                    logger.info(f"  {i+1}: {text[:100]}...")
            
        except Exception as e:
            logger.error(f"使用DocLing处理Word文档时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            texts = []
        
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
            logger.error(f"使用DocLing处理Word文档结构时出错: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
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
            logger.error(f"处理Markdown文件时出错: {str(e)}")
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
            logger.error(f"处理PowerPoint文件时出错: {str(e)}")
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
            logger.error(f"处理文本文件时出错: {str(e)}")
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