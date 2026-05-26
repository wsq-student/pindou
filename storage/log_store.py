import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Config
from models.models import InventoryLog


class LogStore:
    COLUMNS = ["type", "code", "change", "source", "time"]

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or Config.INVENTORY_LOGS_CSV
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.csv_path.exists():
            df = pd.DataFrame(columns=self.COLUMNS)
            df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")

    def _read(self) -> pd.DataFrame:
        if self.csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=self.COLUMNS)
        return pd.read_csv(self.csv_path, encoding="utf-8-sig")

    def append(self, log: InventoryLog) -> None:
        df = self._read()
        new_row = pd.DataFrame([log.to_dict()])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.csv_path, index=False, encoding="utf-8-sig")

    def get_all(self) -> list[InventoryLog]:
        df = self._read()
        logs = []
        for _, row in df.iterrows():
            logs.append(InventoryLog.from_dict(row.to_dict()))
        return logs

    def search(self, keyword: str) -> list[InventoryLog]:
        df = self._read()
        if df.empty:
            return []
        kw = keyword.upper()
        mask = (
            df["code"].str.contains(kw, case=False, na=False)
            | df["source"].str.contains(keyword, case=False, na=False)
            | df["type"].str.contains(keyword, case=False, na=False)
        )
        logs = []
        for _, row in df[mask].iterrows():
            logs.append(InventoryLog.from_dict(row.to_dict()))
        return logs

    def export_csv(self, export_path: Path) -> str:
        df = self._read()
        df.to_csv(export_path, index=False, encoding="utf-8-sig")
        return str(export_path)
