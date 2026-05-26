import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import Config
from models.models import PatternRecord, PatternDetail


class PatternStore:
    RECORD_COLUMNS = ["id", "pattern_name", "image_path", "create_time"]
    DETAIL_COLUMNS = ["pattern_id", "code", "count"]

    def __init__(self, record_path: Optional[Path] = None, detail_path: Optional[Path] = None):
        self.record_path = record_path or Config.PATTERN_RECORDS_CSV
        self.detail_path = detail_path or Config.PATTERN_DETAILS_CSV
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.record_path.exists():
            df = pd.DataFrame(columns=self.RECORD_COLUMNS)
            df.to_csv(self.record_path, index=False, encoding="utf-8-sig")
        if not self.detail_path.exists():
            df = pd.DataFrame(columns=self.DETAIL_COLUMNS)
            df.to_csv(self.detail_path, index=False, encoding="utf-8-sig")

    def _read_records(self) -> pd.DataFrame:
        if self.record_path.stat().st_size == 0:
            return pd.DataFrame(columns=self.RECORD_COLUMNS)
        return pd.read_csv(self.record_path, encoding="utf-8-sig")

    def _read_details(self) -> pd.DataFrame:
        if self.detail_path.stat().st_size == 0:
            return pd.DataFrame(columns=self.DETAIL_COLUMNS)
        return pd.read_csv(self.detail_path, encoding="utf-8-sig")

    def save_pattern(
        self, pattern_name: str, image_path: str, beads: list[dict]
    ) -> str:
        pattern_id = uuid.uuid4().hex[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record_df = self._read_records()
        new_record = pd.DataFrame([{
            "id": pattern_id,
            "pattern_name": pattern_name,
            "image_path": image_path,
            "create_time": now,
        }])
        record_df = pd.concat([record_df, new_record], ignore_index=True)
        record_df.to_csv(self.record_path, index=False, encoding="utf-8-sig")

        detail_df = self._read_details()
        rows = []
        for bead in beads:
            rows.append({
                "pattern_id": pattern_id,
                "code": bead["code"],
                "count": bead["count"],
            })
        detail_df = pd.concat([detail_df, pd.DataFrame(rows)], ignore_index=True)
        detail_df.to_csv(self.detail_path, index=False, encoding="utf-8-sig")

        return pattern_id

    def get_all_records(self) -> list[PatternRecord]:
        df = self._read_records()
        items = []
        for _, row in df.iterrows():
            items.append(PatternRecord.from_dict(row.to_dict()))
        return items

    def get_details(self, pattern_id: str) -> list[PatternDetail]:
        df = self._read_details()
        matched = df[df["pattern_id"] == pattern_id]
        items = []
        for _, row in matched.iterrows():
            items.append(PatternDetail.from_dict(row.to_dict()))
        return items

    def delete_pattern(self, pattern_id: str) -> bool:
        record_df = self._read_records()
        before_r = len(record_df)
        record_df = record_df[record_df["id"] != pattern_id]
        if len(record_df) >= before_r:
            return False
        record_df.to_csv(self.record_path, index=False, encoding="utf-8-sig")

        detail_df = self._read_details()
        detail_df = detail_df[detail_df["pattern_id"] != pattern_id]
        detail_df.to_csv(self.detail_path, index=False, encoding="utf-8-sig")
        return True
