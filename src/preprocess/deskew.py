"""
手書き日本語画像の傾き補正スクリプト

手書き文字画像の傾きを補正し、文字領域を抽出する。

## 段階的処理フロー

### Step 1: 画像分類
画像を4つのカテゴリに分類:
- VERTICAL: 縦書き（縦長画像、高さ > 幅 * 1.2）
- WHITE_HIGH_CONTRAST: 白背景 + 高コントラスト（濃い文字）
- WHITE_LOW_CONTRAST: 白背景 + 低コントラスト（薄い文字）
- GRAY_BACKGROUND: グレー背景

### Step 2: カテゴリ別処理
各カテゴリに最適なパラメータで処理:
- VERTICAL: 回転せず縦のままクロップ
- WHITE_HIGH_CONTRAST: Otsu二値化のみ（ノイズに強い）
- WHITE_LOW_CONTRAST: Otsu + 動的閾値240のマージ
- GRAY_BACKGROUND: Adaptive閾値のみ

### Step 3: 1行判定
クロップ後の高さ比率で判定:
- 3-25%: 1行手書きとして成功
- それ以外: 元画像を返す（複数行または検出失敗）

Usage:
    uv run python src/utils/image_deskew.py
    uv run python src/utils/image_deskew.py --input datasets/appen_test_200 --output datasets/appen_test_200_corrected
"""

import argparse
from enum import Enum
from pathlib import Path

import cv2
import numpy as np


class ImageCategory(Enum):
    """画像のカテゴリ分類"""
    VERTICAL = "vertical"                    # 縦書き（縦長画像）
    WHITE_HIGH_CONTRAST = "white_high"       # 白背景 + 高コントラスト
    WHITE_LOW_CONTRAST = "white_low"         # 白背景 + 低コントラスト
    GRAY_BACKGROUND = "gray"                 # グレー背景


def get_text_region_and_angle(binary_image: np.ndarray, min_area: int = 100,
                               edge_margin_ratio: float = 0.05) -> tuple[float, tuple]:
    """
    二値化画像から文字領域の角度を線形回帰で検出する

    Args:
        binary_image: 二値化済み画像（白テキスト）
        min_area: 最小輪郭面積
        edge_margin_ratio: 除外する画像端の比率（定規などのノイズ対策）

    Returns:
        (角度, None) のタプル。角度は水平からの偏差（度）
    """
    h, w = binary_image.shape[:2]

    # 端のマージンを計算（定規などを除外）
    left_margin = int(w * edge_margin_ratio)
    right_margin = int(w * (1 - edge_margin_ratio))
    top_margin = int(h * edge_margin_ratio)
    bottom_margin = int(h * (1 - edge_margin_ratio))

    # 全ての輪郭を取得
    contours, _ = cv2.findContours(
        binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return 0.0, None

    # 有効な輪郭の重心を収集
    centroids = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        # バウンディングボックスを取得
        x, y, bw, bh = cv2.boundingRect(contour)
        cx = x + bw / 2
        cy = y + bh / 2

        # 画像端にある輪郭を除外（定規などのノイズ対策）
        if cx < left_margin or cx > right_margin:
            continue
        if cy < top_margin or cy > bottom_margin:
            continue

        # 縦長すぎる輪郭を除外（アスペクト比が4以上）- 定規などを除外
        aspect_ratio = bh / (bw + 1e-10)
        if aspect_ratio > 4:
            continue

        # 横長すぎる輪郭も除外（アスペクト比が0.25以下）
        if aspect_ratio < 0.25:
            continue

        centroids.append((cx, cy))

    if len(centroids) < 3:
        return 0.0, None

    # 線形回帰で傾きを計算
    centroids = np.array(centroids)
    x_coords = centroids[:, 0]
    y_coords = centroids[:, 1]

    # numpy polyfit で線形回帰
    try:
        slope, _ = np.polyfit(x_coords, y_coords, 1)
        angle = np.degrees(np.arctan(slope))
    except (np.linalg.LinAlgError, ValueError):
        return 0.0, None

    # 角度を -45 ~ 45 度の範囲に制限
    if angle > 45:
        angle = angle - 90
    elif angle < -45:
        angle = angle + 90

    return angle, None


def rotate_image(image: np.ndarray, angle: float,
                 background_color: tuple = (255, 255, 255)) -> np.ndarray:
    """
    画像を指定角度で回転させる（中心回転）

    Args:
        image: 入力画像
        angle: 回転角度（度）。正の値で反時計回り
        background_color: 背景色

    Returns:
        回転後の画像
    """
    if abs(angle) < 0.5:  # 0.5度未満は回転しない
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    # 回転行列を取得
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # 回転後の画像サイズを計算（はみ出し防止）
    cos = np.abs(rotation_matrix[0, 0])
    sin = np.abs(rotation_matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    # 回転行列の平行移動成分を調整
    rotation_matrix[0, 2] += (new_w - w) / 2
    rotation_matrix[1, 2] += (new_h - h) / 2

    # 回転を適用
    rotated = cv2.warpAffine(
        image, rotation_matrix, (new_w, new_h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=background_color
    )

    return rotated


def classify_image(gray: np.ndarray) -> dict:
    """
    画像の特性を自動判定する

    Args:
        gray: グレースケール画像

    Returns:
        画像特性の辞書:
        - is_white_bg: 白背景かどうか
        - is_high_contrast: 高コントラストかどうか
        - bg_brightness: 背景輝度
        - dynamic_threshold: 動的閾値
        - use_dynamic_threshold: 動的閾値を使用するか
    """
    # 背景輝度（画像の95パーセンタイル = 最も明るい部分）
    bg_brightness = np.percentile(gray, 95)
    is_white_bg = bg_brightness > 245  # 245以上を白背景とする

    # コントラスト（標準偏差）
    contrast = np.std(gray)
    is_high_contrast = contrast > 30

    # 動的閾値を計算（背景より十分暗いピクセルのみ検出）
    if is_white_bg:
        # 白背景: 固定値240（薄い汚れを拾わないよう厳しめ）
        dynamic_threshold = 240
    else:
        # グレー背景: 文字は1パーセンタイル付近の非常に暗い部分
        # 閾値は文字(1%tile)に近い値を設定し、背景のグラデーションを拾わない
        dark_value = np.percentile(gray, 1)
        # 文字より少し明るい値を閾値にする（文字+20〜30程度）
        dynamic_threshold = int(dark_value + 25)

    # カテゴリ判定（縦書きは別途判定するため、ここでは背景・コントラストのみ）
    if not is_white_bg:
        category = ImageCategory.GRAY_BACKGROUND
    elif is_high_contrast:
        category = ImageCategory.WHITE_HIGH_CONTRAST
    else:
        category = ImageCategory.WHITE_LOW_CONTRAST

    return {
        'category': category,
        'is_white_bg': is_white_bg,
        'is_high_contrast': is_high_contrast,
        'bg_brightness': bg_brightness,
        'contrast': contrast,
        'dynamic_threshold': dynamic_threshold,
        'use_dynamic_threshold': not is_high_contrast  # 低コントラストの場合のみ
    }


def detect_bounds_otsu(gray: np.ndarray, min_area: int = None, use_adaptive: bool = False) -> tuple:
    """二値化で文字領域の境界を検出（グラデーション背景対応）

    Args:
        gray: グレースケール画像
        min_area: 最小輪郭面積（Noneの場合は画像サイズに応じて自動設定）
        use_adaptive: 適応的閾値を使用するか（グレー背景向け）
    """
    h, w = gray.shape[:2]

    # min_areaを画像サイズに応じて動的に設定
    # 小さい画像では小さい値、大きい画像では大きい値を使用
    # 薄い手書き文字は輪郭が小さくなりやすいため、全体的に閾値を下げる
    if min_area is None:
        image_area = h * w
        if image_area < 100000:  # 小さい画像（例: 700x110 = 77,000）
            min_area = 10
        elif image_area < 500000:
            min_area = 20
        else:
            min_area = 30

    if use_adaptive:
        # 適応的閾値（グレー背景やグラデーション背景向け）
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 31, 10)
    else:
        # 白い余白（回転で追加された部分など）を除外してOtsu計算
        non_white_mask = gray < 250
        if non_white_mask.sum() > 0:
            non_white_pixels = gray[non_white_mask]
            otsu_thresh, _ = cv2.threshold(non_white_pixels, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            binary = (gray < otsu_thresh).astype(np.uint8) * 255
        else:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # ノイズ除去（小さい画像では軽めに）
    if h * w < 100000:
        kernel = np.ones((2, 2), np.uint8)
    else:
        kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # 輪郭検出してマスク作成（文字らしいサイズでフィルタリング）
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(binary)
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        _, _, bw, bh = cv2.boundingRect(contour)
        # 文字らしいサイズ（高さ: 画像の0.3%~50%、幅: 画像の0.2%~15%）
        # 薄い手書き文字は輪郭が小さくなりやすいため、下限を緩和
        if bh < h * 0.003 or bh > h * 0.50:
            continue
        if bw < w * 0.002 or bw > w * 0.15:
            continue
        cv2.drawContours(mask, [contour], -1, 255, -1)

    # 境界を取得
    rows = np.any(mask > 0, axis=1)
    cols = np.any(mask > 0, axis=0)

    if not rows.any() or not cols.any():
        # フォールバック: サイズフィルタなしで再試行
        mask = np.zeros_like(binary)
        for contour in contours:
            if cv2.contourArea(contour) >= min_area:
                cv2.drawContours(mask, [contour], -1, 255, -1)
        rows = np.any(mask > 0, axis=1)
        cols = np.any(mask > 0, axis=0)
        if not rows.any() or not cols.any():
            return None

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return (rmin, rmax, cmin, cmax)


def detect_bounds_fixed(gray: np.ndarray, threshold: int = 240, min_area: int = 100) -> tuple:
    """固定閾値で文字領域の境界を検出（薄い文字対応）"""
    binary = (gray < threshold).astype(np.uint8) * 255

    # ノイズ除去（小さな点を除去）- 薄い文字を保持するため軽めに
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # 輪郭検出してマスク作成（小さすぎる輪郭を除外）
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(binary)
    for contour in contours:
        if cv2.contourArea(contour) >= min_area:
            cv2.drawContours(mask, [contour], -1, 255, -1)

    rows = np.any(mask > 0, axis=1)
    cols = np.any(mask > 0, axis=0)

    if not rows.any() or not cols.any():
        return None

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return (rmin, rmax, cmin, cmax)


def crop_text_region(image: np.ndarray, padding: int = 30, debug: bool = False,
                     original_props: dict = None) -> np.ndarray:
    """
    文字領域を矩形で抽出する（カテゴリ別処理）

    カテゴリ別の処理:
    - WHITE_HIGH_CONTRAST: Otsu二値化のみ
    - WHITE_LOW_CONTRAST: Otsu + 動的閾値のマージ
    - GRAY_BACKGROUND: Adaptive閾値のみ

    Args:
        image: 入力画像
        padding: 文字領域周囲に追加する余白（ピクセル）
        debug: デバッグ出力を有効にする
        original_props: 回転前の画像特性（回転後に再分類すると背景が変わるため）

    Returns:
        クロップ後の画像
    """
    h, w = image.shape[:2]
    if debug:
        print(f"[crop] Input size: {w}x{h}")

    # グレースケールに変換
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 画像特性を使用（回転前の特性が渡された場合はそれを優先）
    if original_props is not None:
        props = original_props
    else:
        props = classify_image(gray)

    category = props['category']
    if debug:
        print(f"[crop] Category: {category.value}, bg={props['bg_brightness']:.1f}, "
              f"contrast={props['contrast']:.1f}")

    # カテゴリ別の境界検出
    bounds = None

    if category == ImageCategory.GRAY_BACKGROUND:
        # グレー背景: Adaptive閾値のみ
        bounds = detect_bounds_otsu(gray, use_adaptive=True)
        if debug:
            print(f"[crop] Adaptive bounds: {bounds}")

    elif category == ImageCategory.WHITE_HIGH_CONTRAST:
        # 白背景 + 高コントラスト: Otsuのみ
        bounds = detect_bounds_otsu(gray, use_adaptive=False)
        if debug:
            print(f"[crop] Otsu bounds: {bounds}")

    elif category == ImageCategory.WHITE_LOW_CONTRAST:
        # 白背景 + 低コントラスト: Otsu + 動的閾値のマージ
        otsu_bounds = detect_bounds_otsu(gray, use_adaptive=False)
        dynamic_bounds = detect_bounds_fixed(gray, threshold=props['dynamic_threshold'])
        if debug:
            print(f"[crop] Otsu bounds: {otsu_bounds}")
            print(f"[crop] Dynamic bounds (threshold={props['dynamic_threshold']}): {dynamic_bounds}")

        if otsu_bounds is None and dynamic_bounds is None:
            bounds = None
        elif otsu_bounds is None:
            bounds = dynamic_bounds
        elif dynamic_bounds is None:
            bounds = otsu_bounds
        else:
            # 動的閾値が過検出（高さ25%超）した場合はOtsuの結果のみを使用
            dynamic_height = dynamic_bounds[1] - dynamic_bounds[0]
            if dynamic_height > h * 0.25:
                if debug:
                    print(f"[crop] Dynamic over-detected ({dynamic_height/h*100:.1f}%), using Otsu only")
                bounds = otsu_bounds
            else:
                # マージ: 最小のmin、最大のmaxを採用
                rmin = min(otsu_bounds[0], dynamic_bounds[0])
                rmax = max(otsu_bounds[1], dynamic_bounds[1])
                cmin = min(otsu_bounds[2], dynamic_bounds[2])
                cmax = max(otsu_bounds[3], dynamic_bounds[3])
                bounds = (rmin, rmax, cmin, cmax)

    # 境界が検出できなかった場合
    if bounds is None:
        if debug:
            print("[crop] No content found, returning original")
        return image

    rmin, rmax, cmin, cmax = bounds
    if debug:
        print(f"[crop] Final bounds: x={cmin}~{cmax}, y={rmin}~{rmax}")

    # 1行判定: 高さ比率で過検出/検出漏れをチェック
    detected_height = rmax - rmin
    detected_width = cmax - cmin
    height_ratio = detected_height / h
    width_ratio = detected_width / w

    # 小さい画像（既にクロップ済み）の場合は1行判定をスキップ
    # 高さ200px未満または画像面積10万px未満の場合
    is_already_cropped = h < 200 or (h * w < 100000)

    # 1行手書きとして妥当な高さ比率: 3%〜25%（大きい画像の場合のみチェック）
    if not is_already_cropped and height_ratio > 0.25 and width_ratio > 0.85:
        if debug:
            print(f"[crop] Over-detection (h={height_ratio*100:.1f}%, w={width_ratio*100:.1f}%), returning original")
        return image

    if height_ratio < 0.03:
        if debug:
            print(f"[crop] Under-detection (h={height_ratio*100:.1f}%), returning original")
        return image

    # パディングを追加
    rmin = max(0, rmin - padding)
    rmax = min(h, rmax + padding + 1)
    cmin = max(0, cmin - padding)
    cmax = min(w, cmax + padding + 1)

    if debug:
        print(f"[crop] Final crop: x={cmin}~{cmax}, y={rmin}~{rmax}")
        print(f"[crop] Output size: {cmax-cmin}x{rmax-rmin}")

    return image[rmin:rmax, cmin:cmax]


def crop_text_region_vertical(image: np.ndarray, padding: int = 30, debug: bool = False,
                               props: dict = None) -> np.ndarray:
    """
    縦書き画像の文字領域を抽出する

    縦書きの場合、横幅で1行判定を行う（幅が3-25%）

    Args:
        image: 入力画像
        padding: 文字領域周囲に追加する余白（ピクセル）
        debug: デバッグ出力を有効にする
        props: 画像特性

    Returns:
        クロップ後の画像
    """
    h, w = image.shape[:2]
    if debug:
        print(f"[crop_vertical] Input size: {w}x{h}")

    # グレースケールに変換
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    if props is None:
        props = classify_image(gray)

    if debug:
        print(f"[crop_vertical] bg={props['bg_brightness']:.1f}, contrast={props['contrast']:.1f}")

    # 背景に応じた境界検出
    if props['is_white_bg']:
        bounds = detect_bounds_otsu(gray, use_adaptive=False)
    else:
        bounds = detect_bounds_otsu(gray, use_adaptive=True)

    if bounds is None:
        if debug:
            print("[crop_vertical] No content found, returning original")
        return image

    rmin, rmax, cmin, cmax = bounds
    if debug:
        print(f"[crop_vertical] Bounds: x={cmin}~{cmax}, y={rmin}~{rmax}")

    # 縦書き1行判定: 横幅で判定（幅が3-30%）
    detected_width = cmax - cmin
    detected_height = rmax - rmin
    width_ratio = detected_width / w
    height_ratio = detected_height / h

    if width_ratio > 0.30 and height_ratio > 0.85:
        if debug:
            print(f"[crop_vertical] Over-detection (w={width_ratio*100:.1f}%, h={height_ratio*100:.1f}%), returning original")
        return image

    if width_ratio < 0.03:
        if debug:
            print(f"[crop_vertical] Under-detection (w={width_ratio*100:.1f}%), returning original")
        return image

    # パディングを追加
    rmin = max(0, rmin - padding)
    rmax = min(h, rmax + padding + 1)
    cmin = max(0, cmin - padding)
    cmax = min(w, cmax + padding + 1)

    if debug:
        print(f"[crop_vertical] Final crop: x={cmin}~{cmax}, y={rmin}~{rmax}")
        print(f"[crop_vertical] Output size: {cmax-cmin}x{rmax-rmin}")

    return image[rmin:rmax, cmin:cmax]


def remove_edge_noise(image: np.ndarray, edge_margin_ratio: float = 0.05) -> np.ndarray:
    """
    画像の端をクロップしてノイズ（定規など）を除去する

    Args:
        image: 入力画像
        edge_margin_ratio: 除去する端の比率

    Returns:
        端をクロップした画像
    """
    h, w = image.shape[:2]
    left = int(w * edge_margin_ratio)
    right = int(w * (1 - edge_margin_ratio))
    top = int(h * edge_margin_ratio)
    bottom = int(h * (1 - edge_margin_ratio))

    return image[top:bottom, left:right]


def deskew_image(image_path: Path, output_path: Path,
                 angle_threshold: float = 1.0,
                 padding: int = 30,
                 edge_margin_ratio: float = 0.02) -> bool:
    """
    画像の傾きを補正し、文字領域を抽出する（段階的処理）

    処理フロー:
    1. 画像分類（縦書き/白背景高コントラスト/白背景低コントラスト/グレー背景）
    2. カテゴリ別の前処理（縦書きは回転しない）
    3. 文字領域検出・クロップ
    4. 1行判定

    Args:
        image_path: 入力画像パス
        output_path: 出力画像パス
        angle_threshold: この角度以上で回転を適用（度）
        padding: 文字領域周囲の余白（ピクセル）
        edge_margin_ratio: 最初に除去する端の比率

    Returns:
        処理が成功したかどうか
    """
    # === Step 1: 画像読み込みと分類 ===
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Error: Cannot read image: {image_path}")
        return False

    h, w = image.shape[:2]

    # 縦書き判定: 高さ > 幅 * 1.2
    is_vertical = h > w * 1.2

    # 小さい画像（既にクロップ済み）の判定
    # 高さ200px未満または画像面積10万px未満の場合はエッジノイズ除去をスキップ
    is_already_cropped = h < 200 or (h * w < 100000)

    if is_vertical:
        category = ImageCategory.VERTICAL
    else:
        # 端をクロップしてノイズ除去（定規など）- 大きい画像のみ
        if not is_already_cropped:
            image = remove_edge_noise(image, edge_margin_ratio)
            h, w = image.shape[:2]

        # グレースケールに変換して分類
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        props = classify_image(gray)
        category = props['category']

    print(f"[deskew] {image_path.name}: category={category.value}", end="")
    if category != ImageCategory.VERTICAL:
        print(f", bg={props['bg_brightness']:.1f}, contrast={props['contrast']:.1f}")
    else:
        print()

    # === Step 2: カテゴリ別の前処理 ===
    if category == ImageCategory.VERTICAL:
        # 縦書き: 回転せず、縦のままクロップ
        image = remove_edge_noise(image, edge_margin_ratio)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        props = classify_image(gray)
        # 縦書きのカテゴリを保持しつつ、背景情報を使う
        props['category'] = ImageCategory.VERTICAL
        result = image
        # 縦書きは傾き補正をスキップ
    else:
        # 横書き: 傾き検出と回転
        # 二値化（傾き検出用）
        if props['is_white_bg']:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY_INV, 31, 10)

        # モルフォロジー処理でノイズ除去
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 傾き角度を検出
        angle, _ = get_text_region_and_angle(binary, min_area=100, edge_margin_ratio=0)

        # 回転補正
        if abs(angle) >= angle_threshold:
            result = rotate_image(image, angle)
        else:
            result = image

    # === Step 3: 文字領域検出・クロップ ===
    # 縦書きの場合は専用処理
    if category == ImageCategory.VERTICAL:
        result = crop_text_region_vertical(result, padding=padding, debug=True, props=props)
    else:
        result = crop_text_region(result, padding=padding, debug=True, original_props=props)

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), result)

    return True


def process_all_images(input_dir: Path, output_dir: Path,
                       angle_threshold: float = 1.0,
                       padding: int = 30) -> dict:
    """
    ディレクトリ内の全画像を一括処理する
    """
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "failed_files": []
    }

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    image_files = [
        f for f in input_dir.iterdir()
        if f.suffix.lower() in image_extensions
    ]

    stats["total"] = len(image_files)

    print(f"Processing {len(image_files)} images...")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Angle threshold: {angle_threshold}°")
    print(f"Padding: {padding}px")
    print("-" * 50)

    for i, image_path in enumerate(sorted(image_files), 1):
        output_path = output_dir / image_path.name

        success = deskew_image(
            image_path, output_path,
            angle_threshold=angle_threshold,
            padding=padding
        )

        if success:
            stats["success"] += 1
            print(f"[{i}/{len(image_files)}] OK: {image_path.name}")
        else:
            stats["failed"] += 1
            stats["failed_files"].append(str(image_path))
            print(f"[{i}/{len(image_files)}] FAILED: {image_path.name}")

    print("-" * 50)
    print(f"Complete: {stats['success']}/{stats['total']} succeeded")
    if stats["failed"] > 0:
        print(f"Failed files: {stats['failed_files']}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="手書き日本語画像の傾き補正"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("datasets/appen_test_200"),
        help="入力ディレクトリ (default: datasets/appen_test_200)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("datasets/appen_test_200_corrected"),
        help="出力ディレクトリ (default: datasets/appen_test_200_corrected)"
    )
    parser.add_argument(
        "--single", "-s",
        type=Path,
        help="単一ファイルを処理する場合のファイルパス"
    )
    parser.add_argument(
        "--angle-threshold", "-a",
        type=float,
        default=1.0,
        help="回転を適用する最小角度（度）(default: 1.0)"
    )
    parser.add_argument(
        "--padding", "-p",
        type=int,
        default=30,
        help="文字領域周囲の余白（ピクセル）(default: 30)"
    )

    args = parser.parse_args()

    if args.single:
        output_path = args.output / args.single.name
        success = deskew_image(
            args.single, output_path,
            angle_threshold=args.angle_threshold,
            padding=args.padding
        )
        return 0 if success else 1
    else:
        if not args.input.exists():
            print(f"Error: Input directory not found: {args.input}")
            return 1

        stats = process_all_images(
            args.input, args.output,
            angle_threshold=args.angle_threshold,
            padding=args.padding
        )
        return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
