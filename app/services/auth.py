"""
認証システム
"""
import streamlit as st
import hashlib
import time
from typing import Optional

class AuthService:
    """認証サービス"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1時間
        
    def get_admin_password(self) -> str:
        """管理者パスワードを取得"""
        try:
            return st.secrets.get("auth", {}).get("admin_password", "stm32_admin_2024")
        except:
            return "stm32_admin_2024"  # デフォルトパスワード
    
    def hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """パスワードを検証"""
        admin_password = self.get_admin_password()
        return self.hash_password(password) == self.hash_password(admin_password)
    
    def login(self, password: str) -> bool:
        """ログイン処理"""
        if self.verify_password(password):
            st.session_state.authenticated = True
            st.session_state.login_time = time.time()
            return True
        return False
    
    def logout(self):
        """ログアウト処理"""
        st.session_state.authenticated = False
        st.session_state.login_time = None
    
    def is_authenticated(self) -> bool:
        """認証状態をチェック"""
        if not st.session_state.get("authenticated", False):
            return False
        
        # セッションタイムアウトチェック
        login_time = st.session_state.get("login_time", 0)
        if time.time() - login_time > self.session_timeout:
            self.logout()
            return False
        
        return True
    
    def require_auth(self) -> bool:
        """認証を要求（未認証の場合はログイン画面を表示）"""
        if self.is_authenticated():
            return True
        
        # ログイン画面を表示
        self.show_login_form()
        return False
    
    def show_login_form(self):
        """ログインフォームを表示"""
        st.markdown("## 🔐 STマイクロRAGシステム - ログイン")
        st.markdown("---")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### システムアクセスにはパスワードが必要です")
                
                password = st.text_input(
                    "パスワードを入力してください:",
                    type="password",
                    key="login_password"
                )
                
                if st.button("ログイン", key="login_button", use_container_width=True):
                    if password:
                        if self.login(password):
                            st.success("✅ ログインに成功しました！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ パスワードが正しくありません")
                    else:
                        st.warning("⚠️ パスワードを入力してください")
                
                # システム情報を表示
                with st.expander("📖 システム情報"):
                    st.markdown("""
                    **STマイクロRAGシステム** v1.0
                    
                    **機能：**
                    - STM32 NUCLEO-F767ZI Q&Aチャット
                    - サンプルコード生成
                    - CubeMX開発ガイド
                    - Simulinkモデル作成支援
                    - 技術文書検索（1500件以上）
                    
                    **対象ユーザー：**
                    - マイコン初心者
                    - STM32開発者
                    - 学習者・研究者
                    """)
        
        st.stop()  # ログインするまで処理を停止
    
    def show_logout_button(self):
        """ログアウトボタンを表示"""
        if st.sidebar.button("🚪 ログアウト"):
            self.logout()
            st.rerun()
        
        # セッション情報を表示
        login_time = st.session_state.get("login_time", 0)
        remaining_time = self.session_timeout - (time.time() - login_time)
        
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            st.sidebar.text(f"⏰ セッション残り時間: {hours:02d}:{minutes:02d}")
        
        st.sidebar.markdown("---")