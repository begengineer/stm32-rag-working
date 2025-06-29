"""
RAGエンジン - 検索拡張生成の核となるクラス
"""
import logging
from typing import List, Dict, Optional, Tuple
import openai
from langchain_community.llms import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.vector_db import VectorDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """RAG（Retrieval Augmented Generation）エンジン"""
    
    def __init__(self, vector_db: VectorDatabase = None):
        self.vector_db = vector_db or VectorDatabase()
        self.llm = None
        self._initialize_llm()
        self._setup_prompts()
    
    def _initialize_llm(self):
        """LLMの初期化"""
        try:
            if not Config.OPENAI_API_KEY:
                logger.warning("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                return
            
            self.llm = ChatOpenAI(
                model_name=Config.LLM_MODEL,
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                openai_api_key=Config.OPENAI_API_KEY
            )
            
            logger.info(f"LLM initialized: {Config.LLM_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _setup_prompts(self):
        """プロンプトテンプレートの設定"""
        self.qa_prompt = PromptTemplate(
            template=Config.QA_PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        self.code_prompt = PromptTemplate(
            template=Config.CODE_GENERATION_PROMPT,
            input_variables=["request", "microcontroller", "context"]
        )
    
    def answer_question(self, 
                       question: str, 
                       microcontroller: str = "NUCLEO-F767ZI",
                       num_docs: int = 5) -> Dict:
        """質問に対してRAGベースで回答を生成"""
        try:
            # 1. 関連ドキュメントを検索
            relevant_docs = self.vector_db.search_similar_documents(
                query=question,
                k=num_docs,
                microcontroller=microcontroller
            )
            
            if not relevant_docs:
                return {
                    "answer": "申し訳ございませんが、関連する情報が見つかりませんでした。質問を言い換えてお試しください。",
                    "sources": [],
                    "confidence": 0.0,
                    "microcontroller": microcontroller
                }
            
            # 2. コンテキストの構築
            context = self._build_context(relevant_docs)
            
            # 3. LLMで回答生成
            if not self.llm:
                return {
                    "answer": "LLMが初期化されていません。OpenAI API keyを確認してください。",
                    "sources": [],
                    "confidence": 0.0,
                    "microcontroller": microcontroller
                }
            
            prompt = self.qa_prompt.format(context=context, question=question)
            response = self.llm.predict(prompt)
            
            # 4. 信頼度計算
            confidence = self._calculate_confidence(relevant_docs)
            
            # 5. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            return {
                "answer": response.strip(),
                "sources": sources,
                "confidence": confidence,
                "microcontroller": microcontroller,
                "context_length": len(context),
                "num_sources": len(relevant_docs)
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "answer": f"エラーが発生しました: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "microcontroller": microcontroller
            }
    
    def generate_code(self, 
                     request: str, 
                     microcontroller: str = "NUCLEO-F767ZI",
                     num_docs: int = 3) -> Dict:
        """サンプルコード生成"""
        try:
            # 1. コード生成に関連するドキュメントを検索
            search_query = f"{request} サンプルコード プログラム 実装"
            relevant_docs = self.vector_db.search_similar_documents(
                query=search_query,
                k=num_docs,
                microcontroller=microcontroller
            )
            
            # 2. コンテキストの構築
            context = self._build_context(relevant_docs)
            
            # 3. LLMでコード生成
            if not self.llm:
                return {
                    "code": "// LLMが初期化されていません。OpenAI API keyを確認してください。",
                    "explanation": "エラー: LLMが利用できません",
                    "sources": [],
                    "microcontroller": microcontroller
                }
            
            prompt = self.code_prompt.format(
                request=request,
                microcontroller=microcontroller,
                context=context
            )
            response = self.llm.predict(prompt)
            
            # 4. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            return {
                "code": response.strip(),
                "explanation": f"{microcontroller}用の{request}に関するサンプルコードです。",
                "sources": sources,
                "microcontroller": microcontroller,
                "context_length": len(context)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate code: {e}")
            return {
                "code": f"// エラーが発生しました: {str(e)}",
                "explanation": "コード生成に失敗しました",
                "sources": [],
                "microcontroller": microcontroller
            }
    
    def get_microcontroller_info(self, microcontroller: str) -> Dict:
        """マイコンの基本情報を取得"""
        try:
            # 設定からマイコン情報を取得
            mc_info = Config.SUPPORTED_MICROCONTROLLERS.get(microcontroller, {})
            
            if not mc_info:
                return {
                    "info": f"{microcontroller}の情報が見つかりません。",
                    "details": {},
                    "sources": []
                }
            
            # ドキュメントからの詳細情報を検索
            search_query = f"{microcontroller} 仕様 特性 概要"
            relevant_docs = self.vector_db.search_similar_documents(
                query=search_query,
                k=3,
                microcontroller=microcontroller
            )
            
            # ソース情報
            sources = self._extract_sources(relevant_docs)
            
            return {
                "info": mc_info.get("description", ""),
                "details": mc_info,
                "sources": sources,
                "microcontroller": microcontroller
            }
            
        except Exception as e:
            logger.error(f"Failed to get microcontroller info: {e}")
            return {
                "info": f"エラーが発生しました: {str(e)}",
                "details": {},
                "sources": []
            }
    
    def search_documentation(self, 
                           query: str, 
                           microcontroller: str = None,
                           category: str = None,
                           num_results: int = 10) -> List[Dict]:
        """ドキュメント検索"""
        try:
            relevant_docs = self.vector_db.search_similar_documents(
                query=query,
                k=num_results,
                microcontroller=microcontroller,
                category=category
            )
            
            results = []
            for doc, score in relevant_docs:
                results.append({
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": 1.0 - score,  # スコアを類似度に変換
                    "source": doc.metadata.get("filename", "不明"),
                    "category": doc.metadata.get("category", "一般")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Documentation search failed: {e}")
            return []
    
    def _build_context(self, relevant_docs: List[Tuple[Document, float]]) -> str:
        """関連ドキュメントからコンテキストを構築"""
        context_parts = []
        
        for i, (doc, score) in enumerate(relevant_docs, 1):
            source = doc.metadata.get("filename", "不明")
            category = doc.metadata.get("category", "一般")
            
            context_part = f"""
[ソース {i}: {source} ({category})]
{doc.page_content}
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, relevant_docs: List[Tuple[Document, float]]) -> float:
        """回答の信頼度を計算"""
        if not relevant_docs:
            return 0.0
        
        # スコアベースの信頼度計算
        scores = [1.0 - score for doc, score in relevant_docs]
        avg_score = sum(scores) / len(scores)
        
        # ドキュメント数による補正
        doc_count_factor = min(len(relevant_docs) / 5.0, 1.0)
        
        confidence = avg_score * doc_count_factor
        return min(confidence, 1.0)
    
    def _extract_sources(self, relevant_docs: List[Tuple[Document, float]]) -> List[Dict]:
        """ソース情報を抽出"""
        sources = []
        seen_sources = set()
        
        for doc, score in relevant_docs:
            source_info = {
                "filename": doc.metadata.get("filename", "不明"),
                "category": doc.metadata.get("category", "一般"),
                "relevance": 1.0 - score,
                "chunk_id": doc.metadata.get("chunk_id", "")
            }
            
            # 重複を避ける
            source_key = (source_info["filename"], source_info["chunk_id"])
            if source_key not in seen_sources:
                sources.append(source_info)
                seen_sources.add(source_key)
        
        return sources
    
    def get_system_status(self) -> Dict:
        """システムの状態を取得"""
        return {
            "llm_available": self.llm is not None,
            "vector_db_available": self.vector_db is not None,
            "supported_microcontrollers": list(Config.SUPPORTED_MICROCONTROLLERS.keys()),
            "vector_db_collections": self.vector_db.list_collections() if self.vector_db else [],
            "embedding_model": Config.EMBEDDING_MODEL,
            "llm_model": Config.LLM_MODEL
        }