import sys
import os
from pathlib import Path
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = BASE_DIR
load_dotenv(BASE_DIR / ".env")


class Config:
    BASE_DIR: Path = BASE_DIR
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    DOUBAO_API_KEY: str = os.getenv("DOUBAO_API_KEY", os.getenv("ARK_API_KEY", ""))
    DOUBAO_BASE_URL: str = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    DOUBAO_MODEL: str = os.getenv("DOUBAO_MODEL", "doubao-seed-2-0-lite-260215")

    DATA_DIR: Path = BASE_DIR / "data"
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    ASSETS_DIR: Path = BUNDLE_DIR / "assets"

    INVENTORY_CSV: Path = DATA_DIR / "inventory.csv"
    COLOR_MAPPING_CSV: Path = DATA_DIR / "color_mapping.csv"
    PATTERN_RECORDS_CSV: Path = DATA_DIR / "pattern_records.csv"
    PATTERN_DETAILS_CSV: Path = DATA_DIR / "pattern_details.csv"
    INVENTORY_LOGS_CSV: Path = DATA_DIR / "inventory_logs.csv"

    AI_TIMEOUT: int = 300
    AI_MAX_RETRIES: int = 3
    SUPPORTED_IMAGE_FORMATS: tuple = (".jpg", ".jpeg", ".png")

    @classmethod
    def ensure_dirs(cls) -> None:
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
