import pandas as pd
from pathlib import Path
from typing import Optional

from config import Config
from models.models import InventoryItem
from utils.helpers import natural_sort_key


class InventoryStore:
    COLUMNS = ["code", "current_stock", "warning_threshold", "update_time"]

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or Config.INVENTORY_CSV
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

    def get_all(self) -> list[InventoryItem]:
        df = self._read()
        items = []
        for _, row in df.iterrows():
            items.append(InventoryItem.from_dict(row.to_dict()))
        items.sort(key=lambda x: natural_sort_key(x.code))
        return items

    def get_by_code(self, code: str) -> Optional[InventoryItem]:
        df = self._read()
        if df.empty:
            return None
        matched = df[df["code"] == code.upper()]
        if matched.empty:
            return None
        return InventoryItem.from_dict(matched.iloc[0].to_dict())

    def upsert(self, item: InventoryItem) -> None:
        df = self._read()
        mask = df["code"] == item.code
        if mask.any():
            idx = df[mask].index[0]
            for col in self.COLUMNS:
                df.at[idx, col] = item.to_dict()[col]
        else:
            new_row = pd.DataFrame([item.to_dict()])
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

    def search(self, keyword: str) -> list[InventoryItem]:
        df = self._read()
        if df.empty:
            return []
        kw = keyword.upper()
        mask = df["code"].str.contains(kw, case=False, na=False)
        items = []
        for _, row in df[mask].iterrows():
            items.append(InventoryItem.from_dict(row.to_dict()))
        items.sort(key=lambda x: natural_sort_key(x.code))
        return items

    def get_low_stock(self) -> list[InventoryItem]:
        df = self._read()
        if df.empty:
            return []
        low = df[df["current_stock"] <= df["warning_threshold"]]
        items = []
        for _, row in low.iterrows():
            items.append(InventoryItem.from_dict(row.to_dict()))
        return items
