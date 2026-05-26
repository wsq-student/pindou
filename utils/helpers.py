import re
import shutil
from datetime import datetime
from pathlib import Path

from config import Config

_NATURAL_PATTERN = re.compile(r'([A-Za-z]+)(\d+)')


def natural_sort_key(code: str) -> tuple:
    """Return a sort key for natural ordering of codes like A1, A2, B1, B10."""
    m = _NATURAL_PATTERN.match(code)
    if m:
        return (m.group(1).upper(), int(m.group(2)))
    return (code.upper(), 0)


def copy_image_to_data(image_path: str | Path, pattern_name: str) -> str:
    """Copy the uploaded image to data/images/ for persistence."""
    dest_dir = Config.DATA_DIR / "images"
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(image_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in pattern_name if c.isalnum() or c in "_- ")
    dest_name = f"{timestamp}_{safe_name}{src.suffix}"
    dest_path = dest_dir / dest_name
    shutil.copy2(src, dest_path)
    return str(dest_path)


def format_datetime(dt_str: str) -> str:
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%m/%d %H:%M")
    except ValueError:
        return dt_str
