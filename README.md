# ドキュメント処理・OCR比較プロジェクト

複数のドキュメント処理APIとOCRモデルを比較・評価するPythonプロジェクトです。

## 📋 概要

このプロジェクトは、PDFドキュメントを様々なAPIやモデルで処理し、その精度と処理速度を比較するためのツールセットを提供します。

### 対応サービス

- **Upstage Document Parse** - 高精度なドキュメント解析API
- **Azure Document Intelligence** - Microsoftのドキュメント処理サービス
- **YOMITOKU** - 日本語OCRライブラリ
- **Gemini 2.5 Flash** - GoogleのマルチモーダルAI
- **Qwen2.5-VL** - Vision-Language統合モデル

## 🚀 セットアップ

### 必要要件

- Python 3.12
- uv (Pythonパッケージマネージャー)
- 各APIサービスのアカウントとAPIキー

### インストール

1. リポジトリをクローン
```bash
git clone <repository-url>
cd test
```

2. uvを使用して依存関係をインストール
```bash
uv sync
```

3. 環境変数を設定（`.env`ファイルを作成）
```bash
cp .env.example .env
# .envファイルを編集して以下のAPIキーを設定
```

### 必要な環境変数

`.env`ファイルに以下の環境変数を設定してください：

```env
# Upstage API
UPSTAGE_API_KEY=your_upstage_api_key

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_endpoint
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_azure_api_key

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key
```

## 📁 プロジェクト構成

```
src/
├── __init__.py
├── preprocessing.py              # PDF前処理機能
├── run_baseline.py              # ベースラインテスト実行スクリプト
├── run_preprocessing.py         # 前処理実行スクリプト
├── models/                      # 各モデルの実装
│   ├── upstage.py              # Upstage Document Parse
│   ├── azure_di.py             # Azure Document Intelligence
│   ├── yomitoku.py             # YOMITOKU OCR
│   ├── gemini.py               # Gemini 2.5 Flash
│   └── qwen.py                 # Qwen VLモデル
└── utils/                       # ユーティリティ関数
    ├── html_utils.py           # HTML正規化
    ├── timing.py               # 実行時間計測
    └── file_utils.py           # ファイルI/O

data/                            # テスト用PDFファイル
output/                          # 処理結果の出力先
notebook/                        # オリジナルのJupyterノートブック
```

## 💻 使用方法

### PDF前処理

#### 特定ページの抽出
```bash
uv run python src/run_preprocessing.py extract input.pdf --pages 1 2 3 --output-dir output/
```

#### PDFを個別ページに分割
```bash
uv run python src/run_preprocessing.py split input.pdf --output-dir output/
```

#### PDFを画像に変換
```bash
uv run python src/run_preprocessing.py images input.pdf --dpi-scale 2.0
```

#### 複数PDFのバッチ処理
```bash
uv run python src/run_preprocessing.py batch data/ --operation split --output-dir output/
```

### ドキュメント処理テスト

#### 全モデルでテストを実行（タイミング計測付き）
```bash
uv run python src/run_baseline.py data/*.pdf --timing
```

#### Qwenモデルのみ実行
```bash
uv run python src/run_baseline.py data/*.pdf --qwen-only --timing
```

#### 最適化を適用して実行
```bash
uv run python src/run_baseline.py data/*.pdf --optimize --timing
```

#### カスタム出力ディレクトリを指定
```bash
uv run python src/run_baseline.py data/*.pdf --output-dir custom_output/ --timing
```

### プログラムからの使用

```python
from src.models.upstage import run_upstage
from src.models.gemini import run_gemini
from src.preprocessing import extract_pages, split_pdf_pages

# ページを抽出
extracted_pdf = extract_pages("input.pdf", [1, 2, 3])

# Upstageでドキュメントを処理
result = run_upstage("document.pdf", save=True)

# Geminiでドキュメントを処理
result = run_gemini("document.pdf", save=True)
```

## 📊 出力形式

### タイムスタンプベースの出力構造

```
output/
├── 20250126-1430/              # 実行日時フォルダ
│   ├── upstage/                # Upstage処理結果
│   ├── azure/                  # Azure処理結果
│   ├── yomitoku/               # YOMITOKU処理結果
│   ├── gemini/                 # Gemini処理結果
│   ├── qwen25vl/               # Qwen2.5VL処理結果
│   └── timing_results/         # タイミング計測結果
│       └── timing_results_20250126_143000.json
```

### タイミング結果のJSON形式

```json
{
  "timestamp": "2025-01-26T14:30:00",
  "total_files": 10,
  "results": [
    {
      "file_path": "data/sample.pdf",
      "file_name": "sample.pdf",
      "models": {
        "upstage": {
          "status": "success",
          "execution_time": 2.5
        },
        "azure": {
          "status": "success",
          "execution_time": 3.2
        }
      }
    }
  ]
}
```

## 🛠️ 主要な機能

### 前処理機能

- **extract_pages()**: PDFから特定ページを抽出
- **split_pdf_pages()**: PDFを個別ページファイルに分割
- **pdf_to_images()**: PDFページを画像に変換
- **display_pdf_pages()**: PDFページを表示（Jupyter環境）

### モデル実行関数

- **run_upstage()**: Upstage Document Parse APIで処理
- **run_azure_di()**: Azure Document Intelligenceで処理
- **run_yomitoku()**: YOMITOKUでOCR処理
- **run_gemini()**: Gemini 2.5 Flashで処理
- **run_qwen25vl_optimized()**: 最適化されたQwen2.5-VLで処理

### ユーティリティ関数

- **measure_time()**: 関数の実行時間を計測
- **save_timing_results()**: タイミング結果をJSON保存
- **normalize_html_content()**: HTML出力を正規化
- **save_html() / save_markdown()**: 結果を保存

## ⚡ パフォーマンス最適化

### Qwenモデルの最適化

```python
from src.models.qwen import optimize_for_speed, initialize_models

# モデルを初期化（最初に1回実行）
initialize_models()

# 速度最適化を適用
optimize_for_speed()
```

### メモリ管理

```python
from src.models.qwen import clear_model_cache

# メモリ不足時にキャッシュをクリア
clear_model_cache()
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. APIキーエラー
```
Error: 401 - Unauthorized
```
→ `.env`ファイルのAPIキーを確認してください

#### 2. メモリ不足（Qwenモデル使用時）
```
RuntimeError: CUDA out of memory
```
→ `clear_model_cache()`を実行するか、バッチサイズを減らしてください

#### 3. PDFページが見つからない
```
Warning: Page X does not exist in the document
```
→ PDFの総ページ数を確認し、正しいページ番号を指定してください

## 📝 開発コマンド

### テストの実行
```bash
uv run pytest tests/
```

### Jupyterノートブックの起動
```bash
uv run jupyter lab
```

### 依存関係の更新
```bash
uv sync
```

## 📜 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

プルリクエストや改善提案を歓迎します。大きな変更を加える前に、まずissueを作成して議論してください。

## 📧 お問い合わせ

質問や問題がある場合は、GitHubのissuesでお知らせください。
