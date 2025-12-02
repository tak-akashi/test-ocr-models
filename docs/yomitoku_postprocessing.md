# YOMITOKU-OCR 後処理スクリプト

## 概要

`src/run_postprocess_yomitoku.py` は、YOMITOKU-OCRの出力結果を処理し、Ground Truthデータセットと比較して評価レポートを生成するスクリプトです。

### 主な目的

- YOMITOKU-OCRの複数テキスト領域を適切な読み順序でソート・統合
- Ground Truthとの比較による精度評価
- 多様な形式での結果出力（HTML可視化、JSON、CSV）
- 信頼度スコアの統計分析

## 主な機能

### 1. テキスト抽出とソート

YOMITOKU-OCRは個々のテキスト領域を検出しますが、読み順序は保証されていません。このスクリプトは `direction` フィールドに基づいて適応的にソートします。

#### ソートロジック

- **横書き（horizontal）**: Y座標（上）→ X座標（左）の順でソート
  - 上から下、左から右の読み順序
- **縦書き（vertical）**: X座標（右）→ Y座標（上）の順でソート
  - 右から左の列、各列は上から下の読み順序

#### 信頼度フィルタリング

- `det_score`: 検出信頼度スコア
- `rec_score`: 認識信頼度スコア
- `--min-score` オプションで閾値を設定可能

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

#### 信頼度スコア統計
- 平均、最小、最大の検出/認識スコア
- 横書き/縦書きテキスト領域の数

## 使用方法

### 基本的な使い方

```bash
# 依存関係のインストール
uv sync

# yomitoku-ocr出力ディレクトリを指定
uv run python -m src.run_postprocess_yomitoku output/20250125-1430/yomitoku-ocr/
```

### コマンドラインオプション

#### 必須引数

```bash
yomitoku_dir
```
YOMITOKU-OCRの出力ディレクトリパス（例: `output/20250125-1430/yomitoku-ocr/`）

#### オプション引数

```bash
--gt-dataset PATH
```
Ground Truthデータセットのパス（デフォルト: `datasets/html_visualization_datatang/gt_dataset.json`）

```bash
--output-dir PATH
```
結果の出力先ディレクトリ（デフォルト: `{yomitoku_dir}_evaluation`）

```bash
--min-score FLOAT
```
最小信頼度スコア閾値（0.0-1.0、デフォルト: 0.0）

### 使用例

#### 例1: 基本的な実行

```bash
uv run python -m src.run_postprocess_yomitoku output/20250125-1430/yomitoku-ocr/
```

出力先: `output/20250125-1430/yomitoku-ocr_evaluation/`

#### 例2: 信頼度フィルタリング付き

低信頼度の検出結果を除外する場合：

```bash
uv run python -m src.run_postprocess_yomitoku output/20250125-1430/yomitoku-ocr/ --min-score 0.5
```

#### 例3: カスタムGround Truthを使用

```bash
uv run python -m src.run_postprocess_yomitoku \
  output/20250125-1430/yomitoku-ocr/ \
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
  - 平均信頼度スコア
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
    "json_file": "data/batch_0_sample_0_0.json",
    "predicted": "予測されたテキスト",
    "ground_truth": "正解テキスト",
    "exact_match": false,
    "edit_distance": 5,
    "cer": 0.234,
    "predicted_length": 20,
    "ground_truth_length": 21,
    "word_count": 3,
    "avg_det_score": 0.823,
    "avg_rec_score": 0.856,
    "min_det_score": 0.699,
    "min_rec_score": 0.755,
    "max_det_score": 0.907,
    "max_rec_score": 0.961,
    "horizontal_count": 2,
    "vertical_count": 1
  }
]
```

### 3. CSVレポート（`results_{timestamp}.csv`）

Excel等で分析可能な表形式：

| filename | exact_match | edit_distance | cer | predicted | ground_truth | word_count | avg_det_score | avg_rec_score |
|----------|-------------|---------------|-----|-----------|--------------|------------|---------------|---------------|
| batch_0_sample_0 | False | 5 | 0.234 | 予測テキスト | 正解テキスト | 3 | 0.823 | 0.856 |

### 4. サマリー統計（`summary_{timestamp}.json`）

全体の統計情報：

```json
{
  "total_samples": 512,
  "exact_matches": 244,
  "accuracy": 0.4766,
  "avg_cer": 0.2345,
  "avg_edit_distance": 8.32,
  "avg_det_score": 0.8234,
  "avg_rec_score": 0.8567
}
```

### 5. コンソール出力

実行時に標準出力に表示：

```
================================================================================
YOMITOKU-OCR Post-Processing
================================================================================
Input directory: output/20250125-1430/yomitoku-ocr
Ground truth: datasets/html_visualization_datatang/gt_dataset.json
Output directory: output/20250125-1430/yomitoku-ocr_evaluation
Min confidence score: 0.0

Loading ground truth dataset...
Loaded 7691 ground truth entries

Processing yomitoku-ocr outputs...
Processed 512 samples

================================================================================
Summary Statistics
================================================================================
Total Samples:      512
Exact Matches:      244
Accuracy:           47.66%
Avg CER:            23.45%
Avg Edit Distance:  8.32
Avg Det Score:      0.8234
Avg Rec Score:      0.8567
================================================================================

Saved JSON output to: output/20250125-1430/yomitoku-ocr_evaluation/results_20250125_143500.json
Saved CSV output to: output/20250125-1430/yomitoku-ocr_evaluation/results_20250125_143500.csv
Saved HTML output to: output/20250125-1430/yomitoku-ocr_evaluation/results_20250125_143500.html
Saved summary to: output/20250125-1430/yomitoku-ocr_evaluation/summary_20250125_143500.json

Post-processing complete!
```

## 実装の詳細

### データフロー

```
YOMITOKU-OCR出力 (JSON)
    ↓
テキスト抽出・ソート
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

YOMITOKU-OCRの出力ファイル名とGround Truthのマッピング：

- YOMITOKU出力: `batch_0_sample_0_0.json` (最後の`_0`はページインデックス)
- Ground Truth: `cropped_images/batch_0_sample_0.png`
- マッピングキー: `batch_0_sample_0` (共通の基本ファイル名)

### 信頼度スコアの処理

各テキスト領域には2つのスコアがあります：

- **det_score**: テキスト領域の検出信頼度（0.0-1.0）
- **rec_score**: 文字認識の信頼度（0.0-1.0）

`--min-score` オプションを使用すると、両方のスコアがこの閾値以上の領域のみが処理されます。

### エラーハンドリング

- **ファイルが見つからない場合**: 警告を表示し、そのファイルをスキップ
- **JSONパースエラー**: エラーメッセージを表示し、次のファイルへ
- **空のwords配列**: 空文字列として処理（CER = 0 if GT also empty）
- **Ground Truthが見つからない**: 警告を表示し、スキップ

## 依存関係

### 新規追加

- `Levenshtein >= 0.26.1`: 編集距離計算用

### 既存の依存関係

- `pathlib`: パス操作（標準ライブラリ）
- `json`: JSON処理（標準ライブラリ）
- `csv`: CSV出力（標準ライブラリ）
- `unicodedata`: Unicode正規化（標準ライブラリ）
- `argparse`: コマンドライン引数（標準ライブラリ）

## トラブルシューティング

### よくある問題

#### 1. Ground Truthが見つからない

```
Warning: No ground truth found for batch_0_sample_0
```

**原因**: ファイル名のマッピングが失敗

**解決策**:
- Ground Truth JSONのpathフィールドを確認
- YOMITOKU出力のファイル名形式を確認

#### 2. すべてのサンプルがスキップされる

```
Processed 0 samples
```

**原因**:
- yomitoku_dirのパスが間違っている
- JSONファイルが見つからない
- min-scoreが高すぎる

**解決策**:
- `ls {yomitoku_dir}/*_0.json` でファイルを確認
- `--min-score 0.0` で全サンプルを処理

#### 3. CERが100%を超える

**原因**: Ground Truthが非常に短い場合、編集距離がGT長を超えることがある

**説明**: これは正常な動作です。CERは100%を超えることがあります。

## 将来の改善案

### 機能拡張

- [ ] バッチ別の統計レポート
- [ ] 混同行列（よく間違える文字ペア）
- [ ] 信頼度スコアと精度の相関分析
- [ ] 複数のGround Truthフォーマットのサポート
- [ ] インタラクティブなHTMLレポート（ソート・フィルタ機能）

### パフォーマンス最適化

- [ ] 並列処理（multiprocessing）
- [ ] 大規模データセット用のバッチ処理
- [ ] プログレスバーの追加

### UX改善

- [ ] 最新のyomitoku-ocr出力を自動検出
- [ ] 設定ファイルのサポート（YAML/JSON）
- [ ] ドライラン機能（実際の出力前にプレビュー）

## 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md): プロジェクト全体のドキュメント
- [run_models.py](../src/run_models.py): YOMITOKU-OCRの実行スクリプト
- YOMITOKU公式ドキュメント: https://github.com/kotaro-kinoshita/yomitoku

## ライセンス

このスクリプトはプロジェクトのライセンスに従います。
