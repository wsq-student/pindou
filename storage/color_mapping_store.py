import pandas as pd
from pathlib import Path
from typing import Optional

from config import Config
from models.models import ColorMapping
from utils.helpers import natural_sort_key


class ColorMappingStore:
    COLUMNS = ["code", "color_hex"]

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or Config.COLOR_MAPPING_CSV
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.csv_path.exists():
            df = pd.DataFrame(columns=self.COLUMNS)
            df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")

    def _read(self) -> pd.DataFrame:
        if self.csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=self.COLUMNS)
        return pd.read_csv(self.csv_path, encoding="utf-8-sig")

    def _write(self, df: pd.DataFrame) -> None:
        df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")

    def get_all(self) -> list[ColorMapping]:
        df = self._read()
        items = []
        for _, row in df.iterrows():
            items.append(ColorMapping.from_dict(row.to_dict()))
        items.sort(key=lambda x: natural_sort_key(x.code))
        return items

    def get_by_code(self, code: str) -> Optional[ColorMapping]:
        df = self._read()
        if df.empty:
            return None
        matched = df[df["code"] == code.upper()]
        if matched.empty:
            return None
        return ColorMapping.from_dict(matched.iloc[0].to_dict())

    def get_by_codes(self, codes: list[str]) -> dict[str, ColorMapping]:
        df = self._read()
        if df.empty:
            return {}
        upper_codes = [c.upper() for c in codes]
        matched = df[df["code"].isin(upper_codes)]
        result = {}
        for _, row in matched.iterrows():
            m = ColorMapping.from_dict(row.to_dict())
            result[m.code] = m
        return result

    def upsert(self, mapping: ColorMapping) -> None:
        df = self._read()
        mask = df["code"] == mapping.code
        if mask.any():
            idx = df[mask].index[0]
            for col in self.COLUMNS:
                df.at[idx, col] = mapping.to_dict()[col]
        else:
            new_row = pd.DataFrame([mapping.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
        self._write(df)

    def delete(self, code: str) -> bool:
        df = self._read()
        before = len(df)
        df = df[df["code"] != code.upper()]
        if len(df) < before:
            self._write(df)
            return True
        return False

    def search(self, keyword: str) -> list[ColorMapping]:
        df = self._read()
        if df.empty:
            return []
        mask = df["code"].str.contains(keyword, case=False, na=False)
        items = []
        for _, row in df[mask].iterrows():
            items.append(ColorMapping.from_dict(row.to_dict()))
        items.sort(key=lambda x: natural_sort_key(x.code))
        return items

    def has_code(self, code: str) -> bool:
        return self.get_by_code(code) is not None

    def import_from_df(self, df: pd.DataFrame) -> int:
        """Batch import from a DataFrame. Returns count of imported rows."""
        existing = self._read()
        imported = 0
        for _, row in df.iterrows():
            mapping = ColorMapping.from_dict(row.to_dict())
            mask = existing["code"] == mapping.code
            if mask.any():
                idx = existing[mask].index[0]
                for col in self.COLUMNS:
                    existing.at[idx, col] = mapping.to_dict()[col]
            else:
                new_row = pd.DataFrame([mapping.to_dict()])
                existing = pd.concat([existing, new_row], ignore_index=True)
                imported += 1
        self._write(existing)
        return imported

    def export_df(self) -> pd.DataFrame:
        return self._read()
