# ドキュメント処理・OCR比較プロジェクト

複数のドキュメント処理APIとOCRモデルを比較・評価するPythonプロジェクトです。

## 概要

このプロジェクトは、PDFドキュメントを様々なAPIやモデルで処理し、その精度と処理速度を比較するためのツールセットを提供します。

### 対応サービス

- **Upstage Document Parse** - 高精度なドキュメント解析API（レイアウト解析 + OCR専用）
- **Azure Document Intelligence** - Microsoftのドキュメント処理サービス（レイアウト解析 + OCR専用）
- **YOMITOKU** - 日本語OCRライブラリ（レイアウト解析 + OCR専用）
- **Gemini 2.5 Flash** - GoogleのマルチモーダルAI（レイアウト解析 + OCR専用）
- **Claude Sonnet 4.5** - Anthropicのマルチモーダル言語モデル（レイアウト解析 + OCR専用）
- **Qwen2.5-VL** - Vision-Language統合モデル（レイアウト解析 + OCR専用）

> **Note**: すべてのモデルが、レイアウト解析モードとOCR専用モードの両方に対応しています。

## セットアップ

### 必要要件

- Python 3.12
- uv (Pythonパッケージマネージャー)
- 各APIサービスのアカウントとAPIキー

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd test-ocr-models

# 依存関係をインストール
uv sync

# 環境変数を設定
cp .env.sample .env
# .envファイルを編集してAPIキーを設定
```

### 必要な環境変数

`.env`ファイルに以下の環境変数を設定してください：

```env
UPSTAGE_API_KEY=your_upstage_api_key
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_endpoint
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_azure_api_key
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## 使用方法

### レイアウト解析

```bash
# 全モデルで実行（デフォルト: data/フォルダ内のファイル）
uv run layout --models all

# 特定のモデルを指定
uv run layout --models upstage azure yomitoku

# カスタム入力ディレクトリを指定
uv run layout --input custom_data/

# 特定のファイルを指定
uv run layout --input document.pdf --models upstage

# Qwen最適化オプション付き
uv run layout --models qwen --optimize
```

### OCR専用モード

```bash
# 全モデルで実行
uv run ocr --models all

# 特定のモデルを指定
uv run ocr --models upstage azure

# Qwen最適化オプション付き
uv run ocr --models qwen --optimize
```

### PDF前処理

```bash
# 特定ページの抽出
uv run preprocess extract input.pdf --pages 1 2 3

# PDFを個別ページに分割
uv run preprocess split input.pdf

# PDFを画像に変換
uv run preprocess images input.pdf --dpi-scale 2.0
```

### レガシーコマンド（後方互換）

```bash
# 全モデルバリアント指定（レイアウト + OCR）
uv run python -m src.run_models --models all

# 個別指定
uv run python -m src.run_models --models upstage upstage-ocr azure azure-ocr
```

### 利用可能なモデルキー

| モード | キー |
|--------|------|
| レイアウト解析 | `upstage`, `azure`, `yomitoku`, `gemini`, `claude`, `qwen` |
| OCR専用 | `upstage-ocr`, `azure-ocr`, `yomitoku-ocr`, `gemini-ocr`, `claude-ocr`, `qwen-ocr` |
| 全モデル | `all` (12種類すべて実行) |

## プログラムからの使用

```python
from pathlib import Path

# レイアウト解析モデル
from src.models.upstage import process_document_layout as upstage_layout
from src.models.azure import process_document_layout as azure_layout
from src.models.yomitoku import process_document_layout as yomitoku_layout
from src.models.gemini import process_document_layout as gemini_layout
from src.models.claude import process_document_layout as claude_layout
from src.models.qwen import process_document_layout as qwen_layout

# OCR専用モデル
from src.models.upstage import process_document_ocr as upstage_ocr
from src.models.azure import process_document_ocr as azure_ocr
from src.models.yomitoku import process_document_ocr as yomitoku_ocr
from src.models.gemini import process_document_ocr as gemini_ocr
from src.models.claude import process_document_ocr as claude_ocr
from src.models.qwen import process_document_ocr as qwen_ocr

# Qwenユーティリティ
from src.models.qwen import (
    initialize_models,
    optimize_for_speed,
    clear_model_cache,
    download_models,
    get_model_info
)

# 前処理
from src.preprocessing import extract_pages, split_pdf_pages

# 使用例
result = upstage_layout(Path("document.pdf"), output_dir=Path("output/upstage"), save=True)
result = upstage_ocr(Path("document.pdf"), output_dir=Path("output/upstage-ocr"), save=True)
```

## 出力形式

### タイムスタンプベースの出力構造

```
output/
└── YYYYMMDD-HHMM/
    ├── upstage/           # レイアウト解析結果
    ├── upstage-ocr/       # OCR専用結果
    ├── azure/
    ├── azure-ocr/
    ├── yomitoku/
    ├── yomitoku-ocr/
    ├── gemini/
    ├── gemini-ocr/
    ├── claude/
    ├── claude-ocr/
    ├── qwen25vl/
    ├── qwen25vl-ocr/
    └── timing_results/    # 実行時間JSON
```

### 各モデルの出力形式

| モデル | レイアウト解析 | OCR専用 |
|--------|---------------|---------|
| Upstage | HTML/Markdown（構造付き） | HTML/Markdown（テキスト中心） |
| Azure | Markdown（表、段落、レイアウト） | Markdown（テキスト抽出のみ） |
| YOMITOKU | HTML + OCR/レイアウト可視化 | JSON + OCR可視化 |
| Gemini/Claude/Qwen | Markdown（表、マルチカラム、チャート） | Markdown（読み順テキスト） |

## プロジェクト構成

```
src/
├── run_models.py           # 統合モデル実行スクリプト
├── run_preprocessing.py    # 前処理実行スクリプト
├── preprocessing.py        # PDF前処理機能
├── models/                 # 各モデルの実装
│   ├── upstage/           # layout.py, ocr.py
│   ├── azure/             # layout.py, ocr.py
│   ├── yomitoku/          # layout.py, ocr.py
│   ├── gemini/            # layout.py, ocr.py
│   ├── claude/            # layout.py, ocr.py
│   └── qwen/              # layout.py, ocr.py, common.py
└── utils/                  # ユーティリティ関数
    ├── timing.py          # 実行時間計測
    ├── file_utils.py      # ファイルI/O
    └── html_utils.py      # HTML正規化

data/                       # テスト用PDFファイル
output/                     # 処理結果の出力先
notebook/                   # Jupyterノートブック
```

## レイアウト解析 vs OCR専用モード

### レイアウト解析モード
- 文書の構造（見出し、段落、表、リストなど）を解析
- テキストの読み順や階層構造を保持
- より複雑な処理で実行時間が長め

### OCR専用モード
- テキストの抽出に特化
- レイアウト情報は最小限
- より高速な処理

### 各サービスの実装

| サービス | レイアウト解析 | OCR専用 |
|----------|---------------|---------|
| Upstage | `ocr="auto"` | `ocr="force"` |
| Azure | `prebuilt-layout` | `prebuilt-read` |
| YOMITOKU | `DocumentAnalyzer` | `OCR` クラス |
| Gemini/Claude/Qwen | 詳細レイアウトプロンプト | 簡略化OCRプロンプト |

## Qwenモデルの最適化

```python
from src.models.qwen import initialize_models, optimize_for_speed, clear_model_cache

# モデルを初期化（最初に1回実行）
initialize_models()

# 速度最適化を適用
optimize_for_speed()

# メモリ不足時にキャッシュをクリア
clear_model_cache()
```

## Docker使用方法

### セットアップ

```bash
# キャッシュディレクトリを作成
mkdir -p .cache/huggingface .cache/huggingface-gpu

# 環境変数を設定
cp .env.sample .env
```

### 実行方法

```bash
# インタラクティブモード（推奨）
docker-compose run --rm document-processor bash

# コンテナ内で実行
uv run layout --models all
uv run ocr --models upstage azure

# GPU対応環境
docker-compose run --rm --gpus all document-processor-gpu bash
```

### Docker Composeコマンド

```bash
# CPU処理用コンテナを起動
docker-compose up -d document-processor

# GPU処理用コンテナを起動（NVIDIA Docker必須）
docker-compose --profile gpu up -d document-processor-gpu

# Jupyter Lab開発環境を起動
docker-compose --profile jupyter up -d jupyter

# ログを確認
docker-compose logs -f document-processor

# コンテナを停止・削除
docker-compose down
```

## 開発

### テストの実行

```bash
uv run pytest                              # 全テスト
uv run pytest tests/test_model_imports.py  # 特定のテストファイル
uv run pytest -k "test_import_qwen"        # 単一テスト
```

### Jupyterノートブック

```bash
uv run jupyter lab
```

### 依存関係の更新

```bash
uv sync
```

## トラブルシューティング

### APIキーエラー
```
Error: 401 - Unauthorized
```
→ `.env`ファイルのAPIキーを確認してください

### メモリ不足（Qwenモデル使用時）
```
RuntimeError: CUDA out of memory
```
→ `clear_model_cache()`を実行するか、バッチサイズを減らしてください

### 権限エラー（Docker）
```bash
sudo chown -R $USER:$USER ./data ./output ./.cache
```

### GPU認識エラー（Docker）
```bash
# GPU動作確認
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```
