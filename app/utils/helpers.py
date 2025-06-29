"""
ヘルパー関数とユーティリティ
"""
import os
import re
import logging
from typing import List, Dict, Optional, Any
import hashlib
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """ファイル名をサニタイズ"""
    # 不正な文字を除去
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 長すぎる場合は切り詰め
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized

def calculate_file_hash(file_path: str) -> Optional[str]:
    """ファイルのハッシュ値を計算"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    except Exception as e:
        logger.error(f"Hash calculation failed for {file_path}: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式でフォーマット"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """テキストからコードブロックを抽出"""
    code_blocks = []
    
    # マークダウン形式のコードブロック
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for language, code in matches:
        code_blocks.append({
            "language": language if language else "text",
            "code": code.strip()
        })
    
    return code_blocks

def clean_text_for_search(text: str) -> str:
    """検索用にテキストをクリーニング"""
    if not text:
        return ""
    
    # 改行とタブを空白に置換
    text = re.sub(r'[\n\t\r]', ' ', text)
    
    # 複数の空白を単一の空白に
    text = re.sub(r' +', ' ', text)
    
    # 先頭と末尾の空白を除去
    text = text.strip()
    
    return text

def parse_microcontroller_specs(spec_text: str) -> Dict[str, str]:
    """仕様テキストからマイコンスペックを抽出"""
    specs = {}
    
    # 周波数の抽出
    freq_match = re.search(r'(\d+)\s*MHz', spec_text, re.IGNORECASE)
    if freq_match:
        specs['frequency'] = f"{freq_match.group(1)} MHz"
    
    # フラッシュメモリの抽出
    flash_match = re.search(r'(\d+)\s*(KB|MB)\s*Flash', spec_text, re.IGNORECASE)
    if flash_match:
        specs['flash'] = f"{flash_match.group(1)} {flash_match.group(2)}"
    
    # RAMの抽出
    ram_match = re.search(r'(\d+)\s*(KB|MB)\s*RAM', spec_text, re.IGNORECASE)
    if ram_match:
        specs['ram'] = f"{ram_match.group(1)} {ram_match.group(2)}"
    
    return specs

def validate_microcontroller_name(name: str) -> bool:
    """マイコン名の形式をバリデート"""
    # STM32の命名規則に基づく基本的なバリデーション
    pattern = r'^(NUCLEO-|STM32)[A-Z0-9\-]+$'
    return bool(re.match(pattern, name.upper()))

def format_code_with_comments(code: str, language: str = "c") -> str:
    """コードにコメントを追加してフォーマット"""
    if not code:
        return code
    
    lines = code.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 関数定義にコメントを追加
        if re.match(r'^\w+\s+\w+\s*\(.*\)\s*{?$', stripped):
            if not any(comment in line for comment in ['//', '/*']):
                formatted_lines.append(f"    // {stripped}")
        
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def extract_include_statements(code: str) -> List[str]:
    """コードからインクルード文を抽出"""
    includes = []
    pattern = r'#include\s*[<"](.*?)[>"]'
    matches = re.findall(pattern, code)
    
    for match in matches:
        includes.append(match)
    
    return includes

def detect_microcontroller_from_text(text: str) -> Optional[str]:
    """テキストからマイコン名を検出"""
    # 一般的なマイコン名のパターン
    patterns = [
        r'NUCLEO-F\d{3}[A-Z]{2}',
        r'STM32F\d{3}[A-Z]{2}',
        r'STM32[FLH]\d{3}[A-Z]{2}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).upper()
    
    return None

def create_project_structure_info() -> Dict[str, Any]:
    """プロジェクト構造情報を作成"""
    return {
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "description": "STマイクロマイコン RAGシステム",
        "supported_microcontrollers": ["NUCLEO-F767ZI"],
        "supported_file_types": [".pdf", ".txt", ".md"],
        "features": [
            "Q&A システム",
            "サンプルコード生成",
            "ドキュメント検索",
            "マイコン情報表示"
        ]
    }

def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """JSONファイルの保存"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON save failed: {e}")
        return False

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """JSONファイルの読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"JSON load failed: {e}")
        return None

def check_system_requirements() -> Dict[str, bool]:
    """システム要件のチェック"""
    requirements = {
        "python_version": True,  # Python 3.8+を想定
        "memory_available": True,  # 4GB+を想定
        "disk_space": True,  # 1GB+を想定
        "internet_connection": True  # OpenAI API用
    }
    
    # 実際のチェックロジックはここに実装
    # 簡略版のため基本的にTrueを返す
    
    return requirements

def generate_error_report(error: Exception, context: str = "") -> Dict[str, str]:
    """エラーレポートを生成"""
    return {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "suggestions": [
            "アプリケーションを再起動してください",
            "インターネット接続を確認してください",
            "システム管理者に連絡してください"
        ]
    }

def validate_openai_api_key(api_key: str) -> bool:
    """OpenAI API keyの基本的なバリデーション"""
    if not api_key:
        return False
    
    # 基本的な形式チェック
    if not api_key.startswith('sk-'):
        return False
    
    if len(api_key) < 20:
        return False
    
    return True

def create_backup_filename(original_name: str) -> str:
    """バックアップファイル名を生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_name)
    return f"{name}_backup_{timestamp}{ext}"

def progress_callback(current: int, total: int, operation: str = "Processing"):
    """進捗コールバック関数"""
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"{operation}: {current}/{total} ({percentage:.1f}%)")

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """リストをチャンクに分割"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def merge_dictionaries(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """複数の辞書をマージ"""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result