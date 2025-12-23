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

# 最初の10ファイルのみ処理
uv run layout --models upstage --n-samples 10
```

### OCR専用モード

```bash
# 全モデルで実行
uv run ocr --models all

# 特定のモデルを指定
uv run ocr --models upstage azure

# Qwen最適化オプション付き
uv run ocr --models qwen --optimize

# 最初の5ファイルのみ処理
uv run ocr --models upstage --n-samples 5
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

### テキスト抽出・集計

モデル出力からテキストのみを抽出し、CSV/JSON形式で保存します。

```bash
# 出力ディレクトリからテキストを集計
uv run postprocess aggregate output/20251202-0942

# または直接実行
uv run python -m src.postprocess.aggregate output/20251202-0942
```

出力ファイル:
- `{model}_texts.csv/json` - モデル別テキスト
- `combined_texts.csv/json` - 3モデル比較用統合ファイル

### 後処理・評価

OCR結果と正解データを比較し、CER（文字エラー率）を計算します。

```bash
# Upstage出力の評価
uv run postprocess upstage output/20251202-0942

# Azure出力の評価
uv run postprocess azure output/20251202-0942

# Yomitoku OCR出力の評価
uv run postprocess yomitoku-ocr output/20251202-0942

# Yomitoku Layout出力の評価
uv run postprocess yomitoku-layout output/20251202-0942

# 汎用OCR結果の評価
uv run postprocess generic ocr_results.json
```

### レガシーコマンド（後方互換）

```bash
# 全モデルバリアント指定（レイアウト + OCR）
uv run python -m src.run_models --models all

# 個別指定
uv run python -m src.run_models --models upstage upstage-ocr azure azure-ocr

# ファイル数を制限
uv run python -m src.run_models --models upstage --n-samples 10
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
from src.preprocess import extract_pages, split_pdf_pages

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
├── run_preprocessing.py    # 前処理CLI
├── run_postprocess.py      # 後処理CLI
├── models/                 # 各モデルの実装
│   ├── upstage/           # layout.py, ocr.py
│   ├── azure/             # layout.py, ocr.py
│   ├── yomitoku/          # layout.py, ocr.py
│   ├── gemini/            # layout.py, ocr.py
│   ├── claude/            # layout.py, ocr.py
│   └── qwen/              # layout.py, ocr.py, common.py
├── preprocess/             # 前処理モジュール
│   ├── pdf.py             # PDF操作（抽出、分割、画像変換）
│   ├── deskew.py          # 画像傾き補正
│   └── categorize.py      # カテゴリ別処理
├── postprocess/            # 後処理・評価モジュール
│   ├── upstage.py         # Upstage評価
│   ├── azure.py           # Azure評価
│   ├── yomitoku_ocr.py    # Yomitoku OCR評価
│   ├── yomitoku_layout.py # Yomitoku Layout評価
│   ├── generic_ocr.py     # 汎用OCR評価
│   └── aggregate.py       # テキスト集計
└── utils/                  # 汎用ユーティリティ
    ├── timing.py          # 実行時間計測
    ├── file_utils.py      # ファイルI/O
    ├── html_utils.py      # HTML正規化
    └── etl_extractor.py   # ETLデータセット抽出

scripts/                    # Dockerヘルパースクリプト
├── docker-run.ps1         # Windows PowerShell用
├── docker-run.bat         # Windows CMD用
└── docker-run.sh          # Linux/macOS用

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

**対応プラットフォーム**: Linux, macOS, Windows (CMD/PowerShell), WSL2

> **Note**: Windows (CMD/PowerShell) で Docker を使用するには、Docker Desktop for Windows と WSL2 バックエンドが必要です。

### セットアップ

```bash
# 環境変数を設定
cp .env.sample .env
# .envファイルを編集してAPIキーを設定
```

---

### Linux / macOS

```bash
# イメージをビルド
docker compose build

# インタラクティブシェル
docker compose run --rm document-processor bash

# レイアウト解析を実行
docker compose run --rm document-processor layout --models all

# OCR処理を実行
docker compose run --rm document-processor ocr --models upstage azure

# GPU対応
docker compose --profile gpu run --rm document-processor-gpu layout --models qwen --optimize

# Jupyter Lab
docker compose --profile jupyter up jupyter
```

**ヘルパースクリプト:**

```bash
# 実行権限を付与（初回のみ）
chmod +x scripts/docker-run.sh

# 使用例
./scripts/docker-run.sh layout --models all
./scripts/docker-run.sh ocr --models upstage,azure
./scripts/docker-run.sh layout --models qwen --gpu --optimize
./scripts/docker-run.sh jupyter
./scripts/docker-run.sh shell
```

---

### WSL2 (Windows Subsystem for Linux)

WSL2ターミナル内では、Linux と同じコマンドが使用できます。

```bash
# イメージをビルド
docker compose build

# レイアウト解析を実行
docker compose run --rm document-processor layout --models all

# ヘルパースクリプト使用
chmod +x scripts/docker-run.sh
./scripts/docker-run.sh layout --models all
```

**GPU使用時の注意:**
- WSL2でGPUを使用するには、Windows側にNVIDIAドライバーをインストールし、Docker DesktopでWSL2 GPUサポートを有効にする必要があります。

---

### Windows (CMD / PowerShell)

**必要要件:**
- Docker Desktop for Windows
- WSL2 バックエンドが有効（Docker Desktop設定で確認）
- （オプション）NVIDIA GPU + CUDAサポート

**ヘルパースクリプト使用（推奨）:**

```powershell
# PowerShell
.\scripts\docker-run.ps1 layout -Models all
.\scripts\docker-run.ps1 ocr -Models upstage,azure
.\scripts\docker-run.ps1 layout -Models qwen -GPU -Optimize
.\scripts\docker-run.ps1 jupyter
.\scripts\docker-run.ps1 shell
```

```cmd
# コマンドプロンプト
scripts\docker-run.bat layout all
scripts\docker-run.bat ocr upstage azure
scripts\docker-run.bat jupyter
scripts\docker-run.bat shell
```

**直接コマンド:**

```powershell
# PowerShell / CMD 共通
docker compose build
docker compose run --rm document-processor layout --models all
docker compose run --rm document-processor ocr --models upstage azure
docker compose --profile jupyter up jupyter
```

---

### Docker Compose 共通コマンド

```bash
# CPU処理用コンテナを起動
docker compose up -d document-processor

# GPU処理用コンテナを起動（NVIDIA Container Toolkit必須）
docker compose --profile gpu up -d document-processor-gpu

# Jupyter Lab開発環境を起動
docker compose --profile jupyter up -d jupyter

# ログを確認
docker compose logs -f document-processor

# コンテナを停止・削除
docker compose down
```

---

## GPU使用方法（WSL2対応）

### 前提条件

- NVIDIA GPU（CUDA対応）
- WSL2環境: Windows側にNVIDIAドライバーがインストール済み
- Docker DesktopでGPUサポートが有効

### GPU対応確認

```bash
# GPUが認識されているか確認
nvidia-smi

# DockerからGPUにアクセスできるか確認
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

### 簡易スクリプトを使用（推奨）

プロジェクトルートに`run-gpu.sh`スクリプトが用意されています。GPUが利用可能な場合は自動的にGPU版を使用し、そうでない場合はCPU版にフォールバックします。

```bash
# GPUで実行（自動検出）
./run-gpu.sh ocr --models yomitoku upstage

# レイアウト解析をGPUで実行
./run-gpu.sh layout --models qwen yomitoku azure --optimize

# すべてのモデルをGPUで実行
./run-gpu.sh ocr --models all
```

### Docker Composeで直接指定

```bash
# GPU版イメージをビルド
docker compose build document-processor-gpu

# GPU版でOCR実行（複数モデル）
docker compose --profile gpu run --rm document-processor-gpu ocr --models yomitoku upstage azure

# GPU版でレイアウト解析（最適化オプション付き）
docker compose --profile gpu run --rm document-processor-gpu layout --models qwen yomitoku --optimize

# GPU版ですべてのモデルを実行
docker compose --profile gpu run --rm document-processor-gpu layout --models all
```

### GPUを活用するモデル

| モデル | GPU活用 | 説明 |
|--------|---------|------|
| **YOMITOKU** | ✅ Yes | PyTorchベースのOCRモデル。GPUで大幅に高速化 |
| **Qwen2.5-VL** | ✅ Yes | Vision-Languageモデル。GPUで大幅に高速化（`--optimize`推奨） |
| Upstage | ❌ No | API呼び出しのみ（GPUは不要） |
| Azure | ❌ No | API呼び出しのみ（GPUは不要） |
| Gemini | ❌ No | API呼び出しのみ（GPUは不要） |
| Claude | ❌ No | API呼び出しのみ（GPUは不要） |

### 複数モデルの同時実行

YOMITOKUやQwenなどのローカルモデル（GPU使用）と、UpstageやAzureなどのAPIベースモデルを同時に実行できます：

```bash
# YOMITOKUをGPUで実行 + Upstage/AzureをAPI経由で実行
./run-gpu.sh ocr --models yomitoku upstage azure

# QwenとYOMITOKUをGPUで + 他のAPIモデルも実行
./run-gpu.sh layout --models qwen yomitoku gemini claude --optimize
```

**実行順序**: 指定した順番で順次実行されます。GPU使用モデルとAPI呼び出しモデルが混在していても問題ありません。

### パフォーマンスヒント

```bash
# Qwen使用時は --optimize オプションを推奨（GPU最適化）
./run-gpu.sh layout --models qwen --optimize

# ファイル数を制限してテスト実行
./run-gpu.sh ocr --models yomitoku --n-samples 5

# メモリ不足を避けるため、大量処理時はモデルを分けて実行
./run-gpu.sh ocr --models yomitoku qwen
./run-gpu.sh ocr --models upstage azure gemini
```

### トラブルシューティング

#### GPUメモリ不足エラー
```
RuntimeError: CUDA out of memory
```

対処法:
- `--n-samples`でファイル数を制限
- QwenとYOMITOKUを同時に実行せず、分けて実行
- 他のGPU使用プロセスを終了

#### DockerがGPUを認識しない

WSL2の場合:
```bash
# Windows側でNVIDIAドライバーを確認
# Docker Desktop > Settings > Resources > WSL Integration でGPUサポートを有効化
```

Linux/macOSの場合:
```bash
# NVIDIA Container Toolkitをインストール
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

---

## Docker Jupyter Lab 開発環境

Docker環境でJupyter Labを使用してインタラクティブな開発・実験が可能です。

### 起動方法

```bash
# Jupyter Lab を起動（バックグラウンド）
docker compose --profile jupyter up -d jupyter

# フォアグラウンドで起動（ログを確認しながら）
docker compose --profile jupyter up jupyter
```

### アクセス

起動後、以下のURLでJupyter Labにアクセスできます：

- **URL**: http://localhost:8890
- **認証**: トークン/パスワードなし（開発用設定）

> **Note**: ポート8890はdocker-compose.ymlで設定されています。他のサービスと競合する場合は変更可能です。

### マウントされるディレクトリ

| ローカル | コンテナ内 | 説明 |
|----------|-----------|------|
| `./src/` | `/app/src/` | ソースコード（編集可能） |
| `./notebook/` | `/app/notebook/` | ノートブックファイル |
| `./data/` | `/app/data/` | 入力データ（読み取り専用） |
| `./output/` | `/app/output/` | 出力結果 |

### 停止方法

```bash
# 停止
docker compose --profile jupyter down

# または Ctrl+C（フォアグラウンド起動時）
```

### トラブルシューティング

#### コンテナが即座に終了する

`docker-compose.override.yml`が存在する場合、設定が上書きされている可能性があります。

```bash
# 設定を確認
docker compose --profile jupyter config

# override.ymlを一時的に無効化
mv docker-compose.override.yml docker-compose.override.yml.bak
docker compose --profile jupyter up jupyter
```

#### ポートが使用中

```bash
# ポート使用状況を確認
lsof -i :8890

# 別のポートを使用（一時的）
docker compose --profile jupyter run -p 8891:8888 jupyter
```

---

## 設定と環境変数

### 概要

本プロジェクトはPydantic Settingsを使用した設定管理システムを採用しています。すべての設定は以下の優先順位で読み込まれます：

1. **環境変数** (最優先)
2. **`.env`ファイル**
3. **デフォルト値**

### 基本的な使用方法

```python
from src.config import get_settings

# 設定を取得（シングルトン）
settings = get_settings()

# ネスト構造でアクセス
api_key = settings.upstage.api_key
model = settings.gemini.model
```

### 必須環境変数

以下の環境変数は使用するモデルに応じて設定が必要です：

```env
# Upstage
UPSTAGE_API_KEY=your_upstage_api_key

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_azure_endpoint
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your_azure_api_key

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### オプション環境変数（モデル設定）

デフォルト値を上書きする場合に設定します：

```env
# Upstage
UPSTAGE_ENDPOINT=https://api.upstage.ai/v1/document-digitization
UPSTAGE_LAYOUT_MODEL=document-parse-nightly
UPSTAGE_OCR_MODEL=ocr-nightly

# Azure
AZURE_LAYOUT_MODEL=prebuilt-layout
AZURE_OCR_MODEL=prebuilt-read

# Gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_DPI=200

# Claude
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_DPI=200

# Qwen
QWEN_MODEL=Qwen/Qwen2.5-VL-7B-Instruct
QWEN_MAX_NEW_TOKENS=2048
QWEN_TEMPERATURE=0.1
QWEN_DO_SAMPLE=False

# YOMITOKU
YOMITOKU_VISUALIZE=True
```

### 設定クラス構造

| クラス | 用途 | 主な設定項目 |
|--------|------|-------------|
| `UpstageConfig` | Upstage API | `api_key`, `endpoint`, `layout_model`, `ocr_model` |
| `AzureConfig` | Azure Document Intelligence | `endpoint`, `api_key`, `layout_model`, `ocr_model` |
| `GeminiConfig` | Google Gemini | `api_key`, `model`, `dpi` |
| `ClaudeConfig` | Anthropic Claude | `api_key`, `model`, `max_tokens`, `dpi` |
| `QwenConfig` | Qwen2.5-VL | `model`, `max_new_tokens`, `temperature`, `do_sample` |
| `YomitokuConfig` | YOMITOKU | `visualize` |

### プログラムからの設定変更

```python
from src.config import get_settings, clear_settings_cache

# 現在の設定を取得
settings = get_settings()
print(f"Upstage model: {settings.upstage.layout_model}")

# 環境変数を変更後、キャッシュをクリアして再読み込み
import os
os.environ["UPSTAGE_LAYOUT_MODEL"] = "document-parse-v2"
clear_settings_cache()
settings = get_settings()
print(f"New model: {settings.upstage.layout_model}")
```

### Docker環境での設定

Docker環境では、`.env`ファイルが自動的に読み込まれます（`docker-compose.yml`の`env_file`設定）。

```yaml
# docker-compose.yml
services:
  document-processor:
    env_file:
      - .env  # APIキーと設定を読み込み
```

追加の環境変数を設定する場合：

```bash
# 実行時に環境変数を追加
docker compose run -e GEMINI_DPI=300 --rm document-processor layout --models gemini

# または docker-compose.override.yml で設定
```

---

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

### 共通

#### APIキーエラー
```
Error: 401 - Unauthorized
```
→ `.env`ファイルのAPIキーを確認してください

#### メモリ不足（Qwenモデル使用時）
```
RuntimeError: CUDA out of memory
```
→ `clear_model_cache()`を実行するか、`--n-samples`でファイル数を制限してください

### Linux/macOS

#### 権限エラー（Docker）
```bash
sudo chown -R $USER:$USER ./data ./output ./.cache
```

#### GPU認識エラー（Docker）
```bash
# GPU動作確認
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

### WSL2

#### 改行コードエラー
```
/bin/bash^M: bad interpreter
```
→ Windows側で以下を実行してから再クローン:
```bash
git config --global core.autocrlf input
```

#### GPUが認識されない
→ Windows側にNVIDIA ドライバー（CUDA対応）をインストールし、Docker Desktop設定でWSL2 GPUサポートを有効化

### Windows (CMD / PowerShell)

#### Docker Desktop起動エラー
→ WSL2が有効かつ最新であることを確認:
```powershell
wsl --update
wsl --set-default-version 2
```

#### ボリュームマウントエラー
→ Docker Desktop設定 > Resources > File Sharing で対象ドライブへのアクセスを許可

#### PowerShell実行ポリシーエラー
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### GPUがコンテナで認識されない
→ NVIDIA Container Toolkitをインストールし、Docker Desktop設定でGPUサポートを有効化
