#!/bin/bash
cd /Users/tak/Business/Upstage/test-ocr-models
uv run python src/utils/image_deskew.py --single datasets/appen_test_200/ja_pii_handwriting_0038.jpg --output datasets/test_corrected
