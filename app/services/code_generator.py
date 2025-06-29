"""
サンプルコード生成サービス
マイコン初心者向けのコード生成機能
"""
import logging
from typing import Dict, List, Optional
from enum import Enum
import re

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeType(Enum):
    """コードタイプ列挙"""
    BASIC_GPIO = "基本GPIO制御"
    LED_CONTROL = "LED制御"
    BUTTON_INPUT = "ボタン入力"
    PWM_OUTPUT = "PWM出力"
    ADC_INPUT = "ADC入力"
    UART_COMMUNICATION = "UART通信"
    I2C_COMMUNICATION = "I2C通信"
    SPI_COMMUNICATION = "SPI通信"
    TIMER_INTERRUPT = "タイマー割り込み"
    EXTERNAL_INTERRUPT = "外部割り込み"
    RTC_CONTROL = "RTC制御"
    WATCHDOG = "ウォッチドッグ"
    DMA_TRANSFER = "DMA転送"
    POWER_MANAGEMENT = "電源管理"

class CodeTemplate:
    """コードテンプレートクラス"""
    
    def __init__(self, name: str, description: str, template: str, includes: List[str], features: List[str]):
        self.name = name
        self.description = description
        self.template = template
        self.includes = includes
        self.features = features

class CodeGenerator:
    """サンプルコード生成クラス"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """コードテンプレートを読み込み"""
        templates = {}
        
        # LED制御テンプレート
        templates["LED_CONTROL"] = CodeTemplate(
            name="LED制御",
            description="基本的なLED点滅制御",
            template='''
/* USER CODE BEGIN Includes */
#include "main.h"
/* USER CODE END Includes */

/* USER CODE BEGIN PV */
// プライベート変数
/* USER CODE END PV */

/* USER CODE BEGIN PFP */
// プライベート関数プロトタイプ
void LED_Init(void);
void LED_Toggle(void);
void LED_On(void);
void LED_Off(void);
/* USER CODE END PFP */

/**
  * @brief  LED初期化関数
  * @param  None
  * @retval None
  */
void LED_Init(void)
{
    // GPIO Ports Clock Enable
    __HAL_RCC_GPIOB_CLK_ENABLE();
    
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
    // Configure GPIO pin : PB0 (Green LED)
    GPIO_InitStruct.Pin = GPIO_PIN_0;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;  // プッシュプル出力
    GPIO_InitStruct.Pull = GPIO_NOPULL;         // プルアップ・プルダウンなし
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW; // 低速
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
    
    // 初期状態でLEDを消灯
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
}

/**
  * @brief  LED点灯関数
  * @param  None
  * @retval None
  */
void LED_On(void)
{
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);
}

/**
  * @brief  LED消灯関数
  * @param  None
  * @retval None
  */
void LED_Off(void)
{
    HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
}

/**
  * @brief  LEDトグル関数
  * @param  None
  * @retval None
  */
void LED_Toggle(void)
{
    HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_0);
}

/**
  * @brief  メイン関数での使用例
  * @param  None
  * @retval None
  */
int main(void)
{
    /* システム初期化 */
    HAL_Init();
    SystemClock_Config();
    
    /* LED初期化 */
    LED_Init();
    
    /* メインループ */
    while (1)
    {
        LED_Toggle();        // LED状態を反転
        HAL_Delay(500);      // 500ms待機
    }
}
''',
            includes=["main.h", "stm32f7xx_hal.h"],
            features=["GPIO制御", "基本的なLED操作"]
        )
        
        # ボタン入力テンプレート
        templates["BUTTON_INPUT"] = CodeTemplate(
            name="ボタン入力",
            description="ボタン入力の読み取りとデバウンス処理",
            template='''
/* USER CODE BEGIN Includes */
#include "main.h"
/* USER CODE END Includes */

/* USER CODE BEGIN PV */
// プライベート変数
static uint32_t button_last_press_time = 0;
static uint8_t button_state = 0;
/* USER CODE END PV */

/* USER CODE BEGIN PFP */
// プライベート関数プロトタイプ
void Button_Init(void);
uint8_t Button_Read(void);
uint8_t Button_IsPressed(void);
/* USER CODE END PFP */

/**
  * @brief  ボタン初期化関数
  * @param  None
  * @retval None
  */
void Button_Init(void)
{
    // GPIO Ports Clock Enable
    __HAL_RCC_GPIOC_CLK_ENABLE();
    
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
    // Configure GPIO pin : PC13 (User Button)
    GPIO_InitStruct.Pin = GPIO_PIN_13;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;      // 入力モード
    GPIO_InitStruct.Pull = GPIO_NOPULL;          // 外部プルアップ使用
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);
}

/**
  * @brief  ボタン状態読み取り関数（デバウンス処理付き）
  * @param  None
  * @retval ボタン状態 (1: 押下, 0: 非押下)
  */
uint8_t Button_Read(void)
{
    static uint8_t button_prev_state = 1;  // 前回の状態（非押下）
    uint8_t button_current_state;
    
    // 現在のボタン状態を読み取り（押下時は0、非押下時は1）
    button_current_state = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
    
    // デバウンス処理：前回と状態が変わった場合のみ判定
    if (button_prev_state != button_current_state)
    {
        HAL_Delay(50);  // デバウンス待機時間
        button_current_state = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_13);
        
        if (button_prev_state != button_current_state)
        {
            button_prev_state = button_current_state;
            return !button_current_state;  // 押下時に1を返す
        }
    }
    
    return 0;  // 状態変化なし
}

/**
  * @brief  ボタン押下検出関数
  * @param  None
  * @retval ボタン押下状態 (1: 新しい押下, 0: 押下なし)
  */
uint8_t Button_IsPressed(void)
{
    uint32_t current_time = HAL_GetTick();
    
    // チャタリング防止（最小間隔: 200ms）
    if ((current_time - button_last_press_time) < 200)
    {
        return 0;
    }
    
    if (Button_Read())
    {
        button_last_press_time = current_time;
        return 1;
    }
    
    return 0;
}

/**
  * @brief  メイン関数での使用例
  * @param  None
  * @retval None
  */
int main(void)
{
    /* システム初期化 */
    HAL_Init();
    SystemClock_Config();
    
    /* GPIO初期化 */
    Button_Init();
    LED_Init();  // LED初期化も必要
    
    /* メインループ */
    while (1)
    {
        if (Button_IsPressed())
        {
            LED_Toggle();  // ボタンが押されたらLEDを反転
        }
        
        HAL_Delay(10);  // メインループの周期
    }
}
''',
            includes=["main.h", "stm32f7xx_hal.h"],
            features=["GPIO入力", "デバウンス処理", "ボタン読み取り"]
        )
        
        # PWM出力テンプレート
        templates["PWM_OUTPUT"] = CodeTemplate(
            name="PWM出力",
            description="PWM信号生成とデューティ比制御",
            template='''
/* USER CODE BEGIN Includes */
#include "main.h"
/* USER CODE END Includes */

/* USER CODE BEGIN PV */
// プライベート変数
TIM_HandleTypeDef htim3;
uint32_t pwm_duty = 0;  // デューティ比 (0-1000)
/* USER CODE END PV */

/* USER CODE BEGIN PFP */
// プライベート関数プロトタイプ
void PWM_Init(void);
void PWM_SetDuty(uint32_t duty);
void PWM_Start(void);
void PWM_Stop(void);
/* USER CODE END PFP */

/**
  * @brief  PWM初期化関数
  * @param  None
  * @retval None
  */
void PWM_Init(void)
{
    // Timer3クロック有効化
    __HAL_RCC_TIM3_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    
    // GPIO設定 (PB4: TIM3_CH1)
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = GPIO_PIN_4;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = GPIO_AF2_TIM3;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
    
    // Timer3設定
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = 108 - 1;      // 108MHz / 108 = 1MHz
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = 1000 - 1;       // 1MHz / 1000 = 1kHz PWM
    htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&htim3);
    
    // PWMチャンネル設定
    TIM_OC_InitTypeDef sConfigOC = {0};
    sConfigOC.OCMode = TIM_OCMODE_PWM1;
    sConfigOC.Pulse = 0;                 // 初期デューティ比: 0%
    sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
    sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&htim3, &sConfigOC, TIM_CHANNEL_1);
}

/**
  * @brief  PWM開始関数
  * @param  None
  * @retval None
  */
void PWM_Start(void)
{
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
}

/**
  * @brief  PWM停止関数
  * @param  None
  * @retval None
  */
void PWM_Stop(void)
{
    HAL_TIM_PWM_Stop(&htim3, TIM_CHANNEL_1);
}

/**
  * @brief  PWMデューティ比設定関数
  * @param  duty: デューティ比 (0-1000, 0=0%, 1000=100%)
  * @retval None
  */
void PWM_SetDuty(uint32_t duty)
{
    if (duty > 1000) duty = 1000;  // 上限制限
    
    pwm_duty = duty;
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, duty);
}

/**
  * @brief  メイン関数での使用例
  * @param  None
  * @retval None
  */
int main(void)
{
    /* システム初期化 */
    HAL_Init();
    SystemClock_Config();
    
    /* PWM初期化 */
    PWM_Init();
    PWM_Start();
    
    /* メインループ */
    while (1)
    {
        // デューティ比を0%から100%まで段階的に変化
        for (uint32_t duty = 0; duty <= 1000; duty += 10)
        {
            PWM_SetDuty(duty);
            HAL_Delay(50);
        }
        
        // デューティ比を100%から0%まで段階的に変化
        for (uint32_t duty = 1000; duty > 0; duty -= 10)
        {
            PWM_SetDuty(duty);
            HAL_Delay(50);
        }
    }
}
''',
            includes=["main.h", "stm32f7xx_hal.h"],
            features=["PWM生成", "タイマー制御", "デューティ比制御"]
        )
        
        return templates
    
    def get_available_templates(self) -> List[str]:
        """利用可能なテンプレートのリストを取得"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict]:
        """テンプレート情報を取得"""
        template = self.templates.get(template_name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "includes": template.includes,
            "features": template.features
        }
    
    def generate_code_from_template(self, template_name: str, parameters: Dict = None) -> Dict:
        """テンプレートからコードを生成"""
        try:
            template = self.templates.get(template_name)
            if not template:
                return {
                    "success": False,
                    "error": f"テンプレート '{template_name}' が見つかりません",
                    "code": "",
                    "explanation": ""
                }
            
            code = template.template
            
            # パラメータ置換（将来の拡張用）
            if parameters:
                for key, value in parameters.items():
                    code = code.replace(f"{{{key}}}", str(value))
            
            return {
                "success": True,
                "code": code,
                "explanation": template.description,
                "includes": template.includes,
                "features": template.features,
                "template_name": template.name
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": "",
                "explanation": ""
            }
    
    def generate_custom_code(self, request: str, microcontroller: str = "NUCLEO-F767ZI") -> Dict:
        """カスタムコード生成（RAGエンジンと連携）"""
        # 要求を解析してテンプレートを推奨
        template_suggestions = self._analyze_request(request)
        
        return {
            "suggested_templates": template_suggestions,
            "custom_request": request,
            "microcontroller": microcontroller,
            "note": "RAGエンジンと連携してより詳細なコード生成を行います"
        }
    
    def _analyze_request(self, request: str) -> List[str]:
        """要求を解析してテンプレートを推奨"""
        request_lower = request.lower()
        suggestions = []
        
        # キーワードベースの推奨
        if any(keyword in request_lower for keyword in ["led", "点滅", "ライト"]):
            suggestions.append("LED_CONTROL")
        
        if any(keyword in request_lower for keyword in ["ボタン", "button", "スイッチ", "入力"]):
            suggestions.append("BUTTON_INPUT")
        
        if any(keyword in request_lower for keyword in ["pwm", "パルス", "デューティ"]):
            suggestions.append("PWM_OUTPUT")
        
        return suggestions[:3]  # 最大3つまで
    
    def get_code_explanation(self, code: str) -> Dict:
        """コードの解説を生成"""
        try:
            # 基本的なコード解析
            includes = re.findall(r'#include\s*[<"](.*?)[>"]', code)
            functions = re.findall(r'(?:void|int|uint\d+_t)\s+(\w+)\s*\(', code)
            
            explanation = {
                "includes": includes,
                "functions": functions,
                "complexity": "中級" if len(functions) > 5 else "初級",
                "estimated_lines": len(code.split('\n')),
                "notes": []
            }
            
            # コードの特徴を分析
            if "HAL_" in code:
                explanation["notes"].append("HAL（Hardware Abstraction Layer）を使用しています")
            
            if "GPIO" in code:
                explanation["notes"].append("GPIO（汎用入出力）制御を含んでいます")
            
            if "TIM" in code:
                explanation["notes"].append("タイマー機能を使用しています")
            
            if "interrupt" in code.lower() or "IRQ" in code:
                explanation["notes"].append("割り込み処理が含まれています")
            
            return explanation
            
        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            return {"error": str(e)}
    
    def validate_code(self, code: str, microcontroller: str = "NUCLEO-F767ZI") -> Dict:
        """コードの基本的な検証"""
        issues = []
        warnings = []
        
        # 基本的なインクルードチェック
        if "#include" not in code:
            issues.append("必要なヘッダファイルがインクルードされていません")
        
        # HAL初期化チェック
        if "HAL_Init()" not in code and "main(" in code:
            warnings.append("HAL_Init()の呼び出しが見つかりません")
        
        # クロック設定チェック
        if "SystemClock_Config()" not in code and "main(" in code:
            warnings.append("SystemClock_Config()の呼び出しが見つかりません")
        
        # GPIO設定チェック
        if "GPIO" in code and "__HAL_RCC_GPIO" not in code:
            warnings.append("GPIOクロックの有効化が見つかりません")
        
        validation_result = {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "microcontroller": microcontroller
        }
        
        return validation_result
    
    def get_code_suggestions(self, code: str) -> List[str]:
        """コード改善提案"""
        suggestions = []
        
        # エラーハンドリングの提案
        if "HAL_" in code and "!=" not in code:
            suggestions.append("HAL関数の戻り値をチェックしてエラーハンドリングを追加することを推奨します")
        
        # コメントの提案
        comment_ratio = code.count("//") / max(code.count("\n"), 1)
        if comment_ratio < 0.1:
            suggestions.append("コードの理解を助けるため、より多くのコメントを追加することを推奨します")
        
        # マジックナンバーの提案
        if re.search(r'\b\d{3,}\b', code):
            suggestions.append("マジックナンバーを定数として定義することを推奨します")
        
        return suggestions