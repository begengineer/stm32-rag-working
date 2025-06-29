"""
シンプルなRAGエンジン（TF-IDF + テンプレートベース回答生成 + OpenAI統合）
"""
import logging
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document
from langchain.prompts import PromptTemplate

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.simple_vector_db import SimpleVectorDatabase

# OpenAI統合のためのインポート
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Install with: pip install openai")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAGEngine:
    """シンプルなRAGエンジン"""
    
    def __init__(self, vector_db: SimpleVectorDatabase = None, use_openai: bool = True):
        self.vector_db = vector_db or SimpleVectorDatabase()
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_client = None
        
        # OpenAI クライアントの初期化
        if self.use_openai:
            api_key = Config.get_openai_api_key()
            if api_key:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.use_openai = False
            else:
                self.use_openai = False
                logger.info("OpenAI API key not found")
        else:
            self.use_openai = False
            logger.info("Using template-based responses (OpenAI not available)")
        
        self._setup_prompts()
        self._setup_templates()
    
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
    
    def _setup_templates(self):
        """回答テンプレートの設定"""
        self.answer_templates = {
            "gpio": {
                "keywords": ["gpio", "ピン", "pin", "led", "ボタン", "button", "出力", "入力"],
                "template": """
{microcontroller}のGPIOについて説明します。

**GPIO（General Purpose Input/Output）**
- デジタル入出力ピンとして使用
- HAL_GPIO_WritePin()で出力制御
- HAL_GPIO_ReadPin()で入力読み取り
- HAL_GPIO_Init()で初期化

**基本的な使用例：**
```c
// LED制御例
HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);   // HIGH出力
HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET); // LOW出力

// ボタン読み取り例
GPIO_PinState state = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
```

関連ドキュメント: {sources}
                """,
            },
            "timer": {
                "keywords": ["timer", "タイマー", "pwm", "tim", "カウンタ", "counter"],
                "template": """
{microcontroller}のタイマー機能について説明します。

**タイマーの主な用途：**
- PWM信号生成
- 時間計測・遅延生成
- 定期的な割り込み処理
- エンコーダー入力

**HAL関数の例：**
```c
// PWM出力
HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
__HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, duty_cycle);

// 基本タイマー
HAL_TIM_Base_Start_IT(&htim2);  // 割り込み付きスタート
```

関連ドキュメント: {sources}
                """,
            },
            "uart": {
                "keywords": ["uart", "usart", "serial", "通信", "シリアル"],
                "template": """
{microcontroller}のUART通信について説明します。

**UART（Universal Asynchronous Receiver Transmitter）**
- 非同期シリアル通信
- ボーレート、データビット、パリティ、ストップビット設定
- DMA転送対応

**基本的な使用例：**
```c
// データ送信
uint8_t data[] = "Hello World";
HAL_UART_Transmit(&huart3, data, strlen(data), HAL_MAX_DELAY);

// データ受信
uint8_t buffer[100];
HAL_UART_Receive(&huart3, buffer, sizeof(buffer), 5000);
```

関連ドキュメント: {sources}
                """,
            },
            "adc": {
                "keywords": ["adc", "analog", "アナログ", "変換", "センサー"],
                "template": """
{microcontroller}のADC（アナログ-デジタル変換）について説明します。

**ADCの特徴：**
- 12ビット分解能
- 複数チャンネル対応
- DMA転送対応
- 内部基準電圧使用可能

**基本的な使用例：**
```c
// ADC開始
HAL_ADC_Start(&hadc1);

// 変換完了待ち
HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);

// 値読み取り
uint32_t adc_value = HAL_ADC_GetValue(&hadc1);
```

関連ドキュメント: {sources}
                """,
            },
            "i2c": {
                "keywords": ["i2c", "iic", "通信", "センサー", "eeprom"],
                "template": """
{microcontroller}のI2C通信について説明します。

**I2C（Inter-Integrated Circuit）**
- 2線式シリアル通信（SDA, SCL）
- マスター/スレーブ構成
- 複数デバイス接続可能

**基本的な使用例：**
```c
// データ送信
uint8_t data[] = {{0x01, 0x02}};
HAL_I2C_Master_Transmit(&hi2c1, DEVICE_ADDRESS, data, 2, HAL_MAX_DELAY);

// データ受信
uint8_t buffer[10];
HAL_I2C_Master_Receive(&hi2c1, DEVICE_ADDRESS, buffer, 10, HAL_MAX_DELAY);
```

関連ドキュメント: {sources}
                """,
            },
            "spi": {
                "keywords": ["spi", "serial", "通信", "lcd", "sd"],
                "template": """
{microcontroller}のSPI通信について説明します。

**SPI（Serial Peripheral Interface）**
- 4線式シリアル通信（MOSI, MISO, SCK, CS）
- 高速通信可能
- 全二重通信

**基本的な使用例：**
```c
// データ送信
uint8_t tx_data[] = {{0x01, 0x02}};
HAL_SPI_Transmit(&hspi1, tx_data, 2, HAL_MAX_DELAY);

// データ送受信
uint8_t rx_data[2];
HAL_SPI_TransmitReceive(&hspi1, tx_data, rx_data, 2, HAL_MAX_DELAY);
```

関連ドキュメント: {sources}
                """,
            },
            "simulink": {
                "keywords": ["simulink", "matlab", "モデル", "ブロック", "配置", "シミュレーション", "コード生成", "embedded coder"],
                "template": """
NUCLEO-F767ZIでのSimulink開発について説明します。

**Simulink Support Package for STM32 Nucleo**
- Simulink Coder Support Package for STMicroelectronics Nucleo boards
- モデルベース開発でSTM32マイコンを制御
- ハードウェア・イン・ザ・ループ（HIL）テスト対応

**初期設定手順：**
1. **Support Packageのインストール**
   - MATLAB Add-Onsから「Simulink Coder Support Package for STMicroelectronics Nucleo boards」をインストール
   - ハードウェア設定でNUCLEO-F767ZIを選択

2. **開発環境設定**
   - STM32CubeMXとの統合設定
   - コンパイラ（ARM GCC）の設定
   - ボード接続の確認

**利用可能なブロック：**
- **Digital I/O**: デジタル入出力制御
- **ADC**: アナログ入力読み取り
- **PWM**: パルス幅変調出力
- **UART/SCI**: シリアル通信
- **I2C/SPI**: ペリフェラル通信
- **CAN**: CAN通信（F767ZI対応）
- **Timer**: タイマー・カウンター
- **Interrupt**: 割り込み処理

**モデル作成手順：**
1. **新規Simulinkモデル作成**
   - Simulink Library Browserから必要なブロックを配置
   - STM32 Nucleoライブラリブロックを使用

2. **ブロック配置とパラメータ設定**
   - ペリフェラルブロックの配置
   - ピン番号とパラメータの設定
   - 信号線の接続

3. **モデル設定**
   - Configuration Parametersでターゲットハードウェア設定
   - サンプル時間の設定
   - ソルバーの選択

**コード生成とデプロイメント：**
1. **ビルド設定**
   - Ctrl+B でモデルをビルド
   - 自動的にC/C++コードを生成
   - STM32向けに最適化されたコードを出力

2. **プログラム書き込み**
   - ST-LINKを使用してボードに自動書き込み
   - シリアル通信でのデータ監視

**デバッグとモニタリング：**
- **External Mode**: リアルタイムでの信号監視とパラメータ調整
- **Connected I/O**: Simulinkからハードウェアを直接制御
- **PIL (Processor-in-the-Loop)**: プロセッサでの実行テスト

**サンプルアプリケーション例：**
```
LED点滅制御モデル：
[Pulse Generator] → [Digital Output (GPIO)]

ADC読み取りモデル：
[ADC Input] → [Display/Scope]

PWMモーター制御：
[Signal Generator] → [PWM Output] → [Motor Control]

CAN通信モデル：
[CAN Transmit] ↔ [CAN Receive]
```

**ベストプラクティス：**
- 固定ステップソルバーを使用
- 適切なサンプル時間の設定（1ms推奨）
- ハードウェア制約を考慮したモデル設計
- External Modeでのリアルタイムテスト活用

関連ドキュメント: {sources}
                """,
            },
            "cubemx": {
                "keywords": ["cubemx", "cube", "プロジェクト作成", "ピン設定", "コード生成", "設定ツール", "初期化"],
                "template": """
STM32CubeMXについて説明します。

**STM32CubeMXとは：**
- STMicroelectronicsが提供するグラフィカル設定ツール
- ピン配置とペリフェラル設定の視覚的な設定
- 初期化コードの自動生成
- プロジェクトテンプレートの生成

**基本的な使用手順：**
1. **新規プロジェクト作成**
   - File → New Project
   - マイコン選択（{microcontroller}等）
   - プロジェクト名と保存場所を指定

2. **ピン設定（Pinout Configuration）**
   - ピン機能の割り当て（GPIO、UART、SPI等）
   - 代替機能の設定
   - 信号の割り当て確認

3. **クロック設定（Clock Configuration）**
   - システムクロックの設定
   - ペリフェラルクロックの設定
   - 消費電力の最適化

4. **ペリフェラル設定（Peripheral Configuration）**
   - 各ペリフェラルの詳細設定
   - 割り込み設定
   - DMA設定

5. **コード生成**
   - Project → Generate Code
   - HAL/LLライブラリの選択
   - IDEプロジェクトファイルの生成

**生成されるファイル：**
- main.c（メイン関数）
- stm32f7xx_hal_conf.h（HAL設定）
- stm32f7xx_it.c（割り込みハンドラー）
- GPIO、Timer等の初期化関数

**便利な機能：**
- ピン競合の自動検出
- リソース使用量の表示
- 消費電力の計算
- ドキュメント生成

関連ドキュメント: {sources}
                """,
            },
            "general": {
                "keywords": [],
                "template": """
{microcontroller}に関する情報をお探しですね。

**STM32F767ZI Nucleoボードの概要：**
- ARM Cortex-M7コア（216MHz）
- 2MB Flash、512KB RAM
- 豊富なペリフェラル（GPIO、Timer、UART、SPI、I2C、ADC等）
- Arduino互換ピン配置

**開発環境：**
- STM32CubeIDE
- STM32CubeMX（設定ツール）
- HALライブラリ使用

関連ドキュメント: {sources}

より具体的な質問をお聞かせください。
                """,
            }
        }
        
        self.code_templates = {
            "led": """// {microcontroller} LED制御サンプル
#include "main.h"

void LED_Blink_Example(void)
{{
    while (1)
    {{
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);    // LED点灯
        HAL_Delay(500);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);  // LED消灯
        HAL_Delay(500);
    }}
}}""",
            
            "button": """// {microcontroller} ボタン入力サンプル
#include "main.h"

void Button_Control_Example(void)
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
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET); // LED消灯
    }}
}}""",
            
            "pwm": """// {microcontroller} PWM制御サンプル
#include "main.h"

TIM_HandleTypeDef htim3;

void PWM_Control_Example(void)
{{
    // PWM開始
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
    
    // デューティ比を変更（0-1000）
    for (uint32_t duty = 0; duty <= 1000; duty += 10)
    {{
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, duty);
        HAL_Delay(10);
    }}
}}""",
            
            "uart": """// {microcontroller} UART通信サンプル
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
    if (HAL_UART_Receive(&huart3, rx_buffer, sizeof(rx_buffer)-1, 5000) == HAL_OK)
    {{
        // 受信データ処理
        rx_buffer[99] = '\\0';  // 文字列終端
        // 受信データの処理をここに記述
    }}
}}""",
            
            "adc": """// {microcontroller} ADC読み取りサンプル
#include "main.h"

ADC_HandleTypeDef hadc1;

uint32_t ADC_Read_Example(void)
{{
    uint32_t adc_value;
    
    // ADC開始
    HAL_ADC_Start(&hadc1);
    
    // 変換完了待ち
    if (HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY) == HAL_OK)
    {{
        // 値読み取り
        adc_value = HAL_ADC_GetValue(&hadc1);
        
        // 電圧計算例（3.3V基準、12bit）
        float voltage = (adc_value * 3.3f) / 4095.0f;
    }}
    
    HAL_ADC_Stop(&hadc1);
    return adc_value;
}}""",
            
            "simulink": """// {microcontroller} Simulink自動生成コード例
/* Simulinkモデルから生成されたC/C++コード */
#include "rtwtypes.h"
#include "model.h"
#include "model_private.h"

/* Model step function */
void model_step(void)
{{
    /* Simulinkブロック図に基づく処理 */
    
    /* Digital Input読み取り */
    rtU.DigitalInput = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_0);
    
    /* アルゴリズム処理（Simulinkモデルで定義） */
    if (rtU.DigitalInput == 1) {{
        rtY.DigitalOutput = 1;
        rtY.PWMOutput = 50.0; /* 50% duty cycle */
    }} else {{
        rtY.DigitalOutput = 0;
        rtY.PWMOutput = 0.0;
    }}
    
    /* Digital Output設定 */
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, rtY.DigitalOutput);
    
    /* PWM出力設定 */
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, (uint32_t)(rtY.PWMOutput * 10));
}}

/* Model initialize function */
void model_initialize(void)
{{
    /* Simulinkで設定された初期化処理 */
    rtU.DigitalInput = 0;
    rtY.DigitalOutput = 0;
    rtY.PWMOutput = 0.0;
}}

/* Model terminate function */
void model_terminate(void)
{{
    /* 終了処理（必要に応じて） */
}}

/*
Simulinkモデル設計のポイント:
1. ブロック配置: Library Browser → STM32 Nucleo
2. ピン設定: ブロックパラメータでピン番号指定
3. サンプル時間: 0.001 (1ms) 推奨
4. ソルバー: Fixed-step discrete
5. External Mode: リアルタイムモニタリング用
*/""",
            
            "cubemx": """// {microcontroller} CubeMX生成プロジェクト基本構造
#include "main.h"

/* CubeMXで生成される関数のプロトタイプ */
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART3_UART_Init(void);
static void MX_TIM3_Init(void);

/* ユーザーコード開始位置 */
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

int main(void)
{{
    /* USER CODE BEGIN 1 */
    
    /* USER CODE END 1 */
    
    /* MCU設定 */
    HAL_Init();
    
    /* システムクロック設定 */
    SystemClock_Config();
    
    /* CubeMXで生成される初期化関数 */
    MX_GPIO_Init();
    MX_USART3_UART_Init();
    MX_TIM3_Init();
    
    /* USER CODE BEGIN 2 */
    
    /* USER CODE END 2 */
    
    /* メインループ */
    while (1)
    {{
        /* USER CODE BEGIN 3 */
        
        /* USER CODE END 3 */
    }}
}}

/*
CubeMX使用時の注意点:
1. USER CODE BEGIN/ENDブロック内にのみコードを記述
2. CubeMXでコード再生成してもユーザーコードは保持される
3. 初期化関数は自動生成されるため手動変更不要
4. ペリフェラル設定変更はCubeMXで行う
*/""",
        }
    
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
                microcontroller=microcontroller,
                score_threshold=0.05  # より緩い閾値
            )
            
            if not relevant_docs:
                return {
                    "answer": "申し訳ございませんが、関連する情報が見つかりませんでした。質問を言い換えてお試しください。",
                    "sources": [],
                    "confidence": 0.0,
                    "microcontroller": microcontroller
                }
            
            # 2. 回答生成
            answer = self._generate_answer(question, relevant_docs, microcontroller)
            
            # 3. 信頼度計算
            confidence = self._calculate_confidence(relevant_docs)
            
            # 4. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "microcontroller": microcontroller,
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
    
    def _generate_answer(self, question: str, relevant_docs: List[Tuple[Document, float]], microcontroller: str) -> str:
        """回答生成（OpenAI API使用可能時はより高品質な回答を生成）"""
        
        # ソース情報を作成
        sources = [doc.metadata.get("filename", "不明") for doc, _ in relevant_docs[:3]]
        source_str = ", ".join(sources) if sources else "関連ドキュメント"
        
        # OpenAI APIが利用可能な場合は高品質な回答を生成
        if self.use_openai and self.openai_client and relevant_docs:
            try:
                return self._generate_openai_answer(question, relevant_docs, microcontroller, source_str)
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
                logger.info("Falling back to template-based response")
        
        # フォールバック：テンプレートベース回答
        return self._generate_template_answer(question, relevant_docs, microcontroller, source_str)
    
    def _generate_openai_answer(self, question: str, relevant_docs: List[Tuple[Document, float]], 
                               microcontroller: str, source_str: str) -> str:
        """OpenAI APIを使用した高品質回答生成"""
        
        # コンテキストを構築
        context_parts = []
        for doc, score in relevant_docs[:5]:  # 上位5件のドキュメントを使用
            context_parts.append(f"文書: {doc.metadata.get('filename', '不明')}")
            context_parts.append(f"内容: {doc.page_content[:800]}")  # 長すぎるコンテンツを制限
            context_parts.append("---")
        
        context = "\n".join(context_parts)
        
        # プロンプトを構築
        system_prompt = f"""あなたはSTマイクロエレクトロニクスのマイコン専門アシスタントです。
マイコン初心者にも分かりやすく、丁寧に日本語で回答してください。

回答する際は以下の点を心がけてください：
1. 技術用語は初心者にも分かるよう解説を含める
2. 具体的なサンプルコードを提供する場合は、コメントを充実させる
3. CubeMXの使用方法は段階的に説明する
4. 安全性やベストプラクティスも含める
5. 回答の最後に参考ドキュメントを記載する

対象マイコン: {microcontroller}
参考ドキュメント: {source_str}"""

        user_prompt = f"""以下のコンテキスト情報を参考にして、質問に答えてください。

【コンテキスト情報】
{context}

【質問】
{question}

マイコン初心者にも分かりやすく、実用的で詳しい回答をお願いします。"""

        try:
            response = self.openai_client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated answer using OpenAI API")
            return answer
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_template_answer(self, question: str, relevant_docs: List[Tuple[Document, float]], 
                                 microcontroller: str, source_str: str) -> str:
        """テンプレートベース回答生成（フォールバック）"""
        question_lower = question.lower()
        
        # 適切なテンプレートを選択
        for category, template_info in self.answer_templates.items():
            if any(keyword in question_lower for keyword in template_info["keywords"]):
                return template_info["template"].format(
                    microcontroller=microcontroller,
                    sources=source_str
                )
        
        # 関連コンテンツから抜粋
        if relevant_docs:
            context_preview = relevant_docs[0][0].page_content[:300] + "..."
            return f"""
{microcontroller}に関する情報を見つけました。

**関連情報の抜粋：**
{context_preview}

**参考ドキュメント：** {source_str}

より詳細な情報については、上記のドキュメントをご参照ください。
            """
        
        # デフォルト回答
        return self.answer_templates["general"]["template"].format(
            microcontroller=microcontroller,
            sources=source_str
        )
    
    def generate_code(self, 
                     request: str, 
                     microcontroller: str = "NUCLEO-F767ZI",
                     num_docs: int = 3) -> Dict:
        """サンプルコード生成（OpenAI API使用可能時はより高品質なコードを生成）"""
        try:
            # 1. コード生成に関連するドキュメントを検索
            search_query = f"{request} サンプルコード プログラム 実装"
            relevant_docs = self.vector_db.search_similar_documents(
                query=search_query,
                k=num_docs,
                microcontroller=microcontroller,
                score_threshold=0.05
            )
            
            # 2. ソース情報の収集
            sources = self._extract_sources(relevant_docs)
            
            # 3. コード生成（OpenAI APIまたはテンプレート）
            if self.use_openai and self.openai_client and relevant_docs:
                try:
                    result = self._generate_openai_code(request, relevant_docs, microcontroller)
                    result["sources"] = sources
                    return result
                except Exception as e:
                    logger.error(f"OpenAI code generation failed: {e}")
                    logger.info("Falling back to template-based code generation")
            
            # フォールバック：テンプレートベースコード生成
            code = self._generate_code_template(request, microcontroller)
            
            return {
                "code": code,
                "explanation": f"{microcontroller}用の{request}に関するサンプルコードです。\\nCubeMXでの初期設定が必要です。",
                "sources": sources,
                "microcontroller": microcontroller
            }
            
        except Exception as e:
            logger.error(f"Failed to generate code: {e}")
            return {
                "code": f"// エラーが発生しました: {str(e)}",
                "explanation": "コード生成に失敗しました",
                "sources": [],
                "microcontroller": microcontroller
            }
    
    def _generate_openai_code(self, request: str, relevant_docs: List[Tuple[Document, float]], 
                             microcontroller: str) -> Dict:
        """OpenAI APIを使用した高品質コード生成"""
        
        # コンテキストを構築
        context_parts = []
        for doc, score in relevant_docs[:3]:  # 上位3件のドキュメントを使用
            context_parts.append(f"参考文書: {doc.metadata.get('filename', '不明')}")
            context_parts.append(f"内容: {doc.page_content[:600]}")
            context_parts.append("---")
        
        context = "\n".join(context_parts)
        
        # コード生成用プロンプト
        system_prompt = f"""あなたはSTマイクロエレクトロニクスのマイコン開発専門エンジニアです。
{microcontroller}向けの実用的なサンプルコードを生成してください。

コード生成時の要件：
1. HALライブラリを使用する
2. 初心者にも分かりやすいコメントを充実させる
3. エラーハンドリングを含める
4. CubeMXで生成される構造に準拠する
5. 安全性とベストプラクティスを考慮する
6. 実際に動作する完全なコードを提供する

出力形式：
- 詳細なコメント付きのCコード
- 必要な初期設定の説明
- 使用方法の説明"""

        user_prompt = f"""以下の要求に基づいて、{microcontroller}用のサンプルコードを生成してください。

【要求内容】
{request}

【参考情報】
{context}

初心者にも分かりやすく、実際に動作する完全なコードを提供してください。
コードには詳細なコメントを含め、CubeMXでの設定が必要な部分も説明してください。"""

        try:
            response = self.openai_client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # コード生成では低めの温度を使用
                max_tokens=Config.MAX_TOKENS
            )
            
            full_response = response.choices[0].message.content
            
            # レスポンスからコードと説明を分離（簡易的な方法）
            if "```c" in full_response or "```" in full_response:
                parts = full_response.split("```")
                if len(parts) >= 3:
                    code = parts[1].replace("c\n", "").strip()
                    explanation = (parts[0] + parts[2]).strip()
                else:
                    code = full_response
                    explanation = f"{microcontroller}用の{request}に関するサンプルコードです。"
            else:
                code = full_response
                explanation = f"{microcontroller}用の{request}に関するサンプルコードです。"
            
            logger.info("Generated code using OpenAI API")
            return {
                "code": code,
                "explanation": explanation,
                "microcontroller": microcontroller
            }
            
        except Exception as e:
            logger.error(f"OpenAI code generation error: {e}")
            raise
    
    def _generate_code_template(self, request: str, microcontroller: str) -> str:
        """コードテンプレート生成"""
        request_lower = request.lower()
        
        # リクエストタイプを判定
        for code_type, template in self.code_templates.items():
            if code_type in request_lower:
                return template.format(microcontroller=microcontroller)
        
        # デフォルトコード
        return f"""// {microcontroller} {request}サンプル
#include "main.h"

void {request.replace(' ', '_')}_Example(void)
{{
    // TODO: {request}の実装をここに記述
    
    // 基本的な初期化
    HAL_Init();
    SystemClock_Config();
    
    // GPIO、Timer、UART等の初期化（CubeMXで生成）
    // MX_GPIO_Init();
    // MX_TIM_Init();
    // MX_UART_Init();
    
    while (1)
    {{
        // メインループ処理
        // {request}の具体的な処理をここに実装
        
        HAL_Delay(100);
    }}
}}

/*
使用方法:
1. STM32CubeMXで{microcontroller}プロジェクトを作成
2. 必要なペリフェラルを設定
3. 上記コードを統合
4. ビルド・書き込み
*/"""
    
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
                category=category,
                score_threshold=0.05
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
                microcontroller=microcontroller,
                score_threshold=0.05
            )
            
            # ソース情報
            sources = self._extract_sources(relevant_docs)
            
            # 追加の詳細情報
            detailed_info = f"""
{microcontroller}の詳細情報:

**基本仕様:**
- プロセッサコア: {mc_info.get('core', 'ARM Cortex-M7')}
- 動作周波数: {mc_info.get('frequency', '216 MHz')}
- フラッシュメモリ: {mc_info.get('flash', '2 MB')}
- RAM: {mc_info.get('ram', '512 KB')}

**主な特徴:**
- 高性能32ビットマイクロコントローラ
- 豊富なペリフェラル搭載
- 低消費電力設計
- デバッグ機能充実

**対応開発環境:**
- STM32CubeIDE
- STM32CubeMX
- Keil MDK-ARM
- IAR Embedded Workbench

**主要ペリフェラル:**
- GPIO（汎用入出力）
- Timer/PWM
- UART/USART（シリアル通信）
- SPI（シリアルペリフェラルインターフェース）
- I2C（Inter-Integrated Circuit）
- ADC（アナログ-デジタル変換器）
- DAC（デジタル-アナログ変換器）
- USB（ユニバーサルシリアルバス）
            """
            
            return {
                "info": detailed_info,
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
            "llm_available": self.use_openai and self.openai_client is not None,
            "vector_db_available": self.vector_db is not None,
            "supported_microcontrollers": list(Config.SUPPORTED_MICROCONTROLLERS.keys()),
            "vector_db_collections": self.vector_db.list_collections() if self.vector_db else [],
            "embedding_model": "TF-IDF (Simple)",
            "llm_model": Config.LLM_MODEL if self.use_openai else "Template-based (Offline)",
            "total_documents": len(self.vector_db.documents) if self.vector_db else 0,
            "openai_available": OPENAI_AVAILABLE,
            "openai_configured": bool(Config.get_openai_api_key()),
            "mode": "OpenAI + Template Fallback" if self.use_openai else "Template-only"
        }