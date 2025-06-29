"""
UI コンポーネント
Streamlitアプリケーション用のUI部品
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import pandas as pd

def render_header():
    """アプリケーションヘッダーをレンダリング"""
    st.set_page_config(
        page_title="STマイクロマイコン RAGシステム",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔧 STマイクロマイコン RAGシステム")
    st.markdown("**マイコン初心者向けQ&A・サンプルコード生成システム**")
    st.divider()

def render_sidebar_microcontroller_selector(microcontrollers: List[str], current: str):
    """サイドバーにマイコン選択UIをレンダリング"""
    st.sidebar.header("🎯 マイコン選択")
    
    selected = st.sidebar.selectbox(
        "使用するマイコンを選択してください",
        microcontrollers,
        index=microcontrollers.index(current) if current in microcontrollers else 0,
        help="質問や要求に使用するマイコンを選択します"
    )
    
    return selected

def render_microcontroller_info(mc_info: Dict):
    """マイコン情報を表示"""
    if not mc_info:
        st.warning("マイコン情報が取得できませんでした")
        return
    
    st.subheader(f"📊 {mc_info['name']} 仕様")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("シリーズ", mc_info['series'])
        st.metric("コア", mc_info['core'])
    
    with col2:
        st.metric("動作周波数", mc_info['frequency'])
        st.metric("フラッシュメモリ", mc_info['flash'])
    
    with col3:
        st.metric("RAM", mc_info['ram'])
    
    st.write("**説明:**", mc_info['description'])
    
    # 特徴とペリフェラルを表示
    if hasattr(mc_info, 'features') and mc_info.features:
        with st.expander("🌟 主な特徴"):
            for feature in mc_info.features[:8]:  # 最大8個まで表示
                st.write(f"• {feature}")
    
    if hasattr(mc_info, 'peripherals') and mc_info.peripherals:
        with st.expander("🔌 ペリフェラル"):
            for peripheral in mc_info.peripherals[:10]:  # 最大10個まで表示
                st.write(f"• {peripheral}")

def render_chat_interface():
    """チャットインターフェースをレンダリング"""
    st.subheader("💬 Q&A チャット")
    
    # チャット履歴の初期化
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "STマイクロマイコンについて何でもお聞きください！マイコンの基本的な使い方からCubeMXの操作方法まで、初心者の方にも分かりやすくお答えします。"}
        ]
    
    # チャット履歴の表示
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # ユーザー入力
    if prompt := st.chat_input("質問を入力してください（例：LEDを点滅させる方法を教えて）"):
        return prompt
    
    return None

def render_code_generator_interface():
    """コード生成インターフェースをレンダリング"""
    st.subheader("⚡ サンプルコード生成")
    
    # コード生成タイプの選択
    code_type = st.selectbox(
        "生成するコードのタイプを選択",
        ["カスタム要求", "テンプレートから選択"],
        help="カスタム要求では自由記述、テンプレートでは定型的なコード生成が可能です"
    )
    
    if code_type == "カスタム要求":
        request = st.text_area(
            "実現したい機能を記述してください",
            placeholder="例：ボタンを押すたびにLEDの明るさが変わるPWM制御",
            height=100
        )
        
        generate_button = st.button("🚀 コード生成", type="primary")
        
        return {"type": "custom", "request": request, "generate": generate_button}
    
    else:
        template_options = [
            ("LED_CONTROL", "LED制御 - 基本的なLED点滅"),
            ("BUTTON_INPUT", "ボタン入力 - デバウンス処理付き"),
            ("PWM_OUTPUT", "PWM出力 - デューティ比制御")
        ]
        
        selected_template = st.selectbox(
            "テンプレートを選択",
            template_options,
            format_func=lambda x: x[1]
        )
        
        generate_button = st.button("📝 テンプレート生成", type="primary")
        
        return {
            "type": "template", 
            "template": selected_template[0], 
            "generate": generate_button
        }

def render_code_display(code_result: Dict):
    """生成されたコードを表示"""
    if not code_result:
        return
    
    if code_result.get("success", True):
        st.success("コード生成が完了しました！")
        
        # コードの表示
        st.code(code_result.get("code", ""), language="c")
        
        # 説明の表示
        if "explanation" in code_result:
            st.info(f"**説明:** {code_result['explanation']}")
        
        # 追加情報の表示
        if "features" in code_result:
            with st.expander("📋 このコードの特徴"):
                for feature in code_result["features"]:
                    st.write(f"• {feature}")
        
        if "includes" in code_result:
            with st.expander("📁 必要なインクルードファイル"):
                for include in code_result["includes"]:
                    st.code(f'#include "{include}"', language="c")
    
    else:
        st.error(f"コード生成に失敗しました: {code_result.get('error', '不明なエラー')}")

def render_search_interface():
    """ドキュメント検索インターフェースをレンダリング"""
    st.subheader("🔍 ドキュメント検索")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "検索キーワードを入力",
            placeholder="例：GPIO設定、タイマー割り込み、CubeMX"
        )
    
    with col2:
        search_button = st.button("検索", type="primary")
    
    # フィルターオプション
    with st.expander("🔧 検索フィルター"):
        col1, col2 = st.columns(2)
        
        with col1:
            category_filter = st.selectbox(
                "カテゴリでフィルター",
                ["すべて", "hardware", "software_tool", "application_note", "user_manual", "technical_note"],
                help="特定のドキュメントカテゴリに絞り込みます"
            )
        
        with col2:
            result_count = st.slider("最大検索結果数", 5, 20, 10)
    
    return {
        "query": search_query,
        "search": search_button,
        "category": category_filter if category_filter != "すべて" else None,
        "count": result_count
    }

def render_search_results(results: List[Dict]):
    """検索結果を表示"""
    if not results:
        st.info("検索結果がありません。別のキーワードをお試しください。")
        return
    
    st.success(f"{len(results)}件の関連ドキュメントが見つかりました")
    
    for i, result in enumerate(results, 1):
        with st.expander(f"📄 {i}. {result.get('source', '不明')} ({result.get('category', '一般')}) - 関連度: {result.get('relevance_score', 0):.2f}"):
            st.write(result.get('content', '内容が取得できませんでした'))
            
            # メタデータの表示
            if 'metadata' in result:
                metadata = result['metadata']
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'filename' in metadata:
                        st.caption(f"ファイル: {metadata['filename']}")
                
                with col2:
                    if 'chunk_index' in metadata:
                        st.caption(f"セクション: {metadata['chunk_index']}")
                
                with col3:
                    if 'char_count' in metadata:
                        st.caption(f"文字数: {metadata['char_count']}")

def render_system_status(status: Dict):
    """システム状態を表示"""
    st.sidebar.subheader("⚙️ システム状態")
    
    # LLM状態
    llm_status = "🟢 利用可能" if status.get("llm_available", False) else "🔴 利用不可"
    st.sidebar.write(f"**LLM:** {llm_status}")
    
    # ベクトルDB状態
    vdb_status = "🟢 利用可能" if status.get("vector_db_available", False) else "🔴 利用不可"
    st.sidebar.write(f"**ベクトルDB:** {vdb_status}")
    
    # サポートマイコン数
    mc_count = len(status.get("supported_microcontrollers", []))
    st.sidebar.write(f"**サポートマイコン数:** {mc_count}")
    
    # コレクション数
    collection_count = len(status.get("vector_db_collections", []))
    st.sidebar.write(f"**登録ドキュメント:** {collection_count} コレクション")

def render_tips_panel(tips: List[str]):
    """開発Tipsパネルを表示"""
    if tips:
        st.sidebar.subheader("💡 開発Tips")
        for i, tip in enumerate(tips[:3], 1):  # 最大3つまで表示
            st.sidebar.info(f"**Tip {i}:** {tip}")

def render_answer_display(answer_result: Dict):
    """RAG回答を表示"""
    if not answer_result:
        return
    
    # 回答の表示
    st.markdown("### 🤖 回答")
    st.write(answer_result.get("answer", "回答を生成できませんでした"))
    
    # 信頼度の表示
    confidence = answer_result.get("confidence", 0.0)
    if confidence > 0:
        st.progress(confidence, f"信頼度: {confidence:.1%}")
    
    # ソース情報の表示
    sources = answer_result.get("sources", [])
    if sources:
        with st.expander(f"📚 参考資料 ({len(sources)}件)"):
            for i, source in enumerate(sources, 1):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{i}.** {source.get('filename', '不明')}")
                
                with col2:
                    st.caption(source.get('category', '一般'))
                
                with col3:
                    relevance = source.get('relevance', 0.0)
                    st.caption(f"関連度: {relevance:.2f}")

def render_performance_metrics(metrics: Dict):
    """パフォーマンス指標を表示"""
    if not metrics:
        return
    
    with st.expander("📊 応答パフォーマンス"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "context_length" in metrics:
                st.metric("コンテキスト長", f"{metrics['context_length']:,} 文字")
        
        with col2:
            if "num_sources" in metrics:
                st.metric("参照ソース数", f"{metrics['num_sources']} 件")
        
        with col3:
            if "confidence" in metrics:
                st.metric("信頼度", f"{metrics['confidence']:.1%}")

def render_error_message(error: str):
    """エラーメッセージを表示"""
    st.error(f"⚠️ エラーが発生しました: {error}")
    st.info("問題が続く場合は、以下をお試しください：\n"
           "1. 質問を言い換える\n"
           "2. より具体的なキーワードを使用する\n"
           "3. システム管理者に連絡する")

def render_welcome_message():
    """ウェルカムメッセージを表示"""
    st.markdown("""
    ### 👋 STマイクロマイコン RAGシステムへようこそ！
    
    このシステムでは以下の機能が利用できます：
    
    🔍 **Q&Aチャット**
    - マイコンの基本的な使い方
    - CubeMXの操作方法
    - 回路設計のアドバイス
    - トラブルシューティング
    
    ⚡ **サンプルコード生成**
    - LED制御、ボタン入力、PWM制御など
    - 初心者向けの詳細なコメント付き
    - カスタム要求にも対応
    
    📚 **ドキュメント検索**
    - 技術文書からの情報検索
    - アプリケーションノートの参照
    - ユーザーマニュアルの検索
    
    まずは左側のサイドバーでマイコンを選択し、気軽に質問してみてください！
    """)

def create_microcontroller_comparison_chart(comparison_data: Dict):
    """マイコン比較チャートを作成"""
    if not comparison_data or "comparison_table" not in comparison_data:
        return None
    
    # データの準備
    df_data = []
    for item, values in comparison_data["comparison_table"].items():
        for mc_name, value in values.items():
            df_data.append({
                "項目": item,
                "マイコン": mc_name,
                "値": value
            })
    
    if not df_data:
        return None
    
    df = pd.DataFrame(df_data)
    
    # チャートの作成
    fig = px.bar(
        df, 
        x="項目", 
        y="値", 
        color="マイコン",
        title="マイコン仕様比較",
        barmode="group"
    )
    
    return fig