# AZURE-OCR 後処理スクリプト

## 概要

`src/run_postprocess_azure.py` は、Azure Document Intelligence（prebuilt-read、OCR-onlyモード）の出力結果を処理し、Ground Truthデータセットと比較して評価レポートを生成するスクリプトです。

### 主な目的

- Azure-OCRのMarkdown出力からテキストを抽出
- Ground Truthとの比較による精度評価
- 多様な形式での結果出力（HTML可視化、JSON、CSV）

## 主な機能

### 1. テキスト抽出

Azure-OCRは`prebuilt-read`モデルを使用してMarkdown形式でテキストを出力します。

#### Markdown出力の処理

Markdownは既にプレーンテキストに近いため、シンプルな処理：

- 空白を正規化
- 先頭/末尾の空白を削除

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

# azure-ocr出力ディレクトリを指定
uv run python -m src.run_postprocess_azure output/20250125-1430/azure-ocr/
```

### コマンドラインオプション

#### 必須引数

```bash
azure_dir
```
Azure-OCRの出力ディレクトリパス（例: `output/20250125-1430/azure-ocr/`）

#### オプション引数

```bash
--gt-dataset PATH
```
Ground Truthデータセットのパス（デフォルト: `datasets/html_visualization_datatang/gt_dataset.json`）

```bash
--output-dir PATH
```
結果の出力先ディレクトリ（デフォルト: `{azure_dir}_evaluation`）

### 使用例

#### 例1: 基本的な実行

```bash
uv run python -m src.run_postprocess_azure output/20250125-1430/azure-ocr/
```

出力先: `output/20250125-1430/azure-ocr_evaluation/`

#### 例2: カスタムGround Truthを使用

```bash
uv run python -m src.run_postprocess_azure \
  output/20250125-1430/azure-ocr/ \
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
    "output_file": "data/batch_0_sample_0.md",
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
AZURE-OCR Post-Processing
================================================================================
Input directory: output/20250125-1430/azure-ocr
Ground truth: datasets/html_visualization_datatang/gt_dataset.json
Output directory: output/20250125-1430/azure-ocr_evaluation

Loading ground truth dataset...
Loaded 7691 ground truth entries

Processing azure-ocr outputs...
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

Saved JSON output to: output/20250125-1430/azure-ocr_evaluation/results_20250125_143500.json
Saved CSV output to: output/20250125-1430/azure-ocr_evaluation/results_20250125_143500.csv
Saved HTML output to: output/20250125-1430/azure-ocr_evaluation/results_20250125_143500.html
Saved summary to: output/20250125-1430/azure-ocr_evaluation/summary_20250125_143500.json

Post-processing complete!
```

## 実装の詳細

### データフロー

```
Azure-OCR出力 (Markdown)
    ↓
テキスト抽出 (直接読み込み)
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

Azure-OCRの出力ファイル名とGround Truthのマッピング：

- Azure出力: `batch_0_sample_0.md`
- Ground Truth: `cropped_images/batch_0_sample_0.png`
- マッピングキー: `batch_0_sample_0` (共通の基本ファイル名)

### Azure-OCRの出力形式

#### Markdown形式（prebuilt-read）

```markdown
愛知県豊川市赤坂町東裏
```

Azure Document Intelligenceの`prebuilt-read`モデルは、読み取り専用に最適化されており：

- 高解像度のOCR処理
- テキストの読み順序を自動処理
- シンプルなMarkdown出力

### Azure Document Intelligence APIの詳細

現在のスクリプトはMarkdownテキストのみを使用していますが、Azure APIは以下の豊富な情報を返します：

```python
result: AnalyzeResult = poller.result()

# 利用可能だがこのスクリプトでは未使用:
result.pages         # ページレベルの分析
result.paragraphs    # 段落情報
result.lines         # 行情報
result.words         # 単語レベル（バウンディングボックス、信頼度含む）
```

**将来の拡張案**: これらの構造化データを保存・活用することで、YOMITOKU-OCRと同等の詳細分析が可能になります。

### エラーハンドリング

- **ファイルが見つからない場合**: 警告を表示し、そのファイルをスキップ
- **空のコンテンツ**: 空文字列として処理
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

## YOMITOKUとの違い

### YOMITOKU-OCR
- 出力: JSON（単語レベルのバウンディングボックスと信頼度スコア）
- メトリクス: Accuracy、CER、編集距離、信頼度スコア統計
- 機能: 読み順序ソート、方向別処理

### AZURE-OCR（このスクリプト）
- 出力: Markdown（テキストのみ）
- メトリクス: Accuracy、CER、編集距離のみ
- 機能: シンプルなテキスト抽出と比較

**制限事項**:
- 単語レベルの分析不可（現バージョン）
- バウンディングボックス情報未使用
- 信頼度スコア情報未使用
- 読み順序の制御不可（API側で処理済み）

**注**: Azure APIは豊富な構造化データを返すため、スクリプトを拡張することで詳細分析が可能です。

## トラブルシューティング

### よくある問題

#### 1. Ground Truthが見つからない

```
Warning: No ground truth found for batch_0_sample_0
```

**原因**: ファイル名のマッピングが失敗

**解決策**:
- Ground Truth JSONのpathフィールドを確認
- Azure出力のファイル名形式を確認

#### 2. すべてのサンプルがスキップされる

```
Processed 0 samples
```

**原因**:
- azure_dirのパスが間違っている
- Markdownファイルが見つからない

**解決策**:
- `ls {azure_dir}/*.md` でファイルを確認
- 正しいディレクトリを指定

#### 3. 空のMarkdownファイル

**原因**: Azure OCRが文字を認識できなかった

**解決策**:
- スクリプトは自動的に空文字列として扱います
- 元の画像の品質を確認

## 将来の拡張案

### Azure APIの構造化データを活用

Azure Document Intelligence APIの`AnalyzeResult`オブジェクトには豊富な情報が含まれています：

```python
# 単語レベルの情報（バウンディングボックス、信頼度）
for page in result.pages:
    for word in page.words:
        content = word.content
        confidence = word.confidence
        polygon = word.polygon  # バウンディングボックス
```

**提案**:
1. `src/models/azure/ocr.py` を修正してJSON形式でも保存
2. YOMITOKU-OCRと同等の詳細分析スクリプトを作成
3. バウンディングボックスと信頼度スコアの統計も含める

## Azure Document Intelligenceについて

### prebuilt-readモデル

このスクリプトで使用している`prebuilt-read`モデルは：

- **用途**: 純粋なOCR（テキスト抽出）
- **特徴**: 高精度、高速、高解像度対応
- **出力**: Markdown形式（プレーンテキスト）

### prebuilt-layoutモデル（別モデル）

プロジェクトには`src/models/azure/layout.py`もあり、これは：

- **用途**: レイアウト分析（文書構造の理解）
- **特徴**: 表、見出し、段落などの構造を認識
- **出力**: HTMLやMarkdown（構造付き）

本スクリプトは`prebuilt-read`（OCR専用）の後処理用です。

## 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md): プロジェクト全体のドキュメント
- [run_models.py](../src/run_models.py): Azure-OCRの実行スクリプト
- [yomitoku_postprocessing.md](./yomitoku_postprocessing.md): YOMITOKU-OCR後処理スクリプト
- [upstage_postprocessing.md](./upstage_postprocessing.md): Upstage-OCR後処理スクリプト
- [Azure Document Intelligence Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)

## ライセンス

このスクリプトはプロジェクトのライセンスに従います。
