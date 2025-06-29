"""
オンライン文書ブートストラップ - STM32文書をWebから取得してインデックス化
"""
import os
import sys
import logging
import requests
from typing import List, Dict
import tempfile

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from models.simple_vector_db import SimpleVectorDatabase
from models.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OnlineDocumentBootstrap:
    """オンライン文書ブートストラップ"""
    
    def __init__(self, vector_db=None):
        self.vector_db = vector_db or SimpleVectorDatabase()
        try:
            from models.document_processor import DocumentProcessor
            self.doc_processor = DocumentProcessor()
        except:
            self.doc_processor = None
        
        # STM32基本文書のURL
        self.document_urls = {
            "STM32F7_HAL_Overview": "https://www.st.com/resource/en/user_manual/dm00189702-description-of-stm32f7-hal-and-lowlayer-drivers-stmicroelectronics.pdf",
            "NUCLEO_F767ZI_Guide": "https://www.st.com/resource/en/user_manual/dm00244518-stm32-nucleo144-boards-mb1137-stmicroelectronics.pdf",
            "STM32CubeMX_Guide": "https://www.st.com/resource/en/user_manual/dm00104712-stm32cubemx-for-stm32-configuration-and-initialization-c-code-generation-stmicroelectronics.pdf",
        }
        
        # 基本的なSTM32情報テンプレート
        self.basic_info = [
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
"""
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
"""
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
"""
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
"""
            }
        ]
    
    def bootstrap_documents(self) -> bool:
        """基本文書をブートストラップ"""
        try:
            logger.info("Starting document bootstrap...")
            
            # 基本情報をドキュメント化
            documents = []
            for info in self.basic_info:
                from langchain.schema import Document
                doc = Document(
                    page_content=info["content"],
                    metadata={
                        "title": info["title"],
                        "source": "bootstrap",
                        "type": "technical_info"
                    }
                )
                documents.append(doc)
            
            # ベクターDBに追加
            self.vector_db.add_documents(documents)
            logger.info(f"Bootstrapped {len(documents)} basic documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")
            return False
    
    def is_bootstrap_needed(self) -> bool:
        """ブートストラップが必要かチェック"""
        try:
            doc_count = len(self.vector_db.documents)
            return doc_count < 5  # 基本文書数未満の場合
        except:
            return True

def main():
    """メイン実行"""
    bootstrap = OnlineDocumentBootstrap()
    
    if bootstrap.is_bootstrap_needed():
        logger.info("Bootstrapping required documents...")
        success = bootstrap.bootstrap_documents()
        if success:
            logger.info("Bootstrap completed successfully!")
        else:
            logger.error("Bootstrap failed!")
    else:
        logger.info("Documents already available")

if __name__ == "__main__":
    main()