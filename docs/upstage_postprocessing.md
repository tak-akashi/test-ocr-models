# UPSTAGE-OCR 後処理スクリプト

## 概要

`src/run_postprocess_upstage.py` は、Upstage Document Parse API（OCR-onlyモード）の出力結果を処理し、Ground Truthデータセットと比較して評価レポートを生成するスクリプトです。

### 主な目的

- Upstage-OCRのHTML/Markdown出力からテキストを抽出
- Ground Truthとの比較による精度評価
- 多様な形式での結果出力（HTML可視化、JSON、CSV）

## 主な機能

### 1. テキスト抽出

Upstage-OCRはHTML形式またはMarkdown形式でテキストを出力します。このスクリプトは両形式に対応しています。

#### HTML出力の処理

BeautifulSoupを使用してHTMLをパースし、純粋なテキストコンテンツを抽出：

- `<script>` と `<style>` タグを除去
- テキストコンテンツのみを取得
- 空白を正規化

#### Markdown出力の処理

Markdownは既にプレーンテキストに近いため、空白の正規化のみ実施。

### 2. テキスト正規化

比較時に以下の正規化を実行：

- **Unicode正規化（NFKC）**:
  - 全角/半角の統一
  - 互換文字の標準化
  - 濁点の結合方法の統一
- **空白正規化**:
  - 連続する空白を単一スペースに
  - 先頭/末尾の空白を削除

### 3. 評価メトリクス

#### 正解率（Accuracy）
完全一致したサンプルの割合：
```
Accuracy = 完全一致数 / 総サンプル数
```

#### 文字誤り率（CER: Character Error Rate）
文字レベルの編集距離に基づく誤り率：
```
CER = Levenshtein距離 / Ground Truth文字数
```

#### 編集距離（Levenshtein Distance）
予測テキストとGround Truthの間の編集操作（挿入、削除、置換）の最小回数

## 使用方法

### 基本的な使い方

```bash
# 依存関係のインストール
uv sync

# upstage-ocr出力ディレクトリを指定
uv run python -m src.run_postprocess_upstage output/20250125-1430/upstage-ocr/
```

### コマンドラインオプション

#### 必須引数

```bash
upstage_dir
```
Upstage-OCRの出力ディレクトリパス（例: `output/20250125-1430/upstage-ocr/`）

#### オプション引数

```bash
--gt-dataset PATH
```
Ground Truthデータセットのパス（デフォルト: `datasets/html_visualization_datatang/gt_dataset.json`）

```bash
--output-dir PATH
```
結果の出力先ディレクトリ（デフォルト: `{upstage_dir}_evaluation`）

### 使用例

#### 例1: 基本的な実行

```bash
uv run python -m src.run_postprocess_upstage output/20250125-1430/upstage-ocr/
```

出力先: `output/20250125-1430/upstage-ocr_evaluation/`

#### 例2: カスタムGround Truthを使用

```bash
uv run python -m src.run_postprocess_upstage \
  output/20250125-1430/upstage-ocr/ \
  --gt-dataset custom_data/my_gt.json \
  --output-dir evaluation_results/
```

## 出力形式

スクリプトは複数の形式で結果を出力します：

### 1. HTML可視化（`results_{timestamp}.html`）

視覚的な比較レポート：

- **サマリーセクション**:
  - 総サンプル数
  - 完全一致数
  - 正解率
  - 平均CER
  - 平均編集距離
- **詳細比較セクション**:
  - 各サンプルのGround Truth vs 予測結果
  - 一致/不一致の視覚的表示（緑/赤のボーダー）
  - サンプルごとのメトリクス

### 2. 詳細JSON（`results_{timestamp}.json`）

全サンプルの詳細データを含むJSON配列：

```json
[
  {
    "filename": "batch_0_sample_0",
    "output_file": "data/batch_0_sample_0.html",
    "predicted": "予測されたテキスト",
    "ground_truth": "正解テキスト",
    "exact_match": false,
    "edit_distance": 5,
    "cer": 0.234,
    "predicted_length": 20,
    "ground_truth_length": 21
  }
]
```

### 3. CSVレポート（`results_{timestamp}.csv`）

Excel等で分析可能な表形式：

| filename | exact_match | edit_distance | cer | predicted | ground_truth | predicted_length | ground_truth_length |
|----------|-------------|---------------|-----|-----------|--------------|------------------|---------------------|
| batch_0_sample_0 | False | 5 | 0.234 | 予測テキスト | 正解テキスト | 20 | 21 |

### 4. サマリー統計（`summary_{timestamp}.json`）

全体の統計情報：

```json
{
  "total_samples": 512,
  "exact_matches": 244,
  "accuracy": 0.4766,
  "avg_cer": 0.2345,
  "avg_edit_distance": 8.32
}
```

### 5. コンソール出力

実行時に標準出力に表示：

```
================================================================================
UPSTAGE-OCR Post-Processing
================================================================================
Input directory: output/20250125-1430/upstage-ocr
Ground truth: datasets/html_visualization_datatang/gt_dataset.json
Output directory: output/20250125-1430/upstage-ocr_evaluation

Loading ground truth dataset...
Loaded 7691 ground truth entries

Processing upstage-ocr outputs...
Processed 512 samples

================================================================================
Summary Statistics
================================================================================
Total Samples:      512
Exact Matches:      244
Accuracy:           47.66%
Avg CER:            23.45%
Avg Edit Distance:  8.32
================================================================================

Saved JSON output to: output/20250125-1430/upstage-ocr_evaluation/results_20250125_143500.json
Saved CSV output to: output/20250125-1430/upstage-ocr_evaluation/results_20250125_143500.csv
Saved HTML output to: output/20250125-1430/upstage-ocr_evaluation/results_20250125_143500.html
Saved summary to: output/20250125-1430/upstage-ocr_evaluation/summary_20250125_143500.json

Post-processing complete!
```

## 実装の詳細

### データフロー

```
Upstage-OCR出力 (HTML/Markdown)
    ↓
テキスト抽出 (BeautifulSoup/直接読み込み)
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

Upstage-OCRの出力ファイル名とGround Truthのマッピング：

- Upstage出力: `batch_0_sample_0.html` または `batch_0_sample_0.md`
- Ground Truth: `cropped_images/batch_0_sample_0.png`
- マッピングキー: `batch_0_sample_0` (共通の基本ファイル名)

### Upstage-OCRの出力形式

#### HTML形式（デフォルト）

```html
<html>
  <head>
    <meta charset="utf-8"/>
    <style>/* table styles */</style>
  </head>
  <body>
    <p data-category="paragraph" id="0" style="font-size:14px">
      愛知県豊川市赤坂町東裏
    </p>
  </body>
</html>
```

#### Markdown形式

```markdown
愛知県豊川市赤坂町東裏
```

### エラーハンドリング

- **ファイルが見つからない場合**: 警告を表示し、そのファイルをスキップ
- **HTMLパースエラー**: 空文字列として処理
- **空のコンテンツ**: 空文字列として処理
- **Ground Truthが見つからない**: 警告を表示し、スキップ

## 依存関係

### 新規追加

- `beautifulsoup4 >= 4.12.0`: HTMLパース用
- `Levenshtein >= 0.26.1`: 編集距離計算用

### 既存の依存関係

- `pathlib`: パス操作（標準ライブラリ）
- `json`: JSON処理（標準ライブラリ）
- `csv`: CSV出力（標準ライブラリ）
- `unicodedata`: Unicode正規化（標準ライブラリ）
- `argparse`: コマンドライン引数（標準ライブラリ）

## YOMITOKUとの違い

### YOMITOKU-OCR
- 出力: JSON（単語レベルのバウンディングボックスと信頼度スコア）
- メトリクス: Accuracy、CER、編集距離、信頼度スコア統計
- 機能: 読み順序ソート、方向別処理

### UPSTAGE-OCR（このスクリプト）
- 出力: HTML/Markdown（テキストのみ）
- メトリクス: Accuracy、CER、編集距離のみ
- 機能: シンプルなテキスト抽出と比較

**制限事項**:
- 単語レベルの分析不可
- バウンディングボックス情報なし
- 信頼度スコア情報なし
- 読み順序の制御不可（API側で処理済み）

## トラブルシューティング

### よくある問題

#### 1. Ground Truthが見つからない

```
Warning: No ground truth found for batch_0_sample_0
```

**原因**: ファイル名のマッピングが失敗

**解決策**:
- Ground Truth JSONのpathフィールドを確認
- Upstage出力のファイル名形式を確認

#### 2. すべてのサンプルがスキップされる

```
Processed 0 samples
```

**原因**:
- upstage_dirのパスが間違っている
- HTML/Markdownファイルが見つからない

**解決策**:
- `ls {upstage_dir}/*.html` または `ls {upstage_dir}/*.md` でファイルを確認
- 正しいディレクトリを指定

#### 3. HTMLパースエラー

**原因**: 不正なHTML形式

**解決策**:
- スクリプトは自動的にエラーを処理し、空文字列として扱います
- エラーログを確認して原因を特定

## 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md): プロジェクト全体のドキュメント
- [run_models.py](../src/run_models.py): Upstage-OCRの実行スクリプト
- [yomitoku_postprocessing.md](./yomitoku_postprocessing.md): YOMITOKU-OCR後処理スクリプト
- [azure_postprocessing.md](./azure_postprocessing.md): Azure-OCR後処理スクリプト

## ライセンス

このスクリプトはプロジェクトのライセンスに従います。
