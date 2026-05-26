from pathlib import Path

from models.models import InventoryLog
from storage.log_store import LogStore


class LogService:
    def __init__(self):
        self.store = LogStore()

    def get_all(self) -> list[InventoryLog]:
        return self.store.get_all()

    def search(self, keyword: str) -> list[InventoryLog]:
        return self.store.search(keyword)

    def export(self, export_path: Path) -> str:
        return self.store.export_csv(export_path)
