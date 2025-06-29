"""
ベクトルデータベース管理クラス
ChromaDBを使用してベクトル検索機能を提供
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDatabase:
    """ベクトルデータベース管理クラス"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or Config.VECTOR_DB_PATH
        self.embedding_model = None
        self.vector_store = None
        self.client = None
        self._initialize_embedding_model()
        self._initialize_vector_store()
    
    def _initialize_embedding_model(self):
        """埋め込みモデルの初期化"""
        try:
            # OpenAI Embeddingsを使用（軽量で高性能）
            self.embedding_model = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=Config.OPENAI_API_KEY
            )
            logger.info(f"OpenAI Embedding model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _initialize_vector_store(self):
        """ベクトルストアの初期化"""
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # ChromaDBクライアントの初期化
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Langchain Chromaの初期化
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model,
                client=self.client
            )
            
            logger.info(f"Vector store initialized at: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def add_documents(self, documents: List[Document], microcontroller: str = "NUCLEO-F767ZI") -> bool:
        """ドキュメントをベクトルデータベースに追加"""
        try:
            if not documents:
                logger.warning("No documents to add")
                return False
            
            # マイコン固有のコレクション名を生成
            collection_name = f"microcontroller_{microcontroller.lower().replace('-', '_')}"
            
            # ドキュメントにコレクション情報を追加
            for doc in documents:
                doc.metadata["collection"] = collection_name
                doc.metadata["microcontroller"] = microcontroller
            
            # ベクトルストアに追加
            self.vector_store.add_documents(documents)
            
            # 永続化
            self.vector_store.persist()
            
            logger.info(f"Added {len(documents)} documents for {microcontroller}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search_similar_documents(self, 
                               query: str, 
                               k: int = 5, 
                               microcontroller: str = None,
                               category: str = None,
                               score_threshold: float = 0.7) -> List[Tuple[Document, float]]:
        """類似ドキュメントを検索"""
        try:
            # フィルター条件の構築
            filter_dict = {}
            if microcontroller:
                filter_dict["microcontroller"] = microcontroller
            if category:
                filter_dict["category"] = category
            
            # 類似度検索
            if filter_dict:
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k,
                    filter=filter_dict
                )
            else:
                results = self.vector_store.similarity_search_with_score(
                    query=query,
                    k=k
                )
            
            # スコアフィルタリング（スコアが低いほど類似度が高い）
            filtered_results = [
                (doc, score) for doc, score in results 
                if score <= (1.0 - score_threshold)
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant documents for query: {query[:50]}...")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_relevant_documents(self, 
                             query: str, 
                             k: int = 5,
                             microcontroller: str = None) -> List[Document]:
        """関連ドキュメントを取得（スコアなし）"""
        results = self.search_similar_documents(query, k, microcontroller)
        return [doc for doc, score in results]
    
    def delete_collection(self, microcontroller: str) -> bool:
        """指定されたマイコンのコレクションを削除"""
        try:
            collection_name = f"microcontroller_{microcontroller.lower().replace('-', '_')}"
            
            # ChromaDBから直接削除
            try:
                collection = self.client.get_collection(collection_name)
                self.client.delete_collection(collection_name)
                logger.info(f"Deleted collection: {collection_name}")
                return True
            except Exception:
                logger.info(f"Collection {collection_name} not found or already deleted")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """利用可能なコレクションを一覧表示"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_stats(self, microcontroller: str = None) -> Dict:
        """コレクションの統計情報を取得"""
        try:
            stats = {}
            
            if microcontroller:
                collection_name = f"microcontroller_{microcontroller.lower().replace('-', '_')}"
                collections = [collection_name]
            else:
                collections = self.list_collections()
            
            for collection_name in collections:
                try:
                    collection = self.client.get_collection(collection_name)
                    count = collection.count()
                    stats[collection_name] = {
                        "document_count": count,
                        "microcontroller": collection_name.replace("microcontroller_", "").replace("_", "-").upper()
                    }
                except Exception as e:
                    logger.warning(f"Could not get stats for {collection_name}: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def search_by_metadata(self, 
                          microcontroller: str = None,
                          category: str = None,
                          filename: str = None,
                          limit: int = 10) -> List[Document]:
        """メタデータによる検索"""
        try:
            filter_dict = {}
            if microcontroller:
                filter_dict["microcontroller"] = microcontroller
            if category:
                filter_dict["category"] = category
            if filename:
                filter_dict["filename"] = filename
            
            # 空のクエリで検索（フィルターのみ）
            results = self.vector_store.similarity_search(
                query="",
                k=limit,
                filter=filter_dict
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return []
    
    def update_document(self, document_id: str, new_content: str, new_metadata: Dict) -> bool:
        """ドキュメントを更新"""
        try:
            # ChromaDBでは直接更新ができないため、削除してから追加
            # 実際の実装では、より効率的な更新方法を検討する必要がある
            logger.warning("Document update not fully implemented - consider delete and re-add")
            return False
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """データベースのバックアップ"""
        try:
            import shutil
            shutil.copytree(self.persist_directory, backup_path, dirs_exist_ok=True)
            logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """データベースの復元"""
        try:
            import shutil
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
            shutil.copytree(backup_path, self.persist_directory)
            
            # ベクトルストアを再初期化
            self._initialize_vector_store()
            
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False