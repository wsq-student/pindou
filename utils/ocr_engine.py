"""
OCR Engine: extract text from bead pattern images using Tesseract.
Handles Chinese/Unicode file paths via PIL (OpenCV imread fails on those).
"""
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

from utils.logger import get_logger

logger = get_logger(__name__)

# Default Tesseract install path on Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text(image_path: str | Path, scale: int = 6, psm: int = 6) -> str:
    """
    Extract text from a bead pattern image.
    - Load via PIL (handles Unicode paths)
    - Scale up for better OCR
    - Grayscale + OTSU threshold
    - Run Tesseract with specified PSM mode
    Returns extracted text string.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {image_path}")

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    pil_img = Image.open(path)
    w, h = pil_img.size
    pil_img = pil_img.resize((w * scale, h * scale), Image.LANCZOS)

    # Convert to OpenCV for thresholding
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Try with threshold first, fall back to plain gray
    text = pytesseract.image_to_string(thresh, lang="eng", config=f"--psm {psm}")
    if not text.strip():
        text = pytesseract.image_to_string(gray, lang="eng", config=f"--psm {psm}")

    text = text.strip()
    logger.info(f"OCR 提取完成: {len(text)} 字符")
    logger.debug(f"OCR 原文: {text[:300]}")
    return text
