"""
カテゴリ別の手書き画像クロップ処理

手書き画像を4つのカテゴリに自動分類し、各カテゴリに最適なパラメータで
1行手書き部分をクロップする。

カテゴリ:
- WHITE_LOW_CONTRAST: 白背景・薄い文字
- GRAY_BACKGROUND: グレー背景
- WHITE_HIGH_CONTRAST: 白背景・濃い文字
- VERTICAL: 縦書き（縦長画像）

使用方法:
    uv run python src/utils/process_by_category.py [入力ディレクトリ] [出力ディレクトリ]

    # デフォルト（datasets/appen_test_200 → datasets/test_deskew_output）
    uv run python src/utils/process_by_category.py

    # カスタムディレクトリ指定
    uv run python src/utils/process_by_category.py datasets/my_images datasets/output
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


def classify_all_images(input_dir: Path) -> dict[str, list[str]]:
    """全画像をカテゴリに分類"""
    categories = {
        'VERTICAL': [],
        'WHITE_HIGH_CONTRAST': [],
        'WHITE_LOW_CONTRAST': [],
        'GRAY_BACKGROUND': []
    }

    for img_path in sorted(input_dir.glob('*.jpg')):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h, w = img.shape[:2]

        # 縦書き判定: 高さ > 幅 * 1.2
        if h > w * 1.2:
            categories['VERTICAL'].append(img_path.name)
            continue

        # 背景・コントラスト判定
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        bg_brightness = np.percentile(gray, 95)
        contrast = np.std(gray)

        is_white_bg = bg_brightness > 245
        is_high_contrast = contrast > 30

        if not is_white_bg:
            categories['GRAY_BACKGROUND'].append(img_path.name)
        elif is_high_contrast:
            categories['WHITE_HIGH_CONTRAST'].append(img_path.name)
        else:
            categories['WHITE_LOW_CONTRAST'].append(img_path.name)

    return categories


def detect_bounds_adaptive(gray: np.ndarray, min_area: int = 100) -> Optional[tuple]:
    """Adaptive閾値で境界検出（グレー背景用）"""
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 31, 10
    )

    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    h, w = gray.shape[:2]
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        # 文字サイズのフィルタ
        if bh < h * 0.01 or bh > h * 0.25:
            continue
        if bw < w * 0.003 or bw > w * 0.15:
            continue
        valid_contours.append(cnt)

    if not valid_contours:
        return None

    all_points = np.vstack(valid_contours)
    x, y, bw, bh = cv2.boundingRect(all_points)
    return (y, y + bh, x, x + bw)


def detect_bounds_otsu(gray: np.ndarray, min_area: int = 100) -> Optional[tuple]:
    """Otsu二値化で境界検出（白背景用）"""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    h, w = gray.shape[:2]
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        # 文字サイズのフィルタ
        if bh < h * 0.01 or bh > h * 0.25:
            continue
        if bw < w * 0.003 or bw > w * 0.15:
            continue
        valid_contours.append(cnt)

    if not valid_contours:
        return None

    all_points = np.vstack(valid_contours)
    x, y, bw, bh = cv2.boundingRect(all_points)
    return (y, y + bh, x, x + bw)


def detect_bounds_vertical(gray: np.ndarray, min_area: int = 50) -> Optional[tuple]:
    """縦書き用境界検出（フィルタ条件緩和）"""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    h, w = gray.shape[:2]
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        # 縦書き用：高さは大きく（縦長文字）、幅は狭い
        if bh < h * 0.005 or bh > h * 0.30:
            continue
        if bw < w * 0.005 or bw > w * 0.30:
            continue
        valid_contours.append(cnt)

    if not valid_contours:
        return None

    all_points = np.vstack(valid_contours)
    x, y, bw, bh = cv2.boundingRect(all_points)
    return (y, y + bh, x, x + bw)


def detect_bounds_dynamic(gray: np.ndarray, threshold: int = 240, min_area: int = 100) -> Optional[tuple]:
    """動的閾値で境界検出（薄い文字用）"""
    binary = (gray < threshold).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # ノイズ除去: 行ごとのピクセル数が少ない行を除外
    h, w = gray.shape[:2]
    min_pixels_per_row = w * 0.005  # 幅の0.5%以上のピクセルがある行のみ有効
    row_counts = np.sum(binary > 0, axis=1)
    valid_rows = row_counts >= min_pixels_per_row

    if not valid_rows.any():
        return None

    # 有効な行の範囲を取得
    valid_indices = np.where(valid_rows)[0]
    rmin, rmax = valid_indices[0], valid_indices[-1]

    # 列方向も同様に処理
    col_counts = np.sum(binary[rmin:rmax+1] > 0, axis=0)
    min_pixels_per_col = (rmax - rmin + 1) * 0.01
    valid_cols = col_counts >= min_pixels_per_col

    if not valid_cols.any():
        return None

    valid_col_indices = np.where(valid_cols)[0]
    cmin, cmax = valid_col_indices[0], valid_col_indices[-1]

    return (rmin, rmax, cmin, cmax)


def crop_image(image: np.ndarray, bounds: tuple, padding: int = 30) -> np.ndarray:
    """境界に基づいてクロップ"""
    h, w = image.shape[:2]
    rmin, rmax, cmin, cmax = bounds

    # パディング追加
    rmin = max(0, rmin - padding)
    rmax = min(h, rmax + padding + 1)
    cmin = max(0, cmin - padding)
    cmax = min(w, cmax + padding + 1)

    return image[rmin:rmax, cmin:cmax]


def process_white_low_contrast(
    input_dir: Path,
    output_dir: Path,
    files: list[str],
    max_height_ratio: float = 0.40,
    padding: int = 30
) -> list[str]:
    """WHITE_LOW_CONTRAST処理"""
    success = []

    for name in files:
        img_path = input_dir / name
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w = image.shape[:2]

        # 端2%をカット
        margin = int(min(h, w) * 0.02)
        image = image[margin:h-margin, margin:w-margin]
        h, w = image.shape[:2]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Otsu + 動的閾値のマージ
        otsu_bounds = detect_bounds_otsu(gray)
        dynamic_bounds = detect_bounds_dynamic(gray, threshold=240)

        if otsu_bounds is None and dynamic_bounds is None:
            continue

        if otsu_bounds is None:
            bounds = dynamic_bounds
        elif dynamic_bounds is None:
            bounds = otsu_bounds
        else:
            # 動的閾値が過検出の場合はOtsuのみ
            dynamic_height = dynamic_bounds[1] - dynamic_bounds[0]
            if dynamic_height > h * max_height_ratio:
                bounds = otsu_bounds
            else:
                # マージ
                rmin = min(otsu_bounds[0], dynamic_bounds[0])
                rmax = max(otsu_bounds[1], dynamic_bounds[1])
                cmin = min(otsu_bounds[2], dynamic_bounds[2])
                cmax = max(otsu_bounds[3], dynamic_bounds[3])
                bounds = (rmin, rmax, cmin, cmax)

        # 高さチェック
        detected_height = bounds[1] - bounds[0]
        if detected_height > h * max_height_ratio:
            continue
        if detected_height < h * 0.03:
            continue

        result = crop_image(image, bounds, padding)

        # 保存
        cv2.imwrite(str(output_dir / name), result)
        success.append(name)

    return success


def process_gray_background(
    input_dir: Path,
    output_dir: Path,
    files: list[str],
    max_height_ratio: float = 0.45,
    padding: int = 30
) -> list[str]:
    """GRAY_BACKGROUND処理"""
    success = []

    for name in files:
        img_path = input_dir / name
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w = image.shape[:2]

        # 端2%をカット
        margin = int(min(h, w) * 0.02)
        image = image[margin:h-margin, margin:w-margin]
        h, w = image.shape[:2]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Adaptive閾値
        bounds = detect_bounds_adaptive(gray)

        if bounds is None:
            # Otsuも試す
            bounds = detect_bounds_otsu(gray)
            if bounds is None:
                continue

        # 高さチェック（緩和）
        detected_height = bounds[1] - bounds[0]
        if detected_height > h * max_height_ratio:
            continue
        if detected_height < h * 0.02:  # 最小高さチェックを緩和
            continue

        result = crop_image(image, bounds, padding)

        # 保存
        cv2.imwrite(str(output_dir / name), result)
        success.append(name)

    return success


def process_white_high_contrast(
    input_dir: Path,
    output_dir: Path,
    files: list[str],
    max_height_ratio: float = 0.50,
    padding: int = 30
) -> list[str]:
    """WHITE_HIGH_CONTRAST処理"""
    success = []

    for name in files:
        img_path = input_dir / name
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w = image.shape[:2]

        # 端2%をカット
        margin = int(min(h, w) * 0.02)
        image = image[margin:h-margin, margin:w-margin]
        h, w = image.shape[:2]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Otsu
        bounds = detect_bounds_otsu(gray)

        if bounds is None:
            # 動的閾値も試す
            bounds = detect_bounds_dynamic(gray, threshold=230)
            if bounds is None:
                continue

        # 高さチェック（緩和）
        detected_height = bounds[1] - bounds[0]
        if detected_height > h * max_height_ratio:
            continue
        if detected_height < h * 0.02:  # 最小高さチェックを緩和
            continue

        result = crop_image(image, bounds, padding)

        # 保存
        cv2.imwrite(str(output_dir / name), result)
        success.append(name)

    return success


def process_vertical(
    input_dir: Path,
    output_dir: Path,
    files: list[str],
    max_width_ratio: float = 0.55,
    padding: int = 30
) -> list[str]:
    """VERTICAL処理"""
    success = []

    for name in files:
        img_path = input_dir / name
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w = image.shape[:2]

        # 端2%をカット
        margin = int(min(h, w) * 0.02)
        image = image[margin:h-margin, margin:w-margin]
        h, w = image.shape[:2]

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 縦書き専用の検出関数を使用
        bounds = detect_bounds_vertical(gray)

        if bounds is None:
            # 動的閾値も試す
            bounds = detect_bounds_dynamic(gray, threshold=240)
            if bounds is None:
                continue

        # 幅チェック（縦書きは幅で判定、さらに緩和）
        detected_width = bounds[3] - bounds[2]
        if detected_width > w * max_width_ratio:
            continue
        if detected_width < w * 0.005:  # 最小幅チェックをさらに緩和
            continue

        result = crop_image(image, bounds, padding)

        # 保存
        cv2.imwrite(str(output_dir / name), result)
        success.append(name)

    return success


def process_all_categories(input_dir: Path, output_dir: Path) -> dict[str, list[str]]:
    """全カテゴリを処理"""
    output_dir.mkdir(exist_ok=True)

    # 分類
    categories = classify_all_images(input_dir)

    print("=== カテゴリ別枚数 ===")
    for cat, files in categories.items():
        print(f"{cat}: {len(files)}枚")

    results = {}

    # WHITE_LOW_CONTRAST
    print("\n処理中: WHITE_LOW_CONTRAST...")
    results['WHITE_LOW_CONTRAST'] = process_white_low_contrast(
        input_dir, output_dir, categories['WHITE_LOW_CONTRAST'],
        max_height_ratio=0.40
    )
    print(f"  成功: {len(results['WHITE_LOW_CONTRAST'])}枚")

    # GRAY_BACKGROUND
    print("\n処理中: GRAY_BACKGROUND...")
    results['GRAY_BACKGROUND'] = process_gray_background(
        input_dir, output_dir, categories['GRAY_BACKGROUND'],
        max_height_ratio=0.40
    )
    print(f"  成功: {len(results['GRAY_BACKGROUND'])}枚")

    # WHITE_HIGH_CONTRAST
    print("\n処理中: WHITE_HIGH_CONTRAST...")
    results['WHITE_HIGH_CONTRAST'] = process_white_high_contrast(
        input_dir, output_dir, categories['WHITE_HIGH_CONTRAST'],
        max_height_ratio=0.45
    )
    print(f"  成功: {len(results['WHITE_HIGH_CONTRAST'])}枚")

    # VERTICAL
    print("\n処理中: VERTICAL...")
    results['VERTICAL'] = process_vertical(
        input_dir, output_dir, categories['VERTICAL'],
        max_width_ratio=0.40
    )
    print(f"  成功: {len(results['VERTICAL'])}枚")

    # 統合
    all_success = []
    for files in results.values():
        all_success.extend(files)

    print(f"\n=== 合計: {len(all_success)}枚 ===")

    # リスト保存
    with open(output_dir / 'cropped_files.txt', 'w') as f:
        for name in sorted(all_success):
            f.write(name + '\n')

    return results


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='カテゴリ別の手書き画像クロップ処理',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
カテゴリ説明:
  WHITE_LOW_CONTRAST   白背景・薄い文字（鉛筆書きなど）
  GRAY_BACKGROUND      グレー背景（スキャン画像など）
  WHITE_HIGH_CONTRAST  白背景・濃い文字（ペン書きなど）
  VERTICAL             縦書き（縦長画像）

出力:
  - クロップされた画像（出力ディレクトリ内）
  - cropped_files.txt（成功したファイル名リスト）
'''
    )
    parser.add_argument(
        'input_dir',
        nargs='?',
        default='datasets/appen_test_200',
        help='入力画像ディレクトリ（デフォルト: datasets/appen_test_200）'
    )
    parser.add_argument(
        'output_dir',
        nargs='?',
        default='datasets/test_deskew_output',
        help='出力ディレクトリ（デフォルト: datasets/test_deskew_output）'
    )
    parser.add_argument(
        '--classify-only',
        action='store_true',
        help='分類のみ行い、クロップは行わない'
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        print(f"エラー: 入力ディレクトリが存在しません: {input_dir}")
        return 1

    if args.classify_only:
        # 分類のみ
        categories = classify_all_images(input_dir)
        print("=== カテゴリ別枚数 ===")
        total = 0
        for cat, files in categories.items():
            print(f"{cat}: {len(files)}枚")
            total += len(files)
        print(f"\n合計: {total}枚")

        # カテゴリ別ファイルリストを保存
        output_dir.mkdir(exist_ok=True)
        for cat, files in categories.items():
            list_file = output_dir / f'category_{cat.lower()}.txt'
            with open(list_file, 'w') as f:
                for name in sorted(files):
                    f.write(name + '\n')
            print(f"  {list_file} に保存")
    else:
        # 全処理
        process_all_categories(input_dir, output_dir)

    return 0


if __name__ == '__main__':
    exit(main())
