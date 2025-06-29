"""
ドキュメント処理サービス
PDFやテキストファイルからテキストを抽出し、チャンク化する
"""
import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

import PyPDF2
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """ドキュメント処理クラス"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDFからテキストを抽出"""
        try:
            text = ""
            
            # pdfplumberを使用（表やレイアウトを考慮）
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text
                    except Exception as e:
                        logger.warning(f"Page {page_num + 1} processing failed: {e}")
                        
            # フォールバック: PyPDF2を使用
            if not text.strip():
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text
                        except Exception as e:
                            logger.warning(f"Page {page_num + 1} processing failed: {e}")
            
            return self._clean_text(text)
            
        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """ファイルからテキストを抽出"""
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return self.extract_text_from_pdf(file_path)
            elif file_extension in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return self._clean_text(file.read())
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return ""
        except Exception as e:
            logger.error(f"File processing failed for {file_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        if not text:
            return ""
        
        # 改行の正規化
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # 余分な空白の削除
        text = re.sub(r' +', ' ', text)
        
        # 余分な改行の削除（3つ以上の連続改行を2つに）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 文字化けの可能性がある文字の除去
        text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3400-\u4DBF\u002D\u002E\u0028\u0029\u003A\u003B\u002C\u0021\u003F\u300C\u300D\u3001\u3002\u30FB\u002F\u005C\u0040\u0023\u0024\u0025\u005E\u0026\u002A\u002B\u003D\u007B\u007D\u005B\u005D\u007C\u003C\u003E\u007E\u0060\u0027\u0022]', ' ', text)
        
        return text.strip()
    
    def create_documents(self, file_paths: List[str], microcontroller: str = "NUCLEO-F767ZI") -> List[Document]:
        """ファイルリストからDocumentオブジェクトを作成"""
        documents = []
        
        for file_path in file_paths:
            try:
                text = self.extract_text_from_file(file_path)
                if not text:
                    continue
                
                # ファイル情報をメタデータに追加
                metadata = {
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "microcontroller": microcontroller,
                    "file_type": Path(file_path).suffix.lower(),
                    "char_count": len(text)
                }
                
                # ファイルタイプ別の追加メタデータ
                if "nucleo" in file_path.lower():
                    metadata["category"] = "hardware"
                elif "cubemx" in file_path.lower():
                    metadata["category"] = "software_tool"
                elif any(app_note in file_path.lower() for app_note in ["an", "application_note"]):
                    metadata["category"] = "application_note"
                elif "user_manual" in file_path.lower() or "um" in file_path.lower():
                    metadata["category"] = "user_manual"
                elif "technical_note" in file_path.lower() or "tn" in file_path.lower():
                    metadata["category"] = "technical_note"
                else:
                    metadata["category"] = "general"
                
                # テキストをチャンクに分割
                chunks = self.text_splitter.split_text(text)
                
                # 各チャンクをDocumentオブジェクトに変換
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # 空でないチャンクのみ追加
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "chunk_index": i,
                            "chunk_id": f"{os.path.basename(file_path)}_{i}"
                        })
                        
                        documents.append(Document(
                            page_content=chunk,
                            metadata=chunk_metadata
                        ))
                
                logger.info(f"Processed {file_path}: {len(chunks)} chunks created")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info(f"Total documents created: {len(documents)}")
        return documents
    
    def process_directory(self, directory_path: str, microcontroller: str = "NUCLEO-F767ZI") -> List[Document]:
        """ディレクトリ内のサポートされているファイルをすべて処理"""
        file_paths = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in Config.SUPPORTED_FORMATS):
                    file_paths.append(os.path.join(root, file))
        
        logger.info(f"Found {len(file_paths)} supported files in {directory_path}")
        return self.create_documents(file_paths, microcontroller)
    
    def get_document_summary(self, documents: List[Document]) -> Dict:
        """ドキュメントの要約統計を取得"""
        if not documents:
            return {}
        
        categories = {}
        total_chunks = len(documents)
        total_chars = sum(len(doc.page_content) for doc in documents)
        
        for doc in documents:
            category = doc.metadata.get("category", "unknown")
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "average_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
            "categories": categories,
            "microcontroller": documents[0].metadata.get("microcontroller", "unknown")
        }