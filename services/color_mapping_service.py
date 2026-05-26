import pandas as pd
from pathlib import Path

from models.models import ColorMapping
from storage.color_mapping_store import ColorMappingStore
from utils.logger import get_logger

logger = get_logger(__name__)


class ColorMappingService:
    def __init__(self):
        self.store = ColorMappingStore()

    def get_all(self) -> list[ColorMapping]:
        return self.store.get_all()

    def get_by_code(self, code: str) -> ColorMapping | None:
        return self.store.get_by_code(code)

    def get_by_codes(self, codes: list[str]) -> dict[str, ColorMapping]:
        return self.store.get_by_codes(codes)

    def add_or_update(self, code: str, color_hex: str = "") -> ColorMapping:
        mapping = ColorMapping(code=code.upper(), color_hex=color_hex)
        self.store.upsert(mapping)
        logger.info(f"颜色映射: {code} → {color_hex}")
        return mapping

    def delete(self, code: str) -> bool:
        return self.store.delete(code)

    def search(self, keyword: str) -> list[ColorMapping]:
        return self.store.search(keyword)

    def has_code(self, code: str) -> bool:
        return self.store.has_code(code)

    def import_csv(self, file_path: str | Path) -> int:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        return self.store.import_from_df(df)

    def export_csv(self, export_path: str | Path) -> str:
        df = self.store.export_df()
        df.to_csv(export_path, index=False, encoding="utf-8-sig")
        return str(export_path)

    def find_unknown_codes(self, codes: list[str]) -> list[str]:
        """Return codes that don't exist in the mapping table."""
        return [c for c in codes if not self.store.has_code(c)]
