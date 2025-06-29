"""
マイコン選択サービス
将来的な拡張を考慮したマイコン管理機能
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MicrocontrollerInfo:
    """マイコン情報データクラス"""
    name: str
    series: str
    core: str
    frequency: str
    flash: str
    ram: str
    description: str
    features: List[str] = None
    peripherals: List[str] = None
    development_boards: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.peripherals is None:
            self.peripherals = []
        if self.development_boards is None:
            self.development_boards = []

class MicrocontrollerSelector:
    """マイコン選択・管理クラス"""
    
    def __init__(self):
        self.microcontrollers = self._load_microcontrollers()
        self.current_selection = "NUCLEO-F767ZI"  # デフォルト
    
    def _load_microcontrollers(self) -> Dict[str, MicrocontrollerInfo]:
        """設定からマイコン情報を読み込み"""
        microcontrollers = {}
        
        for name, info in Config.SUPPORTED_MICROCONTROLLERS.items():
            mc_info = MicrocontrollerInfo(
                name=info["name"],
                series=info["series"],
                core=info["core"],
                frequency=info["frequency"],
                flash=info["flash"],
                ram=info["ram"],
                description=info["description"]
            )
            
            # NUCLEO-F767ZI固有の情報を追加
            if name == "NUCLEO-F767ZI":
                mc_info.features = [
                    "高性能Cortex-M7コア",
                    "FPU（浮動小数点演算ユニット）",
                    "L1キャッシュ",
                    "DSP命令",
                    "Ethernet MAC",
                    "USB OTG HS/FS",
                    "Camera interface",
                    "LCD-TFT controller",
                    "真正乱数ジェネレータ",
                    "AES、Hash（SHA/MD5）、3DES暗号化"
                ]
                
                mc_info.peripherals = [
                    "UART/USART x8",
                    "SPI x6", 
                    "I2C x4",
                    "ADC x3 (12-bit)",
                    "DAC x2 (12-bit)",
                    "Timer x17",
                    "GPIO x144",
                    "CAN x3",
                    "SDMMC x2",
                    "QSPI x1"
                ]
                
                mc_info.development_boards = [
                    "NUCLEO-F767ZI",
                    "STM32F769I-DISCO",
                    "STM32F746G-DISCO"
                ]
            
            microcontrollers[name] = mc_info
        
        return microcontrollers
    
    def get_available_microcontrollers(self) -> List[str]:
        """利用可能なマイコンのリストを取得"""
        return list(self.microcontrollers.keys())
    
    def get_microcontroller_info(self, name: str) -> Optional[MicrocontrollerInfo]:
        """指定されたマイコンの情報を取得"""
        return self.microcontrollers.get(name)
    
    def set_current_microcontroller(self, name: str) -> bool:
        """現在のマイコンを設定"""
        if name in self.microcontrollers:
            self.current_selection = name
            logger.info(f"Current microcontroller set to: {name}")
            return True
        else:
            logger.warning(f"Unknown microcontroller: {name}")
            return False
    
    def get_current_microcontroller(self) -> str:
        """現在選択されているマイコンを取得"""
        return self.current_selection
    
    def get_microcontroller_comparison(self, names: List[str]) -> Dict:
        """複数のマイコンを比較"""
        comparison = {
            "microcontrollers": [],
            "comparison_table": {}
        }
        
        valid_names = [name for name in names if name in self.microcontrollers]
        
        if not valid_names:
            return comparison
        
        # 比較項目
        comparison_items = ["series", "core", "frequency", "flash", "ram"]
        
        for item in comparison_items:
            comparison["comparison_table"][item] = {}
            for name in valid_names:
                mc_info = self.microcontrollers[name]
                comparison["comparison_table"][item][name] = getattr(mc_info, item)
        
        # 詳細情報
        for name in valid_names:
            comparison["microcontrollers"].append({
                "name": name,
                "info": self.microcontrollers[name]
            })
        
        return comparison
    
    def search_microcontrollers(self, criteria: Dict) -> List[str]:
        """条件に基づいてマイコンを検索"""
        results = []
        
        for name, mc_info in self.microcontrollers.items():
            match = True
            
            # シリーズで絞り込み
            if "series" in criteria:
                if criteria["series"].upper() not in mc_info.series.upper():
                    match = False
            
            # コアで絞り込み
            if "core" in criteria:
                if criteria["core"].upper() not in mc_info.core.upper():
                    match = False
            
            # フラッシュサイズで絞り込み（簡単な文字列比較）
            if "min_flash" in criteria:
                # より詳細な比較ロジックが必要
                pass
            
            if match:
                results.append(name)
        
        return results
    
    def get_recommended_microcontroller(self, use_case: str) -> Dict:
        """用途に基づいてマイコンを推奨"""
        recommendations = {
            "general": "NUCLEO-F767ZI",
            "iot": "NUCLEO-F767ZI", 
            "motor_control": "NUCLEO-F767ZI",
            "audio": "NUCLEO-F767ZI",
            "graphics": "NUCLEO-F767ZI",
            "security": "NUCLEO-F767ZI"
        }
        
        use_case_lower = use_case.lower()
        recommended = recommendations.get(use_case_lower, "NUCLEO-F767ZI")
        
        recommendation_info = {
            "recommended": recommended,
            "reason": self._get_recommendation_reason(use_case_lower, recommended),
            "microcontroller_info": self.microcontrollers.get(recommended)
        }
        
        return recommendation_info
    
    def _get_recommendation_reason(self, use_case: str, recommended: str) -> str:
        """推奨理由を生成"""
        reasons = {
            "general": "汎用的な開発に適した高性能マイコンです",
            "iot": "豊富な通信インターフェースとセキュリティ機能を備えています",
            "motor_control": "高精度タイマーとPWM機能を持ち、モーター制御に最適です",
            "audio": "I2S、SAI、DMA機能により高品質な音声処理が可能です",
            "graphics": "LCD-TFTコントローラーとDMA2Dを備え、グラフィックス処理に適しています",
            "security": "ハードウェア暗号化機能と真正乱数ジェネレータを内蔵しています"
        }
        
        return reasons.get(use_case, "高性能で多機能なマイコンです")
    
    def add_microcontroller(self, 
                           name: str, 
                           series: str,
                           core: str,
                           frequency: str,
                           flash: str,
                           ram: str,
                           description: str) -> bool:
        """新しいマイコンを追加（将来の拡張用）"""
        try:
            new_mc = MicrocontrollerInfo(
                name=name,
                series=series,
                core=core,
                frequency=frequency,
                flash=flash,
                ram=ram,
                description=description
            )
            
            self.microcontrollers[name] = new_mc
            logger.info(f"Added new microcontroller: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add microcontroller {name}: {e}")
            return False
    
    def remove_microcontroller(self, name: str) -> bool:
        """マイコンを削除"""
        try:
            if name in self.microcontrollers:
                del self.microcontrollers[name]
                
                # 現在の選択が削除されたマイコンの場合、デフォルトに戻す
                if self.current_selection == name:
                    self.current_selection = "NUCLEO-F767ZI"
                
                logger.info(f"Removed microcontroller: {name}")
                return True
            else:
                logger.warning(f"Microcontroller not found: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove microcontroller {name}: {e}")
            return False
    
    def export_microcontroller_data(self) -> Dict:
        """マイコンデータをエクスポート"""
        return {
            "microcontrollers": {
                name: {
                    "name": mc.name,
                    "series": mc.series,
                    "core": mc.core,
                    "frequency": mc.frequency,
                    "flash": mc.flash,
                    "ram": mc.ram,
                    "description": mc.description,
                    "features": mc.features,
                    "peripherals": mc.peripherals,
                    "development_boards": mc.development_boards
                }
                for name, mc in self.microcontrollers.items()
            },
            "current_selection": self.current_selection
        }
    
    def get_development_tips(self, microcontroller: str) -> List[str]:
        """マイコン固有の開発Tips"""
        tips = {
            "NUCLEO-F767ZI": [
                "L1キャッシュを有効にしてパフォーマンスを向上させましょう",
                "DMA使用時はキャッシュコヒーレンシーに注意してください",
                "FPUを活用して浮動小数点演算を高速化できます",
                "Ethernet機能を使用する場合は適切なPHYチップの設定が必要です",
                "USB OTG機能を使用する際は電源設定を確認してください",
                "高速クロック使用時は電源とGNDの配線に注意が必要です"
            ]
        }
        
        return tips.get(microcontroller, ["マイコン固有の情報は現在準備中です"])