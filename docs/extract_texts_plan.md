# テキスト抽出スクリプト作成計画

## 概要
`output/20251202-0942`ディレクトリ内のazure、upstage、yomitokuモデル出力からテキストを抽出するスクリプトを作成する。

## 入力データ構造

| モデル | ディレクトリ | ファイル形式 | テキスト抽出方法 |
|--------|-------------|-------------|-----------------|
| Azure | `azure/appen_samples_200/` | `.md` | Markdownをそのまま正規化 |
| Upstage | `upstage/appen_samples_200/` | `.html` | BeautifulSoupでHTMLからテキスト抽出 |
| YOMITOKU | `yomitoku/appen_samples_200/` | `.json` | `words`配列から`content`を読み順でソート・結合 |

## 出力形式

1. **モデル別ファイル**（CSV + JSON）
   - `azure_texts.csv`, `azure_texts.json`
   - `upstage_texts.csv`, `upstage_texts.json`
   - `yomitoku_texts.csv`, `yomitoku_texts.json`

2. **統合ファイル**（3モデル比較用）
   - `combined_texts.csv` - ファイル名、azure_text、upstage_text、yomitoku_textの列
   - `combined_texts.json` - 同内容の構造化データ

## 実装計画

### 新規スクリプト: `src/extract_texts.py`

```
src/extract_texts.py
├── extract_text_azure(file_path)      # Markdown → テキスト
├── extract_text_upstage(file_path)    # HTML → テキスト（BeautifulSoup使用）
├── extract_text_yomitoku(file_path)   # JSON → テキスト（読み順ソート）
├── process_model_outputs(model_dir, model_type)  # モデル別処理
├── save_model_outputs(results, output_dir, model_name)  # モデル別出力
├── save_combined_outputs(all_results, output_dir)  # 統合出力
└── main()                             # CLI エントリーポイント
```

### CLI使用方法

```bash
uv run python -m src.extract_texts output/20251202-0942 --output-dir output/20251202-0942/extracted
```

### テキスト抽出ロジック（既存コードから流用）

1. **Azure (Markdown)**
   - `run_postprocess_azure.py:38-54` の `extract_text_from_markdown()` を使用
   - 空白正規化のみ

2. **Upstage (HTML)**
   - `run_postprocess_upstage.py:39-64` の `extract_text_from_html()` を使用
   - BeautifulSoupでscript/style除去後テキスト抽出

3. **YOMITOKU (JSON)**
   - `run_postprocess_yomitoku.py:38-124` の `extract_and_sort_text()` を使用
   - 横書き・縦書きを読み順でソートして結合

### 出力ファイル構造

```
output/20251202-0942/extracted/
├── azure_texts.csv
├── azure_texts.json
├── upstage_texts.csv
├── upstage_texts.json
├── yomitoku_texts.csv
├── yomitoku_texts.json
├── combined_texts.csv
└── combined_texts.json
```

### CSV形式

**モデル別**
```csv
filename,text
ja_pii_handwriting_0001,抽出されたテキスト...
```

**統合**
```csv
filename,azure,upstage,yomitoku
ja_pii_handwriting_0001,azureテキスト...,upstageテキスト...,yomitokuテキスト...
```

## 依存関係
- `beautifulsoup4` (既存)
- 標準ライブラリ: `json`, `csv`, `pathlib`, `argparse`

## 実装手順

1. `src/extract_texts.py` を新規作成
2. 各モデル用のテキスト抽出関数を実装（既存コードから流用）
3. モデル別・統合の両方の出力処理を実装
4. CLIインターフェースを実装
5. テスト実行
