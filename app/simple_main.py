"""
シンプル版STマイクロRAGシステム - 確実に動作するバージョン
"""
import streamlit as st
import os
import logging
from typing import List, Dict, Optional
from langchain.schema import Document
import openai

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 認証機能
def check_auth():
    """簡単認証"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 STマイクロRAGシステム - ログイン")
        password = st.text_input("パスワードを入力してください", type="password")
        
        if st.button("ログイン"):
            if password == "stm32_rag_admin_2024":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが間違っています")
        st.stop()

# OpenAI設定
def get_openai_client():
    """OpenAIクライアント取得"""
    try:
        api_key = st.secrets["api_keys"]["openai_api_key"]
        return openai.OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"OpenAI設定エラー: {e}")
        return None

# 文書データ（インメモリ）
EMBEDDED_DOCS = [
    {
        "title": "STM32F767ZI基本仕様",
        "content": """
STM32F767ZI マイクロコントローラの基本仕様：
- ARM Cortex-M7コア（216MHz）
- 2MB Flash メモリ
- 512KB RAM
- 144ピンLQFPパッケージ
- GPIO: 最大114本
- タイマー: 17個（基本、汎用、高度制御）
- 通信: UART×4、SPI×6、I2C×4、CAN×3、USB OTG×2
- ADC: 3個（12bit、最大24チャンネル）
- DAC: 2個（12bit）
- 動作電圧: 1.7V～3.6V
""",
        "category": "仕様"
    },
    {
        "title": "GPIO基本設定",
        "content": """
STM32F767ZI GPIO基本設定：

1. GPIOクロック有効化：
__HAL_RCC_GPIOx_CLK_ENABLE();

2. GPIO設定構造体：
GPIO_InitTypeDef GPIO_InitStruct = {0};
GPIO_InitStruct.Pin = GPIO_PIN_x;
GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
GPIO_InitStruct.Pull = GPIO_NOPULL;
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;

3. GPIO初期化：
HAL_GPIO_Init(GPIOx, &GPIO_InitStruct);

4. GPIO制御：
HAL_GPIO_WritePin(GPIOx, GPIO_PIN_x, GPIO_PIN_SET);
HAL_GPIO_WritePin(GPIOx, GPIO_PIN_x, GPIO_PIN_RESET);
""",
        "category": "GPIO"
    },
    {
        "title": "UART通信設定",
        "content": """
STM32F767ZI UART通信設定：

1. UART初期化：
UART_HandleTypeDef huart3;
huart3.Instance = USART3;
huart3.Init.BaudRate = 115200;
huart3.Init.WordLength = UART_WORDLENGTH_8B;
huart3.Init.StopBits = UART_STOPBITS_1;
huart3.Init.Parity = UART_PARITY_NONE;
huart3.Init.Mode = UART_MODE_TX_RX;
huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;

2. データ送信：
HAL_UART_Transmit(&huart3, (uint8_t*)data, strlen(data), HAL_MAX_DELAY);

3. データ受信：
HAL_UART_Receive(&huart3, (uint8_t*)buffer, size, HAL_MAX_DELAY);
""",
        "category": "UART"
    },
    {
        "title": "Simulink STM32サポート",
        "content": """
MATLAB/Simulink STM32サポート：

1. サポートパッケージのインストール：
- Embedded Coder Support Package for STMicroelectronics STM32 Processors

2. モデル設定：
- Target Hardware: STM32F7xx
- Board: NUCLEO-F767ZI
- Hardware Implementation: STM32F767ZI

3. ブロック利用例：
- Digital Input/Output
- Analog Input (ADC)
- PWM Output
- Serial Receive/Transmit
- Timer Counter

4. コード生成：
Ctrl+B でコード生成・フラッシュ書き込み実行
""",
        "category": "Simulink"
    },
    {
        "title": "PWM設定",
        "content": """
STM32F767ZI PWM設定：

1. タイマークロック有効化：
__HAL_RCC_TIM1_CLK_ENABLE();

2. タイマー設定：
TIM_HandleTypeDef htim1;
htim1.Instance = TIM1;
htim1.Init.Prescaler = 215; // 216MHz -> 1MHz
htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
htim1.Init.Period = 999; // 1kHz PWM
htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;

3. PWM出力設定：
TIM_OC_InitTypeDef sConfigOC = {0};
sConfigOC.OCMode = TIM_OCMODE_PWM1;
sConfigOC.Pulse = 500; // 50% duty cycle
sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;

4. PWM開始：
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
""",
        "category": "PWM"
    }
]

def simple_search(query: str, docs: List[Dict]) -> List[Dict]:
    """シンプル検索"""
    query_lower = query.lower()
    results = []
    
    for doc in docs:
        content_lower = doc["content"].lower()
        title_lower = doc["title"].lower()
        
        # キーワードマッチング
        if (query_lower in content_lower or 
            query_lower in title_lower or
            any(keyword in content_lower for keyword in query_lower.split())):
            results.append(doc)
    
    return results[:3]  # 上位3件

def generate_answer(question: str, client) -> str:
    """OpenAIで回答生成"""
    if not client:
        return "OpenAI接続エラーのため、テンプレート回答を使用できません。"
    
    # 関連文書を検索
    relevant_docs = simple_search(question, EMBEDDED_DOCS)
    
    if not relevant_docs:
        return "申し訳ございませんが、関連する情報が見つかりませんでした。質問を言い換えてお試しください。"
    
    # コンテキスト作成
    context = "\n\n".join([f"【{doc['title']}】\n{doc['content']}" for doc in relevant_docs])
    
    # プロンプト作成
    prompt = f"""
STM32 NUCLEO-F767ZI開発に関する質問に、提供された技術文書を参考にして回答してください。

質問: {question}

参考文書:
{context}

回答は以下の形式で作成してください：
1. 簡潔で分かりやすい説明
2. 具体的なコード例（該当する場合）
3. 注意点やベストプラクティス

回答:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"回答生成中にエラーが発生しました: {e}"

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="STマイクロRAGシステム",
        page_icon="🔬",
        layout="wide"
    )
    
    # 認証チェック
    check_auth()
    
    # OpenAIクライアント取得
    client = get_openai_client()
    
    # ヘッダー
    st.title("🔬 STマイクロRAGシステム")
    st.subheader("STM32 NUCLEO-F767ZI 開発支援AI")
    
    # システム状態表示
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 ドキュメント", len(EMBEDDED_DOCS))
    with col2:
        status = "🟢 利用可能" if client else "🔴 利用不可"
        st.metric("🤖 LLM", status)
    with col3:
        st.metric("🔧 マイコン", "NUCLEO-F767ZI")
    
    # メインコンテンツ
    tab1, tab2 = st.tabs(["💬 Q&A", "📋 文書一覧"])
    
    with tab1:
        st.markdown("### STM32開発に関する質問をお聞かせください")
        
        # チャット履歴
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # チャット表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # ユーザー入力
        if prompt := st.chat_input("質問を入力してください（例：GPIO設定方法、UART通信、PWM制御など）"):
            # ユーザーメッセージ追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI回答生成
            with st.chat_message("assistant"):
                with st.spinner("回答を生成しています..."):
                    answer = generate_answer(prompt, client)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
    
    with tab2:
        st.markdown("### 利用可能な技術文書")
        for doc in EMBEDDED_DOCS:
            with st.expander(f"📄 {doc['title']} ({doc['category']})"):
                st.markdown(doc['content'])
    
    # サイドバー
    with st.sidebar:
        st.markdown("### 🔧 システム情報")
        st.info("STM32 NUCLEO-F767ZI専用RAGシステム")
        
        if st.button("🚪 ログアウト"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()