"""
STマイクロマイコン RAGシステム設定ファイル
"""
import os
from typing import Dict, List
from dotenv import load_dotenv

# Streamlitが利用可能かチェック
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

load_dotenv()

class Config:
    """システム設定クラス"""
    
    # パス設定（環境に応じて動的に設定）
    @staticmethod
    def get_data_path():
        """データディレクトリパスを取得"""
        if STREAMLIT_AVAILABLE:
            # Streamlit Cloud環境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(current_dir, "..", "data")
        else:
            # ローカル環境
            return "../data"
    
    @staticmethod  
    def get_vector_db_path():
        """ベクターDBパスを取得"""
        data_path = Config.get_data_path()
        return os.path.join(data_path, "vector_store")
    
    # 設定値
    VECTOR_DB_PATH = property(lambda self: Config.get_vector_db_path())
    DOCUMENTS_PATH = property(lambda self: os.path.join(Config.get_data_path(), "documents"))
    
    # OpenAI API設定（Streamlit Secrets優先）
    @staticmethod
    def get_openai_api_key():
        """OpenAI APIキーを安全に取得"""
        if STREAMLIT_AVAILABLE:
            try:
                # Streamlit Secretsから取得
                api_key = st.secrets.get("api_keys", {}).get("openai_api_key", "")
                if api_key:
                    return api_key
            except Exception as e:
                print(f"Streamlit Secrets読み取りエラー: {e}")
        
        # フォールバック：環境変数
        env_key = os.getenv("OPENAI_API_KEY", "")
        if env_key:
            return env_key
            
        # 最後のフォールバック：直接ファイル読み取り
        try:
            secrets_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    content = f.read()
                    # 簡易TOML解析
                    for line in content.split('\n'):
                        if 'openai_api_key' in line and '=' in line:
                            key = line.split('=')[1].strip().strip('"')
                            if key.startswith('sk-'):
                                return key
        except Exception as e:
            print(f"Secrets file読み取りエラー: {e}")
        
        return ""
    
    OPENAI_API_KEY = ""  # 初期化時は空
    
    # ベクトルデータベース設定
    VECTOR_DB_TYPE = "chromadb"  # chromadb or faiss
    VECTOR_DB_PATH = "../data/vector_store"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # 埋め込みモデル設定（OpenAI Embeddings使用）
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    # LLM設定
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    # ドキュメント設定
    DOCUMENT_PATH = "../data/documents"
    SUPPORTED_FORMATS = [".pdf", ".txt", ".md"]
    
    # マイコン設定
    SUPPORTED_MICROCONTROLLERS = {
        "NUCLEO-F767ZI": {
            "name": "NUCLEO-F767ZI",
            "series": "STM32F7",
            "core": "Cortex-M7",
            "frequency": "216 MHz",
            "flash": "2 MB",
            "ram": "512 KB",
            "description": "高性能ARM Cortex-M7マイコン開発ボード"
        }
    }
    
    # UI設定
    APP_TITLE = "STマイクロマイコン RAGシステム"
    APP_DESCRIPTION = "マイコン初心者向けQ&A・サンプルコード生成システム"
    
    # システムプロンプト
    SYSTEM_PROMPT = """
あなたはSTマイクロエレクトロニクスのマイコン専門アシスタントです。
マイコン初心者にも分かりやすく、丁寧に日本語で回答してください。

以下の点を心がけて回答してください：
1. 技術用語は初心者にも分かるよう解説を含める
2. 具体的なサンプルコードを提供する場合は、コメントを充実させる
3. CubeMXの使用方法は段階的に説明する
4. 安全性やベストプラクティスも含める
5. 関連するドキュメントへの参照も提供する

回答は簡潔で実用的なものにしてください。
"""

    # プロンプトテンプレート
    QA_PROMPT_TEMPLATE = """
以下のコンテキスト情報を使用して、ユーザーの質問に答えてください。

コンテキスト:
{context}

質問: {question}

マイコン初心者にも分かりやすく、日本語で詳しく回答してください。
"""

    CODE_GENERATION_PROMPT = """
以下の要求に基づいて、STM32マイコン用のサンプルコードを生成してください。

要求: {request}
マイコン: {microcontroller}
コンテキスト: {context}

以下の形式で回答してください：
1. コードの概要説明
2. 必要なライブラリとヘッダファイル
3. 詳細なコメント付きサンプルコード
4. 使用方法とポイント
5. 注意事項

初心者にも分かりやすいよう、丁寧にコメントを記述してください。
"""