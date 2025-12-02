# YOMITOKU Layout Mode 後処理スクリプト

## 概要

`src/run_postprocess_yomitoku_layout.py` は、YOMITOKU Layout Mode（DocumentAnalyzer）の出力結果を処理し、Ground Truthデータセットと比較して評価レポートを生成するスクリプトです。

### 主な目的

- YOMITOKU Layout Modeの`paragraphs`フィールドを活用
- 文書構造（段落順序）を考慮したテキスト抽出
- Ground Truthとの比較による精度評価
- レイアウト情報（段落数、表数、図数）の統計分析

## YOMITOKU OCR Mode との違い

### OCR Mode (`run_postprocess_yomitoku.py`)
- **使用クラス**: `OCR`（シンプル、高速）
- **出力**: JSON（`words`フィールドのみ）
- **テキスト抽出**: 単語を座標でソート（top-to-bottom, left-to-right）
- **メトリクス**: Accuracy、CER、編集距離、信頼度スコア

### Layout Mode (`run_postprocess_yomitoku_layout.py`)
- **使用クラス**: `DocumentAnalyzer`（フル機能、遅い）
- **出力**: JSON（`paragraphs`, `tables`, `words`, `figures`）
- **テキスト抽出**: 段落を`order`フィールドでソート
- **メトリクス**: Accuracy、CER、編集距離、段落/表/図の統計

### なぜ両方必要か？

| 特徴 | OCR Mode | Layout Mode |
|------|----------|-------------|
| **精度** | 座標ベースソート | セマンティック順序 |
| **速度** | 高速 | 低速 |
| **構造** | なし | 段落、表、図を検出 |
| **用途** | シンプルなテキスト抽出 | 複雑なレイアウト文書 |

**推奨**:
- 単純な文書 → OCR Mode
- 複雑なレイアウト（複数段組、表、図）→ Layout Mode

## 主な機能

### 1. 段落ベースのテキスト抽出

Layout Modeは文書を段落単位で分析し、読み順序を自動的に決定します。

#### ParagraphSchema構造

```json
{
  "paragraphs": [
    {
      "box": [x, y, width, height],
      "contents": "段落のテキスト内容",
      "direction": "horizontal",
      "order": 1,
      "role": "paragraph"
    }
  ]
}
```

#### 抽出ロジック

```python
# 段落をorder フィールドでソート
sorted_paragraphs = sorted(paragraphs, key=lambda p: p.get("order", 0))

# contents フィールドを連結
text = "".join([p["contents"] for p in sorted_paragraphs])
```

**利点**:
- 文書構造を尊重
- セマンティックな読み順序（見出し → 本文）
- 複数段組の文書に強い

### 2. レイアウト情報の統計

各サンプルについて以下を記録：

- **paragraph_count**: 検出された段落の数
- **table_count**: 検出された表の数
- **figure_count**: 検出された図/画像の数

### 3. テキスト正規化

OCR Modeと同じ正規化を実施：

- **Unicode正規化（NFKC）**
- **空白正規化**

### 4. 評価メトリクス

- **正解率（Accuracy）**: 完全一致率
- **CER（Character Error Rate）**: 文字誤り率
- **編集距離（Levenshtein Distance）**: 編集操作の回数

## 使用方法

### 前提条件

Layout Modeを実行すると、以下のファイルが生成されます：

```bash
uv run layout --models yomitoku
```

出力例：
```
output/20250125-1430/yomitoku/data/
├── sample_0.html            # HTML形式（構造化）
├── sample_0.json            # JSON形式（NEW! 後処理用）
├── sample_ocr_0.jpg         # OCR可視化
└── sample_layout_0.jpg      # Layout可視化
```

### 基本的な使い方

```bash
# 依存関係のインストール
uv sync

# yomitoku layout出力ディレクトリを指定
uv run python -m src.run_postprocess_yomitoku_layout output/20250125-1430/yomitoku/
```

### コマンドラインオプション

#### 必須引数

```bash
yomitoku_dir
```
YOMITOKU Layout Modeの出力ディレクトリパス（例: `output/20250125-1430/yomitoku/`）

#### オプション引数

```bash
--gt-dataset PATH
```
Ground Truthデータセットのパス（デフォルト: `datasets/html_visualization_datatang/gt_dataset.json`）

```bash
--output-dir PATH
```
結果の出力先ディレクトリ（デフォルト: `{yomitoku_dir}_evaluation_layout`）

### 使用例

#### 例1: 基本的な実行

```bash
uv run python -m src.run_postprocess_yomitoku_layout output/20250125-1430/yomitoku/
```

出力先: `output/20250125-1430/yomitoku_evaluation_layout/`

#### 例2: カスタムGround Truthを使用

```bash
uv run python -m src.run_postprocess_yomitoku_layout \
  output/20250125-1430/yomitoku/ \
  --gt-dataset custom_data/my_gt.json \
  --output-dir evaluation_results_layout/
```

## 出力形式

### 1. HTML可視化（`results_{timestamp}.html`）

視覚的な比較レポート：

- **サマリーセクション**:
  - 総サンプル数
  - 完全一致数
  - 正解率
  - 平均CER
  - 平均段落数
  - 平均表数

- **詳細比較セクション**:
  - 各サンプルのGround Truth vs 予測結果
  - 一致/不一致の視覚的表示
  - サンプルごとのレイアウト情報

### 2. 詳細JSON（`results_{timestamp}.json`）

全サンプルの詳細データを含むJSON配列：

```json
[
  {
    "filename": "batch_0_sample_0",
    "json_file": "data/batch_0_sample_0_0.json",
    "predicted": "予測されたテキスト",
    "ground_truth": "正解テキスト",
    "exact_match": false,
    "edit_distance": 5,
    "cer": 0.234,
    "predicted_length": 20,
    "ground_truth_length": 21,
    "paragraph_count": 3,
    "table_count": 1,
    "figure_count": 0
  }
]
```

### 3. CSVレポート（`results_{timestamp}.csv`）

Excel等で分析可能な表形式：

| filename | exact_match | cer | paragraph_count | table_count | figure_count |
|----------|-------------|-----|-----------------|-------------|--------------|
| sample_0 | False | 0.234 | 3 | 1 | 0 |

### 4. サマリー統計（`summary_{timestamp}.json`）

全体の統計情報：

```json
{
  "total_samples": 512,
  "exact_matches": 244,
  "accuracy": 0.4766,
  "avg_cer": 0.2345,
  "avg_edit_distance": 8.32,
  "avg_paragraph_count": 2.5,
  "avg_table_count": 0.3,
  "avg_figure_count": 0.1
}
```

### 5. コンソール出力

実行時に標準出力に表示：

```
================================================================================
YOMITOKU Layout Mode Post-Processing
================================================================================
Input directory: output/20250125-1430/yomitoku
Ground truth: datasets/html_visualization_datatang/gt_dataset.json
Output directory: output/20250125-1430/yomitoku_evaluation_layout

Loading ground truth dataset...
Loaded 7691 ground truth entries

Processing yomitoku layout outputs...
Processed 512 samples

================================================================================
Summary Statistics
================================================================================
Total Samples:      512
Exact Matches:      244
Accuracy:           47.66%
Avg CER:            23.45%
Avg Edit Distance:  8.32
Avg Paragraphs:     2.50
Avg Tables:         0.30
Avg Figures:        0.10
================================================================================
```

## 実装の詳細

### データフロー

```
YOMITOKU Layout出力 (JSON)
    ↓
Paragraphsフィールド抽出
    ↓
orderフィールドでソート
    ↓
contentsフィールド連結
    ↓
テキスト正規化
    ↓
Ground Truthと比較
    ↓
メトリクス計算
    ↓
結果出力 (HTML/JSON/CSV)
```

### ファイルマッピング

YOMITOKU Layout出力ファイル名とGround Truthのマッピング：

- Layout出力: `batch_0_sample_0_0.json` (最後の`_0`はページインデックス)
- Ground Truth: `cropped_images/batch_0_sample_0.png`
- マッピングキー: `batch_0_sample_0` (共通の基本ファイル名)

### Layout Modeの出力内容

#### DocumentAnalyzerSchema

```python
{
  "paragraphs": [
    {
      "box": [x, y, width, height],
      "contents": "段落テキスト",
      "direction": "horizontal/vertical",
      "order": 1,
      "role": "heading/paragraph/..."
    }
  ],
  "tables": [
    {
      "box": [x, y, width, height],
      # 表構造情報
    }
  ],
  "words": [
    # OCR Modeと同じword-level情報
  ],
  "figures": [
    {
      "box": [x, y, width, height]
    }
  ]
}
```

### エラーハンドリング

- **ファイルが見つからない場合**: 警告を表示し、スキップ
- **JSONパースエラー**: エラーメッセージを表示し、次のファイルへ
- **空のparagraphs配列**: 空文字列として処理
- **Ground Truthが見つからない**: 警告を表示し、スキップ

## OCR Mode vs Layout Mode 比較

### 同じデータセットでの比較実行

```bash
# OCR Mode（words fieldベース）
uv run python -m src.run_postprocess_yomitoku output/20250125-1430/yomitoku-ocr/

# Layout Mode（paragraphs fieldベース）
uv run python -m src.run_postprocess_yomitoku_layout output/20250125-1430/yomitoku/
```

### 期待される違い

| メトリクス | OCR Mode | Layout Mode |
|-----------|----------|-------------|
| **精度** | 座標ソートの誤差あり | order fieldで正確 |
| **処理対象** | 全単語 | 段落単位 |
| **複雑レイアウト** | 誤順序の可能性 | 正しい順序 |
| **構造情報** | なし | 段落/表/図の統計 |

**推奨**:
- 両方実行して精度を比較
- 複雑なレイアウトではLayout Modeが優位

## 依存関係

### 新規追加（既存と同じ）

- `Levenshtein >= 0.26.1`: 編集距離計算用

### 既存の依存関係

- `pathlib`: パス操作（標準ライブラリ）
- `json`: JSON処理（標準ライブラリ）
- `csv`: CSV出力（標準ライブラリ）
- `unicodedata`: Unicode正規化（標準ライブラリ）
- `argparse`: コマンドライン引数（標準ライブラリ）

## トラブルシューティング

### よくある問題

#### 1. JSONファイルが見つからない

```
Processed 0 samples
```

**原因**: `layout.py`が修正前に実行された

**解決策**:
1. `src/models/yomitoku/layout.py`が最新版か確認
2. Layout Modeを再実行してJSON出力を生成:
   ```bash
   uv run layout --models yomitoku
   ```

#### 2. paragraphsフィールドが空

```
Warning: Empty paragraphs for sample_0
```

**原因**: 文書構造が検出できなかった

**解決策**:
- 元の画像/PDFの品質を確認
- OCR Modeと比較（wordsフィールドはあるか？）

#### 3. orderフィールドがNone

```json
{
  "order": null,
  "contents": "..."
}
```

**動作**: スクリプトは自動的に0として扱う

**影響**: ソート順序が不正確になる可能性

## 将来の拡張案

### 構造比較メトリクス

Ground Truthに構造情報がある場合：

- **段落分割精度**: 段落数の一致率
- **表検出精度**: 表の検出/誤検出率
- **見出し認識精度**: roleフィールドの正確性

### 複数モデル比較

```bash
# 3つのアプローチで同じデータセットを評価
uv run python -m src.run_postprocess_yomitoku output/xxx/yomitoku-ocr/          # OCR Mode
uv run python -m src.run_postprocess_yomitoku output/xxx/yomitoku/              # Layout (wordsベース)
uv run python -m src.run_postprocess_yomitoku_layout output/xxx/yomitoku/       # Layout (paragraphsベース)
```

結果を比較して、最適なアプローチを選択。

## 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md): プロジェクト全体のドキュメント
- [run_models.py](../src/run_models.py): YOMITOKU Layout Modeの実行スクリプト
- [yomitoku_postprocessing.md](./yomitoku_postprocessing.md): YOMITOKU OCR Mode後処理スクリプト
- [upstage_postprocessing.md](./upstage_postprocessing.md): Upstage-OCR後処理スクリプト
- [azure_postprocessing.md](./azure_postprocessing.md): Azure-OCR後処理スクリプト

## ライセンス

このスクリプトはプロジェクトのライセンスに従います。
