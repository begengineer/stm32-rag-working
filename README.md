# STマイクロRAGシステム

STM32 NUCLEO-F767ZI開発者向けのAI支援Q&Aシステム

## 🚀 機能

- **STM32 Q&A**: マイコン開発に関する質問に詳細回答
- **サンプルコード生成**: HALライブラリを使用した実用的なコード
- **CubeMX支援**: プロジェクト作成・設定ガイド
- **Simulink対応**: モデルベース開発支援
- **技術文書検索**: 1500件以上のSTM32技術資料から検索

## 🔧 対応技術

- STM32 HALライブラリ
- STM32CubeMX
- MATLAB/Simulink
- GPIO、PWM、ADC、UART、I2C、SPI、CAN通信
- 低電力設計、セキュリティ

## 🏃‍♂️ クイックスタート

### 1. 環境構築
```bash
pip install -r requirements.txt
```

### 2. 設定
`.streamlit/secrets.toml`を作成:
```toml
[api_keys]
openai_api_key = "your_openai_api_key"

[auth]
admin_password = "your_password"
session_timeout = 3600
```

### 3. 実行
```bash
streamlit run app/main.py
```

## 🔐 セキュリティ

- パスワード認証
- セッション管理
- APIキー秘匿化
- セキュアな設定管理

## 📚 ドキュメント構成

- STM32技術資料
- Application Notes
- CubeMX文書
- Simulink統合ガイド

## 🤝 対象ユーザー

- マイコン初心者
- STM32開発者
- 学習者・研究者
- エンジニア

## 📄 ライセンス

教育・研究目的での使用を想定

---

**開発者**: AI支援開発システム  
**バージョン**: 1.0  
**最終更新**: 2024年