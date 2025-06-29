"""
シンプルなベクトルデータベース（TF-IDF + Cosine Similarity）
依存関係を最小限に抑えたオフライン版
"""
import os
import json
import logging
import pickle
from typing import List, Dict, Optional, Tuple
from collections import Counter
import math
import re

from langchain.schema import Document

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVectorDatabase:
    """シンプルなベクトルデータベース（TF-IDF）"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or Config.get_vector_db_path()
        self.documents = []  # List[Document]
        self.tfidf_vectors = []  # List[Dict[str, float]]
        self.vocabulary = set()
        self.idf_scores = {}
        
        # ディレクトリ作成
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 既存データを読み込み
        self._load_data()
        
        logger.info(f"Simple vector database initialized at: {self.persist_directory}")
    
    def _tokenize(self, text: str) -> List[str]:
        """テキストをトークン化"""
        # 簡単な前処理
        text = text.lower()
        # 英数字と日本語文字のみを保持
        text = re.sub(r'[^a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\s]', ' ', text)
        # 単語分割（英語）と文字分割（日本語）
        tokens = []
        for word in text.split():
            if re.match(r'^[a-zA-Z0-9]+$', word):
                # 英数字の場合はそのまま
                if len(word) > 2:  # 短すぎる単語は除外
                    tokens.append(word)
            else:
                # 日本語の場合は2-gramで分割
                for i in range(len(word) - 1):
                    bigram = word[i:i+2]
                    if len(bigram) == 2:
                        tokens.append(bigram)
        
        return tokens
    
    def _calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Term Frequency計算"""
        token_count = Counter(tokens)
        total_tokens = len(tokens)
        
        tf_scores = {}
        for token, count in token_count.items():
            tf_scores[token] = count / total_tokens
        
        return tf_scores
    
    def _calculate_idf(self):
        """Inverse Document Frequency計算"""
        doc_count = len(self.documents)
        if doc_count == 0:
            return
        
        # 各トークンが出現するドキュメント数をカウント
        token_doc_count = Counter()
        
        for doc in self.documents:
            tokens = set(self._tokenize(doc.page_content))
            for token in tokens:
                token_doc_count[token] += 1
        
        # IDF計算
        self.idf_scores = {}
        for token, count in token_doc_count.items():
            self.idf_scores[token] = math.log(doc_count / count)
    
    def _calculate_tfidf_vector(self, tokens: List[str]) -> Dict[str, float]:
        """TF-IDFベクトル計算"""
        tf_scores = self._calculate_tf(tokens)
        tfidf_vector = {}
        
        for token, tf in tf_scores.items():
            idf = self.idf_scores.get(token, 0)
            tfidf_vector[token] = tf * idf
        
        return tfidf_vector
    
    def _cosine_similarity(self, vector1: Dict[str, float], vector2: Dict[str, float]) -> float:
        """コサイン類似度計算"""
        # 共通する語彙を取得
        common_tokens = set(vector1.keys()) & set(vector2.keys())
        
        if not common_tokens:
            return 0.0
        
        # 内積計算
        dot_product = sum(vector1[token] * vector2[token] for token in common_tokens)
        
        # ベクトルの大きさ計算
        magnitude1 = math.sqrt(sum(val ** 2 for val in vector1.values()))
        magnitude2 = math.sqrt(sum(val ** 2 for val in vector2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def add_documents(self, documents: List[Document], microcontroller: str = "NUCLEO-F767ZI") -> bool:
        """ドキュメントを追加"""
        try:
            if not documents:
                logger.warning("No documents to add")
                return False
            
            # メタデータにマイコン情報を追加
            for doc in documents:
                doc.metadata["microcontroller"] = microcontroller
            
            # ドキュメントを追加
            self.documents.extend(documents)
            
            # 語彙を更新
            for doc in documents:
                tokens = self._tokenize(doc.page_content)
                self.vocabulary.update(tokens)
            
            # IDF再計算
            self._calculate_idf()
            
            # 全ドキュメントのTF-IDFベクトルを再計算
            self.tfidf_vectors = []
            for doc in self.documents:
                tokens = self._tokenize(doc.page_content)
                tfidf_vector = self._calculate_tfidf_vector(tokens)
                self.tfidf_vectors.append(tfidf_vector)
            
            # データを保存
            self._save_data()
            
            logger.info(f"Added {len(documents)} documents for {microcontroller}")
            logger.info(f"Total documents: {len(self.documents)}")
            logger.info(f"Vocabulary size: {len(self.vocabulary)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def search_similar_documents(self, 
                               query: str, 
                               k: int = 5, 
                               microcontroller: str = None,
                               category: str = None,
                               score_threshold: float = 0.1) -> List[Tuple[Document, float]]:
        """類似ドキュメントを検索"""
        try:
            if not self.documents:
                logger.warning("No documents in database")
                return []
            
            # クエリのTF-IDFベクトル計算
            query_tokens = self._tokenize(query)
            query_vector = self._calculate_tfidf_vector(query_tokens)
            
            # 各ドキュメントとの類似度計算
            similarities = []
            for i, (doc, doc_vector) in enumerate(zip(self.documents, self.tfidf_vectors)):
                # フィルター適用
                if microcontroller and doc.metadata.get("microcontroller") != microcontroller:
                    continue
                if category and doc.metadata.get("category") != category:
                    continue
                
                similarity = self._cosine_similarity(query_vector, doc_vector)
                if similarity >= score_threshold:
                    similarities.append((doc, 1.0 - similarity))  # スコアを距離に変換
            
            # 類似度でソート（スコアが小さいほど類似度が高い）
            similarities.sort(key=lambda x: x[1])
            
            # 上位k件を返す
            results = similarities[:k]
            
            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_relevant_documents(self, 
                             query: str, 
                             k: int = 5,
                             microcontroller: str = None) -> List[Document]:
        """関連ドキュメントを取得"""
        results = self.search_similar_documents(query, k, microcontroller)
        return [doc for doc, score in results]
    
    def list_collections(self) -> List[str]:
        """利用可能なコレクションを一覧表示"""
        microcontrollers = set()
        for doc in self.documents:
            mc = doc.metadata.get("microcontroller")
            if mc:
                microcontrollers.add(f"microcontroller_{mc.lower().replace('-', '_')}")
        return list(microcontrollers)
    
    def get_collection_stats(self, microcontroller: str = None) -> Dict:
        """コレクションの統計情報を取得"""
        stats = {}
        
        if microcontroller:
            count = sum(1 for doc in self.documents 
                       if doc.metadata.get("microcontroller") == microcontroller)
            collection_name = f"microcontroller_{microcontroller.lower().replace('-', '_')}"
            stats[collection_name] = {
                "document_count": count,
                "microcontroller": microcontroller
            }
        else:
            # 全てのマイコンの統計
            microcontroller_counts = Counter()
            for doc in self.documents:
                mc = doc.metadata.get("microcontroller", "unknown")
                microcontroller_counts[mc] += 1
            
            for mc, count in microcontroller_counts.items():
                collection_name = f"microcontroller_{mc.lower().replace('-', '_')}"
                stats[collection_name] = {
                    "document_count": count,
                    "microcontroller": mc
                }
        
        return stats
    
    def _save_data(self):
        """データを保存"""
        try:
            data = {
                "documents": [(doc.page_content, doc.metadata) for doc in self.documents],
                "tfidf_vectors": self.tfidf_vectors,
                "vocabulary": list(self.vocabulary),
                "idf_scores": self.idf_scores
            }
            
            with open(os.path.join(self.persist_directory, "simple_vector_db.pkl"), "wb") as f:
                pickle.dump(data, f)
            
            logger.info("Data saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def _load_data(self):
        """データを読み込み"""
        try:
            data_file = os.path.join(self.persist_directory, "simple_vector_db.pkl")
            if os.path.exists(data_file):
                with open(data_file, "rb") as f:
                    data = pickle.load(f)
                
                # ドキュメント復元
                self.documents = [
                    Document(page_content=content, metadata=metadata)
                    for content, metadata in data.get("documents", [])
                ]
                
                self.tfidf_vectors = data.get("tfidf_vectors", [])
                self.vocabulary = set(data.get("vocabulary", []))
                self.idf_scores = data.get("idf_scores", {})
                
                logger.info(f"Loaded {len(self.documents)} documents from cache")
            
        except Exception as e:
            logger.warning(f"Failed to load existing data: {e}")
            # 新規データベースとして初期化
            self.documents = []
            self.tfidf_vectors = []
            self.vocabulary = set()
            self.idf_scores = {}