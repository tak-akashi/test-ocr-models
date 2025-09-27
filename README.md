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

### 実行環境

- **ネイティブ環境** - uvパッケージマネージャーを使用した従来の方法
- **Docker環境** - Windows/WSL2/Linux対応のコンテナ化環境（推奨）

### 🚀 クイックスタート（Docker）

```bash
# 1. リポジトリをクローン
git clone <repository-url> && cd test

# 2. 環境設定
cp .env.example .env  # APIキーを設定

# 3. bashに入って作業開始
docker-compose run --rm document-processor bash

# 4. コンテナ内でスクリプト実行
python src/run_baseline.py        # 全モデル実行
python src/run_qwen.py            # Qwenモデルのみ
python src/run_preprocessing.py   # 前処理ツール
```

## 🚀 セットアップ

### 必要要件

#### ネイティブ環境
- Python 3.12
- uv (Pythonパッケージマネージャー)
- 各APIサービスのアカウントとAPIキー

#### Docker環境（推奨：Windows/WSL2/Linux）
- Docker Desktop または Docker Engine
- Docker Compose
- NVIDIA Docker（GPU処理を使用する場合）

### インストール

#### ネイティブ環境でのセットアップ

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

#### Docker環境でのセットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd test
```

2. キャッシュディレクトリを作成
```bash
mkdir -p .cache/huggingface .cache/huggingface-gpu
```

3. 環境変数を設定（`.env`ファイルを作成）
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

4. Dockerコンテナの使用開始

**方法1: 直接bashに入って作業（推奨）**
```bash
# CPU処理用 - bashに直接入る
docker-compose run --rm document-processor bash

# GPU処理用 - bashに直接入る
docker-compose run --rm --gpus all document-processor-gpu bash
```

**方法2: サービスとして起動**
```bash
# CPU処理用（バックグラウンド起動）
docker-compose up -d

# GPU処理用（NVIDIA Docker必須）
docker-compose --profile gpu up -d document-processor-gpu

# Jupyter Lab開発環境
docker-compose --profile jupyter up -d jupyter
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

**ネイティブ環境:**
```bash
# プロジェクトルートから実行（推奨）
uv run python run_preprocessing.py extract input.pdf --pages 1 2 3 --output-dir output/
# または
uv run python src/run_preprocessing.py extract input.pdf --pages 1 2 3 --output-dir output/
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_preprocessing.py extract input.pdf --pages 1 2 3

# 方法2: 一回限りの実行
docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor preprocessing extract input.pdf --pages 1 2 3
```

#### PDFを個別ページに分割

**ネイティブ環境:**
```bash
uv run python run_preprocessing.py split input.pdf --output-dir output/
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_preprocessing.py split input.pdf

# 方法2: 一回限りの実行
docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor preprocessing split input.pdf
```

#### PDFを画像に変換

**ネイティブ環境:**
```bash
uv run python run_preprocessing.py images input.pdf --dpi-scale 2.0
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_preprocessing.py images input.pdf --dpi-scale 2.0

# 方法2: 一回限りの実行
docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor preprocessing images input.pdf --dpi-scale 2.0
```

#### 複数PDFのバッチ処理

**ネイティブ環境:**
```bash
uv run python run_preprocessing.py batch data/ --operation split --output-dir output/
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_preprocessing.py batch data/ --operation split

# 方法2: 一回限りの実行
docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor preprocessing batch data/ --operation split
```

### ドキュメント処理テスト

#### 全モデルでテストを実行（タイミング計測付き）

**ネイティブ環境:**
```bash
# プロジェクトルートから実行（推奨）
uv run python run_baseline.py data/*.pdf --timing
# または
uv run python src/run_baseline.py data/*.pdf --timing
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_baseline.py

# 方法2: サービス経由で実行
docker-compose up -d
docker-compose exec document-processor python src/run_baseline.py

# 方法3: 一回限りの実行
docker run --rm -v ./data:/app/data:ro -v ./output:/app/output --env-file .env document-processor baseline
```

#### Qwenモデルのみ実行（GPU推奨）

**ネイティブ環境:**
```bash
uv run python run_baseline.py data/*.pdf --qwen-only --timing
```

**Docker環境:**
```bash
# 方法1: GPU対応bashに入って直接実行（推奨）
docker-compose run --rm --gpus all document-processor-gpu bash
# コンテナ内で実行:
python src/run_qwen.py

# 方法2: GPU対応サービス経由で実行
docker-compose --profile gpu up -d document-processor-gpu
docker-compose exec document-processor-gpu python src/run_qwen.py

# 方法3: 一回限りの実行
docker run --rm --gpus all -v ./data:/app/data:ro -v ./output:/app/output --env-file .env document-processor-gpu qwen
```

#### 最適化を適用して実行

**ネイティブ環境:**
```bash
uv run python run_baseline.py data/*.pdf --optimize --timing
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_baseline.py --optimize

# 方法2: 一回限りの実行
docker run --rm -v ./data:/app/data:ro -v ./output:/app/output --env-file .env document-processor baseline --optimize
```

#### カスタム出力ディレクトリを指定

**ネイティブ環境:**
```bash
uv run python run_baseline.py data/*.pdf --output-dir custom_output/ --timing
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
python src/run_baseline.py --output-dir custom_output/

# 方法2: 一回限りの実行（カスタム出力先）
docker run --rm -v ./data:/app/data:ro -v ./custom_output:/app/output --env-file .env document-processor baseline
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

## 🐳 Docker使用方法

### 推奨ワークフロー

#### インタラクティブ開発（推奨）

**基本的な使用方法:**
```bash
# bashに直接入って作業開始
docker-compose run --rm document-processor bash

# コンテナ内で複数のコマンドを連続実行
python src/run_baseline.py
python src/run_qwen.py
python src/run_preprocessing.py extract sample.pdf --pages 1 2 3

# 作業終了時は exit で自動クリーンアップ
exit
```

**GPU使用時:**
```bash
# GPU対応環境で作業
docker-compose run --rm --gpus all document-processor-gpu bash

# コンテナ内でGPU対応処理を実行
python src/run_qwen.py
```

### Docker Composeコマンド

#### サービス管理（バックグラウンド起動）
```bash
# CPU処理用コンテナを起動
docker-compose up -d document-processor

# GPU処理用コンテナを起動（NVIDIA Docker必須）
docker-compose --profile gpu up -d document-processor-gpu

# Jupyter Lab開発環境を起動
docker-compose --profile jupyter up -d jupyter

# ログを確認
docker-compose logs -f document-processor

# コンテナ内でコマンドを実行
docker-compose exec document-processor bash

# コンテナを停止・削除
docker-compose down

# ボリュームも含めて削除
docker-compose down --volumes
```

#### 直接Dockerコマンドの使い分け

**インタラクティブ開発:**
```bash
# 推奨：docker-composeを使用
docker-compose run --rm document-processor bash

# または直接docker指定
docker run --rm -it -v ./data:/app/data -v ./output:/app/output --env-file .env document-processor bash
```

**一回限りの実行:**
```bash
# 特定コマンドのみ実行
docker run --rm -v ./data:/app/data -v ./output:/app/output --env-file .env document-processor baseline

# Jupyter Labを起動（http://localhost:8888でアクセス）
docker run --rm -p 8888:8888 -v ./notebook:/app/notebook -v ./data:/app/data document-processor jupyter

# ヘルプを表示
docker run --rm document-processor help
```

### プラットフォーム別セットアップ

#### Windows（WSL2必須）
```bash
# 1. Docker Desktop for WindowsをWSL2バックエンドでインストール
# 2. Docker DesktopでWSL2統合を有効化
# 3. WSL2環境でリポジトリをクローン

mkdir -p .cache/huggingface .cache/huggingface-gpu
docker-compose build
docker-compose up -d document-processor
```

#### Linux（ネイティブDocker）
```bash
# Docker と Docker Compose をインストール
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# GPU対応（NVIDIA）の場合
# NVIDIA Container Toolkitをインストール
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# セットアップ
mkdir -p .cache/huggingface .cache/huggingface-gpu
docker-compose build
docker-compose up -d document-processor
```

#### macOS（Docker Desktop）
```bash
# 1. Docker Desktop for Macをインストール
# 2. Apple Silicon (M1/M2) の場合、マルチアーキテクチャ対応を確認

mkdir -p .cache/huggingface .cache/huggingface-gpu
docker-compose build
docker-compose up -d document-processor  # CPU処理のみ（GPUサポートなし）
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

### Docker固有の問題

#### 4. 権限エラー（Permission denied）
```
docker: Error response from daemon: failed to create task for container
```
→ マウントディレクトリの権限を確認してください
```bash
sudo chown -R $USER:$USER ./data ./output ./.cache
```

#### 5. GPU認識エラー
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```
→ NVIDIA Dockerのインストールを確認してください
```bash
# GPU動作確認
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

#### 6. メモリ不足（Dockerコンテナ）
```
docker: Error response from daemon: container killed due to memory limit
```
→ Docker Desktopのメモリ制限を増やすか、軽量なモデルを使用してください

#### 7. Windowsでパスエラー
```
docker: invalid reference format: repository name must be lowercase
```
→ WSL2環境を使用し、Windowsドライブレターを避けてください

#### 8. 日時フォルダがUTC時間で作成される
```
出力フォルダ名: 20250126-0500 (UTC時間)
期待する名前: 20250126-1400 (日本時間)
```
→ Docker環境では自動的に `TZ=Asia/Tokyo` が設定済みです。問題が続く場合はコンテナを再ビルドしてください
```bash
docker-compose build --no-cache
```

## 📝 開発コマンド

### テストの実行

**ネイティブ環境:**
```bash
uv run pytest tests/
```

**Docker環境:**
```bash
# 方法1: bashに入って直接実行（推奨）
docker-compose run --rm document-processor bash
# コンテナ内で実行:
pytest tests/

# 方法2: サービス経由で実行
docker-compose up -d
docker-compose exec document-processor pytest tests/

# 方法3: 一回限りの実行
docker run --rm -v .:/app document-processor pytest tests/
```

### Jupyterノートブックの起動

**ネイティブ環境:**
```bash
uv run jupyter lab
```

**Docker環境:**
```bash
# 方法1: bashに入ってJupyterを起動
docker-compose run --rm -p 8888:8888 document-processor bash
# コンテナ内で実行:
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
# ブラウザで http://localhost:8888 にアクセス

# 方法2: Jupyter専用サービスを起動（推奨）
docker-compose --profile jupyter up -d jupyter
# ブラウザで http://localhost:8890 にアクセス

# 方法3: 直接実行
docker run --rm -p 8888:8888 -v ./notebook:/app/notebook -v ./data:/app/data document-processor jupyter
# ブラウザで http://localhost:8888 にアクセス
```

### 依存関係の更新

**ネイティブ環境:**
```bash
uv sync
```

**Docker環境:**
```bash
# Dockerイメージを再ビルド
docker-compose build --no-cache
```

