import cv2
import numpy as np
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


def preprocess_for_ocr(image_path: str | Path, scale: float = 2.0) -> str:
    """
    Light OpenCV preprocessing to improve text clarity for AI vision models.
    - Resize up (moderate scale)
    - Keep color (no grayscale conversion)
    - CLAHE contrast enhancement on lightness channel only
    - No sharpening, no denoising (can blur fine text)
    """
    path = Path(image_path)
    img = cv2.imread(str(path))
    if img is None:
        logger.warning(f"OpenCV 无法读取图片: {image_path}, 使用原图")
        return str(path)

    h, w = img.shape[:2]
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # CLAHE on L channel in LAB color space (keeps color, enhances contrast)
    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    enhanced = cv2.merge([l_enhanced, a, b])
    result = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    output_path = path.parent / f"{path.stem}_preprocessed{path.suffix}"
    cv2.imwrite(str(output_path), result)
    logger.info(f"OCR 预处理完成 (保持彩色): {output_path}")

    return str(output_path)
