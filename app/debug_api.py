"""
OpenAI API キーのデバッグツール
"""
import streamlit as st
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_openai_api():
    """OpenAI APIの動作確認"""
    st.title("🔧 OpenAI API デバッグツール")
    
    # API キーの取得と表示
    try:
        api_key = st.secrets.get("api_keys", {}).get("openai_api_key", "")
        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-8:] if len(api_key) > 16 else "短すぎます"
            st.success(f"✅ API キーが見つかりました: {masked_key}")
            
            # APIキーの長さチェック
            if len(api_key) < 20:
                st.error("❌ APIキーが短すぎます。正しいキーを設定してください。")
                return
                
        else:
            st.error("❌ API キーが見つかりません")
            return
    except Exception as e:
        st.error(f"❌ Secrets読み取りエラー: {e}")
        return
    
    # OpenAI クライアントのテスト
    if st.button("🧪 OpenAI API テスト"):
        try:
            with st.spinner("APIテスト中..."):
                client = OpenAI(api_key=api_key)
                
                # シンプルなテストリクエスト
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": "Hello! 日本語で短く挨拶してください。"}
                    ],
                    max_tokens=50,
                    temperature=0.7
                )
                
                st.success("✅ OpenAI API テスト成功！")
                st.write("**応答:**", response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"❌ OpenAI API テスト失敗: {e}")
            logger.error(f"OpenAI API test failed: {e}")
    
    # 設定情報の表示
    st.subheader("📋 現在の設定")
    
    try:
        secrets_info = {
            "api_keys": "✅ あり" if st.secrets.get("api_keys") else "❌ なし",
            "auth": "✅ あり" if st.secrets.get("auth") else "❌ なし",
        }
        st.json(secrets_info)
    except Exception as e:
        st.error(f"設定確認エラー: {e}")
    
    # ベクターDB状態をチェック
    st.subheader("📊 ベクターDB状態")
    if st.button("🔍 ベクターDB診断"):
        try:
            from models.simple_vector_db import SimpleVectorDatabase
            from config import Config
            
            vector_db = SimpleVectorDatabase()
            doc_count = len(vector_db.documents)
            
            st.write(f"**ドキュメント数**: {doc_count}")
            st.write(f"**ベクターDB パス**: {Config.get_vector_db_path()}")
            
            if doc_count == 0:
                st.error("❌ ベクターDBが空です！")
                
                # ブートストラップを実行
                if st.button("🚀 基本文書を初期化"):
                    from bootstrap_docs import OnlineDocumentBootstrap
                    bootstrap = OnlineDocumentBootstrap(vector_db)
                    
                    with st.spinner("初期化中..."):
                        success = bootstrap.bootstrap_documents()
                        if success:
                            st.success("✅ 基本文書の初期化完了！")
                            st.rerun()
                        else:
                            st.error("❌ 初期化失敗")
                
                # 直接実行ボタンも追加
                if st.button("⚡ 今すぐ初期化実行"):
                    from bootstrap_docs import OnlineDocumentBootstrap
                    bootstrap = OnlineDocumentBootstrap(vector_db)
                    st.write("初期化を開始します...")
                    success = bootstrap.bootstrap_documents()
                    st.write(f"初期化結果: {success}")
                    if success:
                        new_count = len(vector_db.documents) 
                        st.success(f"✅ {new_count}個の文書を追加しました！")
                    else:
                        st.error("❌ 初期化に失敗しました")
            else:
                st.success(f"✅ ベクターDBに{doc_count}個の文書があります")
                
                # サンプル検索テスト
                if st.button("🧪 検索テスト"):
                    results = vector_db.similarity_search("GPIO設定", k=3)
                    if results:
                        st.success(f"✅ {len(results)}件の関連文書が見つかりました")
                        for i, doc in enumerate(results[:2]):
                            st.write(f"**{i+1}.** {doc.page_content[:100]}...")
                    else:
                        st.error("❌ 関連文書が見つかりませんでした")
                        
        except Exception as e:
            st.error(f"ベクターDB診断エラー: {e}")
    
    # 簡易修正案の提示
    st.subheader("🔧 推奨修正案")
    st.markdown("""
    **回答が生成されない場合の対処法：**
    
    1. **ベクターDBの初期化**
       - 上記の「🚀 基本文書を初期化」ボタンを実行
    
    2. **Q&Aタブでテスト**
       - 「GPIO設定方法を教えて」などの質問を試す
    
    3. **アプリ再起動**
       - 問題が続く場合は「Reboot app」を実行
    """)

if __name__ == "__main__":
    debug_openai_api()