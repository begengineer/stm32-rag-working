"""
STマイクロマイコン RAGシステム メインアプリケーション
"""
import streamlit as st
import os
import sys
import logging
from typing import Dict, List, Optional

# パス設定 - 現在のディレクトリをルートに設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# プロジェクトのモジュールをインポート
from config import Config
from models.simple_rag_engine import SimpleRAGEngine
from models.simple_vector_db import SimpleVectorDatabase
from services.document_processor import DocumentProcessor
from services.microcontroller_selector import MicrocontrollerSelector
from services.code_generator import CodeGenerator
from services.auth import AuthService
from ui.components import *

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STMicroRAGApp:
    """STマイクロマイコン RAGアプリケーション"""
    
    def __init__(self):
        self.setup_page_config()
        self.auth_service = AuthService()
        
        # 認証チェック
        if not self.auth_service.require_auth():
            return
        
        self.initialize_session_state()
        self.initialize_components()
    
    def setup_page_config(self):
        """ページ設定"""
        st.set_page_config(
            page_title="STマイクロRAGシステム",
            page_icon="🔬",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """セッション状態の初期化"""
        if "initialized" not in st.session_state:
            st.session_state.initialized = False
            st.session_state.current_microcontroller = "NUCLEO-F767ZI"
            st.session_state.vector_db_ready = False
            st.session_state.documents_processed = False
            st.session_state.messages = []
    
    def initialize_components(self):
        """システムコンポーネントの初期化"""
        try:
            # コンポーネントの初期化
            self.microcontroller_selector = MicrocontrollerSelector()
            self.code_generator = CodeGenerator()
            self.document_processor = DocumentProcessor()
            
            # ベクトルデータベースの初期化（シンプル版）
            if not st.session_state.vector_db_ready:
                self.vector_db = SimpleVectorDatabase()
                self.rag_engine = SimpleRAGEngine(self.vector_db)
                
                # ドキュメントブートストラップ
                self.bootstrap_documents_if_needed()
                
                st.session_state.vector_db_ready = True
            else:
                self.vector_db = SimpleVectorDatabase()
                self.rag_engine = SimpleRAGEngine(self.vector_db)
            
            st.session_state.initialized = True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            st.error(f"システムの初期化に失敗しました: {e}")
            st.stop()
    
    def bootstrap_documents_if_needed(self):
        """必要に応じて基本文書をブートストラップ"""
        try:
            from bootstrap_docs import OnlineDocumentBootstrap
            bootstrap = OnlineDocumentBootstrap(self.vector_db)
            
            if bootstrap.is_bootstrap_needed():
                with st.spinner("📚 基本文書を初期化しています..."):
                    success = bootstrap.bootstrap_documents()
                    if success:
                        logger.info("Documents bootstrapped successfully")
                        st.success("基本文書の初期化が完了しました！")
                    else:
                        logger.warning("Bootstrap partially failed")
                        
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            # エラーがあっても続行
    
    def process_documents_if_needed(self):
        """必要に応じてドキュメントを処理"""
        if st.session_state.documents_processed:
            return
        
        # ドキュメント処理状況を確認
        collections = self.vector_db.list_collections()
        nucleo_collection = f"microcontroller_nucleo_f767zi"
        
        if nucleo_collection not in collections:
            with st.spinner("📚 ドキュメントを処理しています..."):
                self.process_documents()
        
        st.session_state.documents_processed = True
    
    def process_documents(self):
        """利用可能なドキュメントを処理してベクトル化"""
        try:
            # ドキュメントファイルのパスを設定
            base_path = "/mnt/c/Users/anpan/OneDrive/デスクトップ/WorkSpace/RAGSystem"
            document_files = []
            
            # PDFファイルを検索
            pdf_files = [
                "nucleo-f767zi.pdf",
                "tn1235-overview-of-stlink-derivatives-stmicroelectronics.pdf", 
                "um1974-stm32-nucleo144-boards-mb1137-stmicroelectronics.pdf",
                "um1727-getting-started-with-stm32-nucleo-board-software-development-tools-stmicroelectronics.pdf"
            ]
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(base_path, pdf_file)
                if os.path.exists(pdf_path):
                    document_files.append(pdf_path)
                else:
                    logger.warning(f"Document not found: {pdf_path}")
            
            # ANフォルダのPDFファイルも追加
            an_folder = os.path.join(base_path, "AN")
            if os.path.exists(an_folder):
                for file in os.listdir(an_folder):
                    if file.endswith(".pdf"):
                        document_files.append(os.path.join(an_folder, file))
            
            if document_files:
                # ドキュメントを処理
                documents = self.document_processor.create_documents(
                    document_files, 
                    "NUCLEO-F767ZI"
                )
                
                if documents:
                    # ベクトルデータベースに追加
                    success = self.vector_db.add_documents(documents, "NUCLEO-F767ZI")
                    
                    if success:
                        st.success(f"✅ {len(documents)}個のドキュメントチャンクを処理しました")
                        logger.info(f"Processed {len(document_files)} files into {len(documents)} chunks")
                    else:
                        st.warning("ドキュメントの登録に一部失敗しました")
                else:
                    st.warning("ドキュメントからテキストを抽出できませんでした")
            else:
                st.warning("処理可能なドキュメントが見つかりませんでした")
                
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            st.error(f"ドキュメント処理中にエラーが発生しました: {e}")
    
    def handle_microcontroller_selection(self):
        """マイコン選択の処理"""
        available_mcs = self.microcontroller_selector.get_available_microcontrollers()
        current_mc = st.session_state.current_microcontroller
        
        selected_mc = render_sidebar_microcontroller_selector(available_mcs, current_mc)
        
        if selected_mc != current_mc:
            st.session_state.current_microcontroller = selected_mc
            self.microcontroller_selector.set_current_microcontroller(selected_mc)
            st.rerun()
        
        return selected_mc
    
    def render_main_interface(self):
        """メインインターフェースのレンダリング"""
        # ヘッダー
        render_header()
        
        # マイコン選択
        selected_mc = self.handle_microcontroller_selection()
        
        # システム状態表示
        status = self.rag_engine.get_system_status()
        render_system_status(status)
        
        # 開発Tipsの表示
        tips = self.microcontroller_selector.get_development_tips(selected_mc)
        render_tips_panel(tips)
        
        # メインコンテンツ
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Q&A", "⚡ コード生成", "🔍 ドキュメント検索", "📊 マイコン情報", "🔧 デバッグ"])
        
        with tab1:
            self.render_qa_tab(selected_mc)
        
        with tab2:
            self.render_code_generation_tab(selected_mc)
        
        with tab3:
            self.render_search_tab(selected_mc)
        
        with tab4:
            self.render_microcontroller_info_tab(selected_mc)
        
        with tab5:
            self.render_debug_tab()
    
    def render_qa_tab(self, microcontroller: str):
        """Q&Aタブのレンダリング"""
        if not st.session_state.messages:
            render_welcome_message()
        
        # チャットインターフェース
        user_input = render_chat_interface()
        
        if user_input:
            # ユーザーメッセージを追加
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # RAGエンジンで回答生成
            with st.chat_message("assistant"):
                with st.spinner("回答を生成しています..."):
                    try:
                        answer_result = self.rag_engine.answer_question(
                            user_input, 
                            microcontroller
                        )
                        
                        # 回答を表示
                        answer = answer_result.get("answer", "申し訳ございません。回答を生成できませんでした。")
                        st.markdown(answer)
                        
                        # パフォーマンス指標を表示
                        render_performance_metrics(answer_result)
                        
                        # 参考資料を表示
                        sources = answer_result.get("sources", [])
                        if sources:
                            with st.expander(f"📚 参考資料 ({len(sources)}件)"):
                                for i, source in enumerate(sources, 1):
                                    st.write(f"**{i}.** {source.get('filename', '不明')} ({source.get('category', '一般')})")
                        
                        # アシスタントメッセージを追加
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        
                    except Exception as e:
                        error_msg = f"回答生成中にエラーが発生しました: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    def render_code_generation_tab(self, microcontroller: str):
        """コード生成タブのレンダリング"""
        code_interface = render_code_generator_interface()
        
        if code_interface and code_interface.get("generate", False):
            with st.spinner("コードを生成しています..."):
                try:
                    if code_interface["type"] == "custom":
                        # カスタム要求でのコード生成
                        if code_interface["request"].strip():
                            code_result = self.rag_engine.generate_code(
                                code_interface["request"],
                                microcontroller
                            )
                            render_code_display(code_result)
                        else:
                            st.warning("要求を入力してください")
                    
                    elif code_interface["type"] == "template":
                        # テンプレートからのコード生成
                        template_result = self.code_generator.generate_code_from_template(
                            code_interface["template"]
                        )
                        render_code_display(template_result)
                
                except Exception as e:
                    render_error_message(str(e))
    
    def render_search_tab(self, microcontroller: str):
        """ドキュメント検索タブのレンダリング"""
        search_interface = render_search_interface()
        
        if search_interface["search"] and search_interface["query"].strip():
            with st.spinner("ドキュメントを検索しています..."):
                try:
                    results = self.rag_engine.search_documentation(
                        search_interface["query"],
                        microcontroller,
                        search_interface["category"],
                        search_interface["count"]
                    )
                    
                    render_search_results(results)
                
                except Exception as e:
                    render_error_message(str(e))
    
    def render_microcontroller_info_tab(self, microcontroller: str):
        """マイコン情報タブのレンダリング"""
        # 基本情報の表示
        mc_info_result = self.rag_engine.get_microcontroller_info(microcontroller)
        mc_info = self.microcontroller_selector.get_microcontroller_info(microcontroller)
        
        if mc_info:
            render_microcontroller_info(mc_info.__dict__)
        
        # RAGからの詳細情報
        if mc_info_result and mc_info_result.get("info"):
            st.subheader("📝 詳細情報")
            st.write(mc_info_result["info"])
            
            # ソース情報
            sources = mc_info_result.get("sources", [])
            if sources:
                with st.expander("📚 情報源"):
                    for source in sources:
                        st.write(f"• {source.get('filename', '不明')}")
        
        # 推奨情報
        st.subheader("💡 用途別推奨")
        use_cases = ["general", "iot", "motor_control", "audio", "graphics", "security"]
        
        for use_case in use_cases:
            recommendation = self.microcontroller_selector.get_recommended_microcontroller(use_case)
            if recommendation["recommended"] == microcontroller:
                st.success(f"**{use_case.title()}用途:** {recommendation['reason']}")
    
    def render_debug_tab(self):
        """デバッグタブのレンダリング"""
        from debug_api import debug_openai_api
        debug_openai_api()
    
    def run(self):
        """アプリケーションの実行"""
        try:
            # ログアウトボタンをサイドバーに表示
            self.auth_service.show_logout_button()
            
            # ドキュメント処理
            self.process_documents_if_needed()
            
            # メインインターフェースの表示
            self.render_main_interface()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"アプリケーションエラー: {e}")
            st.info("ページを再読み込みしてみてください")

def main():
    """メイン関数"""
    try:
        app = STMicroRAGApp()
        app.run()
    except Exception as e:
        st.error(f"アプリケーションの起動に失敗しました: {e}")
        st.info("システム管理者に連絡してください")

if __name__ == "__main__":
    main()