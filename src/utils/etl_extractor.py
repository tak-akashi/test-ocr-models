#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETL8G / ETL9G extractor
- (Optional) download zip from provided URL
- extract images to PNG
- build labels.csv with unicode char + JIS code metadata

Tested logic is based on public examples for ETL8G/ETL9G parsing.
You must comply with ETLCDB terms of use.

変更内容

  1. 解凍済みディレクトリからの読み込み対応
    - iter_records_from_file():
  ディスク上のETLファイルから直接レコードを読み込む関数を追加
    - extract_dataset_from_directory():
  ディレクトリ内のETLファイルを処理する関数を追加
  2. ETL8B/ETL9Bのサポート追加
    - B型（バイナリ）データセットの仕様を追加
    - decode_record()でG型とB型の異なる画像フォーマットを自動判別
  3. 自動検出機能
    - detect_source_type(): ZIPファイルかディレクトリかを自動検出
    - extract_auto(): ソースタイプに応じて適切な抽出関数を呼び出し
  4. CLIの拡張
    - --data-dir: データソースディレクトリを指定
    - --datasets: 処理するデータセットを選択（ETL8G, ETL9G, ETL8B, ETL9B, all）
    - --flatten/--no-flatten: 出力構造の制御

  使用例

  # assets/etlcdbから全データセットを抽出
  uv run python -m src.utils.etl_extractor --data-dir assets/etlcdb --out-dir assets/etlcdb/extracted

  # 特定のデータセットのみ
  uv run python -m src.utils.etl_extractor --data-dir assets/etlcdb --datasets ETL8G
  ETL9G
"""

from __future__ import annotations

import os
import io
import csv
import sys
import struct
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple, List

import numpy as np
from PIL import Image

try:
    import requests
except ImportError:
    requests = None

from zipfile import ZipFile
from tqdm import tqdm


# -----------------------------
# Config
# -----------------------------

@dataclass
class DatasetSpec:
    name: str            # "ETL8G" or "ETL9G"
    zip_filename: str    # "ETL8G.zip"
    record_size: int     # 8199 for G-type
    img_size: Tuple[int, int]  # (128, 127)
    unpack_fmt: str      # struct format string
    img_data_index: int  # index in unpacked tuple that holds packed bitmap
    # label code index:
    label_index: int = 1


ETL8G = DatasetSpec(
    name="ETL8G",
    zip_filename="ETL8G.zip",
    record_size=8199,
    img_size=(128, 127),
    unpack_fmt=">HH8sIBBBBHHHHBB30x8128s11x",
    img_data_index=14,
)

ETL9G = DatasetSpec(
    name="ETL9G",
    zip_filename="ETL9G.zip",
    record_size=8199,
    img_size=(128, 127),
    unpack_fmt=">HH8sIBBBBHHHHBB30x8128s11x",
    img_data_index=14,
)

# ETL8B and ETL9B use a different format (binary, 64x63 pixels)
ETL8B = DatasetSpec(
    name="ETL8B",
    zip_filename="ETL8B.zip",
    record_size=512,
    img_size=(64, 63),
    unpack_fmt=">HH4sI4B4H2B30x504s",  # ETL8B/9B format
    img_data_index=12,
)

ETL9B = DatasetSpec(
    name="ETL9B",
    zip_filename="ETL9B.zip",
    record_size=576,
    img_size=(64, 63),
    unpack_fmt=">HH8sI4B4H2B34x504s8x",  # ETL9B format (568 + 8x padding = 576)
    img_data_index=12,
)

# Mapping from directory name to spec
DATASET_SPECS = {
    "ETL8G": ETL8G,
    "ETL9G": ETL9G,
    "ETL8B": ETL8B,
    "ETL9B": ETL9B,
}


# -----------------------------
# Download (optional)
# -----------------------------

def download_zip(url: str, out_path: Path, password: Optional[str] = None) -> None:
    """
    Try to download ETL zip.
    The official site provides a password-protected download page.
    Auth method may vary; this function attempts a simple HTTP basic auth if password is given.
    If this doesn't work for your link, download manually and place the zip into data_dir.
    """
    if requests is None:
        raise RuntimeError("requests is not installed. pip install requests")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    auth = None
    if password:
        # Some sites use basic auth; if not, this will just be ignored by the server.
        auth = requests.auth.HTTPBasicAuth("", password)

    with requests.get(url, stream=True, auth=auth, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", "0") or "0")
        with open(out_path, "wb") as f, tqdm(
            total=total if total > 0 else None,
            unit="B", unit_scale=True, desc=f"Downloading {out_path.name}"
        ) as pbar:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


# -----------------------------
# JIS code → Unicode
# -----------------------------

def jis0208_to_unicode(jis_code: int) -> str:
    """
    Convert a JIS X 0208 code (as an integer) to a Unicode character
    using ISO-2022-JP escape sequence trick.
    Widely used in ETL extraction examples.
    """
    try:
        seq = b"\x1b$B" + jis_code.to_bytes(2, "big") + b"\x1b(B"
        ch = seq.decode("iso-2022-jp")
        return ch
    except Exception:
        return f"null_{jis_code:04X}"


# -----------------------------
# Core parsing
# -----------------------------

def iter_records_from_member(zf: ZipFile, member_name: str, spec: DatasetSpec) -> Iterator[bytes]:
    """Iterate records from a ZipFile member."""
    with zf.open(member_name) as f:
        while True:
            s = f.read(spec.record_size)
            if not s or len(s) < spec.record_size:
                break
            yield s


def iter_records_from_file(file_path: Path, spec: DatasetSpec) -> Iterator[bytes]:
    """Iterate records from an uncompressed ETL file on disk."""
    with open(file_path, "rb") as f:
        while True:
            s = f.read(spec.record_size)
            if not s or len(s) < spec.record_size:
                break
            yield s


def decode_record(record_bytes: bytes, spec: DatasetSpec) -> Tuple[Image.Image, int]:
    """
    Returns (image, jis_code_int)
    """
    r = struct.unpack(spec.unpack_fmt, record_bytes)
    jis_code = int(r[spec.label_index])

    if "G" in spec.name:
        # G-type: Packed 4-bit grayscale bitmap (ETL8G, ETL9G)
        # Same approach used in public ETL8G/9G code samples.
        img_f = Image.frombytes("F", spec.img_size, r[spec.img_data_index], "bit", (4, 0))
        img_l = img_f.convert("L")
        # Convert 0..15 to 0..255 and invert (common ETL handling)
        img_l = img_l.point(lambda x: 255 - (x << 4))
    else:
        # B-type: 1-bit binary bitmap (ETL8B, ETL9B)
        # Each byte contains 8 pixels
        img_data = r[spec.img_data_index]
        img_f = Image.frombytes("1", spec.img_size, img_data, "raw", "1;I")
        img_l = img_f.convert("L")

    return img_l, jis_code


def _process_records(
    record_iterator: Iterator[bytes],
    spec: DatasetSpec,
    out_dir: Path,
    source_name: str,
    global_idx: int,
    flatten: bool,
    labels: List[dict],
) -> int:
    """
    Process records from an iterator and save images.
    Returns the updated global_idx.
    """
    for rec in record_iterator:
        global_idx += 1
        img, jis_code = decode_record(rec, spec)
        ch = jis0208_to_unicode(jis_code)

        # File naming
        safe_char = ch
        # Avoid path issues
        if safe_char.startswith("null_"):
            safe_char = "UNK"
        safe_char = safe_char.replace("/", "_")

        if flatten:
            img_rel = Path("images") / spec.name / f"{spec.name}_{global_idx:07d}.png"
        else:
            # group by char label
            img_rel = Path("images") / spec.name / safe_char / f"{spec.name}_{global_idx:07d}.png"
            (out_dir / img_rel.parent).mkdir(parents=True, exist_ok=True)

        img_abs = out_dir / img_rel
        img_abs.parent.mkdir(parents=True, exist_ok=True)
        img.save(img_abs)

        labels.append({
            "dataset": spec.name,
            "source_member": source_name,
            "index": global_idx,
            "label_char": ch,
            "label_jis_hex": f"0x{jis_code:04X}",
            "label_jis_int": jis_code,
            "image_path": str(img_rel).replace("\\", "/"),
            "width": spec.img_size[0],
            "height": spec.img_size[1],
        })

    return global_idx


def extract_dataset(
    zip_path: Path,
    out_dir: Path,
    spec: DatasetSpec,
    flatten: bool = True,
) -> List[dict]:
    """
    Extract all records from ETL8G/ETL9G zip.
    Returns list of label dicts for CSV.
    """
    labels: List[dict] = []
    images_dir = out_dir / "images" / spec.name
    images_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path) as zf:
        # Many ETL zips contain multiple members like ETL8G_01, ETL8G_02...
        members = [n for n in zf.namelist() if "_" in Path(n).name]
        members.sort()

        global_idx = 0
        for m in members:
            global_idx = _process_records(
                iter_records_from_member(zf, m, spec),
                spec, out_dir, m, global_idx, flatten, labels
            )

    return labels


def extract_dataset_from_directory(
    data_dir: Path,
    out_dir: Path,
    spec: DatasetSpec,
    flatten: bool = True,
) -> List[dict]:
    """
    Extract all records from an uncompressed ETL8G/ETL9G directory.
    The directory should contain files like ETL8G_01, ETL8G_02, etc.
    Returns list of label dicts for CSV.
    """
    labels: List[dict] = []
    images_dir = out_dir / "images" / spec.name
    images_dir.mkdir(parents=True, exist_ok=True)

    # Find ETL data files (e.g., ETL8G_01, ETL9G_01, etc.)
    # Exclude INFO files and other non-data files
    data_files = sorted([
        f for f in data_dir.iterdir()
        if f.is_file() and "_" in f.name and "INFO" not in f.name.upper()
    ])

    if not data_files:
        raise FileNotFoundError(f"No ETL data files found in {data_dir}")

    global_idx = 0
    for data_file in tqdm(data_files, desc=f"Processing {spec.name}"):
        global_idx = _process_records(
            iter_records_from_file(data_file, spec),
            spec, out_dir, data_file.name, global_idx, flatten, labels
        )

    return labels


def write_labels_csv(labels: List[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "dataset", "source_member", "index",
        "label_char", "label_jis_hex", "label_jis_int",
        "image_path", "width", "height"
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in labels:
            w.writerow(row)


# -----------------------------
# Main
# -----------------------------

def detect_source_type(data_dir: Path, spec: DatasetSpec) -> Tuple[str, Optional[Path]]:
    """
    Detect whether the source is a ZIP file or an uncompressed directory.
    Returns (source_type, path) where source_type is 'zip', 'directory', or 'none'.
    """
    # Check for ZIP file
    zip_path = data_dir / spec.zip_filename
    if zip_path.exists():
        return "zip", zip_path

    # Check for uncompressed directory
    dir_path = data_dir / spec.name
    if dir_path.is_dir():
        # Verify it contains data files
        data_files = [f for f in dir_path.iterdir() if f.is_file() and "_" in f.name]
        if data_files:
            return "directory", dir_path

    return "none", None


def extract_auto(
    data_dir: Path,
    out_dir: Path,
    spec: DatasetSpec,
    flatten: bool = True,
) -> List[dict]:
    """
    Automatically detect source type (ZIP or directory) and extract.
    """
    source_type, source_path = detect_source_type(data_dir, spec)

    if source_type == "zip":
        print(f"Extracting {spec.name} from ZIP: {source_path} ...")
        return extract_dataset(source_path, out_dir, spec, flatten)
    elif source_type == "directory":
        print(f"Extracting {spec.name} from directory: {source_path} ...")
        return extract_dataset_from_directory(source_path, out_dir, spec, flatten)
    else:
        print(f"[WARN] No source found for {spec.name} in {data_dir}")
        return []


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract ETL Character Database images")
    parser.add_argument(
        "--data-dir", "-d",
        type=Path,
        default=Path(os.environ.get("ETL_DATA_DIR", "data")),
        help="Directory containing ETL data (ZIP files or extracted folders)"
    )
    parser.add_argument(
        "--out-dir", "-o",
        type=Path,
        default=Path(os.environ.get("ETL_OUT_DIR", "out")),
        help="Output directory for extracted images and labels"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["ETL8G", "ETL9G", "ETL8B", "ETL9B", "all"],
        default=["all"],
        help="Which datasets to extract (default: all)"
    )
    parser.add_argument(
        "--flatten",
        action="store_true",
        default=True,
        help="Flatten output (don't group by character)"
    )
    parser.add_argument(
        "--no-flatten",
        action="store_false",
        dest="flatten",
        help="Group images by character label"
    )

    args = parser.parse_args()

    data_dir = args.data_dir
    out_dir = args.out_dir
    flatten = args.flatten

    # Determine which datasets to process
    if "all" in args.datasets:
        datasets_to_process = list(DATASET_SPECS.keys())
    else:
        datasets_to_process = args.datasets

    data_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_labels: List[dict] = []

    for dataset_name in datasets_to_process:
        spec = DATASET_SPECS[dataset_name]
        labels = extract_auto(data_dir, out_dir, spec, flatten)
        all_labels.extend(labels)
        if labels:
            print(f"  -> {len(labels)} samples extracted from {dataset_name}")

    if all_labels:
        write_labels_csv(all_labels, out_dir / "labels.csv")
        print("\nDone.")
        print(f"Images: {out_dir / 'images'}")
        print(f"Labels: {out_dir / 'labels.csv'}")
        print(f"Total samples: {len(all_labels)}")
    else:
        print("\n[ERROR] No datasets were found or extracted.")
        print(f"Please ensure data is available in: {data_dir}")
        print("Expected structure:")
        print("  - ZIP files: ETL8G.zip, ETL9G.zip, etc.")
        print("  - Or directories: ETL8G/, ETL9G/, etc. containing ETL8G_01, etc.")
        sys.exit(1)


if __name__ == "__main__":
    main()