"""
RAGエンジン - OpenAI不要版（デモ用）
"""
import logging
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document
from langchain.prompts import PromptTemplate

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.vector_db_offline import OfflineVectorDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfflineRAGEngine:
    """RAG（Retrieval Augmented Generation）エンジン（オフライン版）"""
    
    def __init__(self, vector_db: OfflineVectorDatabase = None):
        self.vector_db = vector_db or OfflineVectorDatabase()
        self.llm = None  # OpenAI不使用
        self._setup_prompts()
    
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
        """質問に対してRAGベースで回答を生成（デモ版）"""
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
            
            # 3. 簡易回答生成（OpenAI不使用）
            answer = self._generate_simple_answer(question, context, microcontroller)
            
            # 4. 信頼度計算
            confidence = self._calculate_confidence(relevant_docs)
            
            # 5. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            return {
                "answer": answer,
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
    
    def _generate_simple_answer(self, question: str, context: str, microcontroller: str) -> str:
        """簡易回答生成（OpenAI不使用）"""
        # 基本的なキーワードマッチングによる回答生成
        question_lower = question.lower()
        context_lower = context.lower()
        
        # GPIO関連
        if any(keyword in question_lower for keyword in ['gpio', 'ピン', 'pin', 'led', 'ボタン', 'button']):
            if 'gpio' in context_lower or 'pin' in context_lower:
                return f"""
{microcontroller}のGPIOについて関連情報を見つけました。

GPIOピンの基本的な使用方法:
- 出力設定: HAL_GPIO_WritePin()関数を使用
- 入力読み取り: HAL_GPIO_ReadPin()関数を使用
- 初期化: HAL_GPIO_Init()関数で設定

詳細な設定方法については、見つかったドキュメントをご参照ください。
                """
        
        # タイマー関連
        elif any(keyword in question_lower for keyword in ['timer', 'タイマー', 'pwm']):
            if 'timer' in context_lower or 'tim' in context_lower:
                return f"""
{microcontroller}のタイマー機能について情報を見つけました。

タイマーの主な用途:
- PWM信号生成
- 時間計測
- 定期的な割り込み処理

HAL関数を使用してタイマーを制御できます。
                """
        
        # UART/通信関連
        elif any(keyword in question_lower for keyword in ['uart', 'serial', 'usart', '通信']):
            if 'uart' in context_lower or 'usart' in context_lower:
                return f"""
{microcontroller}のUART通信について情報を見つけました。

UART通信の基本:
- HAL_UART_Transmit()で送信
- HAL_UART_Receive()で受信
- ボーレート設定が重要

詳細な設定例については、関連ドキュメントをご確認ください。
                """
        
        # 一般的な回答
        else:
            return f"""
{microcontroller}に関する情報を見つけました。

関連するドキュメントから抜粋した情報:
{context[:500]}...

詳細については、下記のソースドキュメントをご参照ください。
            """
    
    def generate_code(self, 
                     request: str, 
                     microcontroller: str = "NUCLEO-F767ZI",
                     num_docs: int = 3) -> Dict:
        """サンプルコード生成（デモ版）"""
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
            
            # 3. 簡易コード生成
            code = self._generate_simple_code(request, microcontroller)
            
            # 4. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            return {
                "code": code,
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
    
    def _generate_simple_code(self, request: str, microcontroller: str) -> str:
        """簡易コード生成"""
        request_lower = request.lower()
        
        # LED制御
        if any(keyword in request_lower for keyword in ['led', 'ライト', '点灯', '点滅']):
            return f"""// {microcontroller} LED制御サンプル
#include "main.h"

void LED_Control_Example(void)
{{
    // LED点灯
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);
    HAL_Delay(1000);
    
    // LED消灯
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
    HAL_Delay(1000);
}}

// メインループでの使用例
int main(void)
{{
    HAL_Init();
    SystemClock_Config();
    
    // GPIO初期化（実際の設定はCubeMXで生成）
    MX_GPIO_Init();
    
    while (1)
    {{
        LED_Control_Example();
    }}
}}"""
        
        # ボタン入力
        elif any(keyword in request_lower for keyword in ['button', 'ボタン', '入力', 'switch']):
            return f"""// {microcontroller} ボタン入力サンプル
#include "main.h"

void Button_Read_Example(void)
{{
    GPIO_PinState button_state;
    
    // ボタン状態読み取り
    button_state = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
    
    if (button_state == GPIO_PIN_RESET)
    {{
        // ボタンが押された時の処理
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);  // LED点灯
    }}
    else
    {{
        // ボタンが離された時の処理
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET); // LED消灯
    }}
}}"""
        
        # PWM
        elif any(keyword in request_lower for keyword in ['pwm', 'サーボ', 'servo']):
            return f"""// {microcontroller} PWM制御サンプル
#include "main.h"

TIM_HandleTypeDef htim3;

void PWM_Control_Example(void)
{{
    uint32_t pulse_width = 1000; // 初期パルス幅
    
    // PWM開始
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
    
    // パルス幅を変更
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, pulse_width);
    
    HAL_Delay(1000);
}}"""
        
        # UART
        elif any(keyword in request_lower for keyword in ['uart', 'serial', 'usart', '通信']):
            return f"""// {microcontroller} UART通信サンプル
#include "main.h"
#include <string.h>

UART_HandleTypeDef huart3;

void UART_Communication_Example(void)
{{
    uint8_t tx_buffer[] = "Hello from {microcontroller}\\r\\n";
    uint8_t rx_buffer[100];
    
    // データ送信
    HAL_UART_Transmit(&huart3, tx_buffer, strlen((char*)tx_buffer), HAL_MAX_DELAY);
    
    // データ受信（タイムアウト付き）
    HAL_UART_Receive(&huart3, rx_buffer, sizeof(rx_buffer), 5000);
}}"""
        
        # 一般的なコード
        else:
            return f"""// {microcontroller} 基本サンプル
#include "main.h"

void Basic_Example(void)
{{
    // {request}に関する基本的な実装例
    // 詳細な実装については、STM32 HALドライバーライブラリ
    // およびCubeMXを使用してプロジェクトを生成してください
    
    // 初期化
    HAL_Init();
    SystemClock_Config();
    
    // メインループ
    while (1)
    {{
        // ここに{request}の処理を実装
        HAL_Delay(100);
    }}
}}"""
    
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
        
        return "\\n".join(context_parts)
    
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
            "llm_available": False,  # オフライン版のためFalse
            "vector_db_available": self.vector_db is not None,
            "supported_microcontrollers": list(Config.SUPPORTED_MICROCONTROLLERS.keys()),
            "vector_db_collections": self.vector_db.list_collections() if self.vector_db else [],
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": "Offline (Demo Mode)"
        }