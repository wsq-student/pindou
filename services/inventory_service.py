from datetime import datetime
from typing import Optional

from models.models import InventoryItem, InventoryLog
from storage.inventory_store import InventoryStore
from storage.color_mapping_store import ColorMappingStore
from storage.log_store import LogStore
from utils.logger import get_logger

logger = get_logger(__name__)


class InventoryService:
    def __init__(self):
        self.store = InventoryStore()
        self.mapping_store = ColorMappingStore()
        self.log_store = LogStore()

    def get_all(self) -> list[InventoryItem]:
        return self.store.get_all()

    def get_by_code(self, code: str) -> Optional[InventoryItem]:
        return self.store.get_by_code(code)

    def add_or_update(self, code: str, stock: int, threshold: int = 10) -> InventoryItem:
        existing = self.store.get_by_code(code)
        if existing:
            old_stock = existing.current_stock
            existing.current_stock = stock
            existing.warning_threshold = threshold
            existing.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.store.upsert(existing)
            logger.info(f"更新库存: [{code}] {old_stock}->{stock}")
        else:
            existing = InventoryItem(
                code=code.upper(),
                current_stock=stock,
                warning_threshold=threshold,
            )
            self.store.upsert(existing)
            logger.info(f"新增颜色库存: [{code}], 初始: {stock}")
        return existing

    def delete_code(self, code: str) -> bool:
        result = self.store.delete(code)
        if result:
            logger.info(f"已删除库存项: {code}")
        return result

    def search(self, keyword: str) -> list[InventoryItem]:
        return self.store.search(keyword)

    def get_low_stock(self) -> list[InventoryItem]:
        return self.store.get_low_stock()

    def ensure_inventory_exists(self, code: str) -> InventoryItem:
        item = self.store.get_by_code(code)
        if item is None:
            item = InventoryItem(code=code.upper(), current_stock=0)
            self.store.upsert(item)
        return item

    def _deduct_and_log(self, code: str, count: int, source: str) -> None:
        code = code.upper()
        count = int(count)
        item = self.store.get_by_code(code)
        if item is None:
            item = InventoryItem(code=code, current_stock=0)

        item.current_stock -= count
        item.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.store.upsert(item)

        log = InventoryLog(type="消耗", code=code, change=-count, source=source)
        self.log_store.append(log)
        logger.info(f"扣减库存: [{code}] -{count}")

    def check_and_deduct(self, beads: list[dict], pattern_name: str) -> tuple[bool, list[dict]]:
        """检查库存并扣减。beads: [{"code":"A1","count":42}, ...]"""
        insufficient: list[dict] = []

        for bead in beads:
            code = bead["code"].upper()
            count = int(bead["count"])
            item = self.store.get_by_code(code)
            current = item.current_stock if item else 0
            if current < count:
                insufficient.append({
                    "code": code,
                    "need": count,
                    "current": current,
                    "shortage": count - current,
                })

        if insufficient:
            return False, insufficient

        for bead in beads:
            self._deduct_and_log(bead["code"], bead["count"], pattern_name)

        return True, []

    def force_deduct(self, beads: list[dict], pattern_name: str) -> None:
        """库存不足时强制扣减，允许负库存，并写入消耗日志。"""
        for bead in beads:
            self._deduct_and_log(bead["code"], bead["count"], pattern_name)

    def add_stock(self, code: str, amount: int, source: str = "手动入库") -> bool:
        item = self.store.get_by_code(code)
        if item is None:
            item = InventoryItem(code=code.upper(), current_stock=amount)
        else:
            item.current_stock += amount
            item.update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.store.upsert(item)
        log = InventoryLog(type="入库", code=code.upper(), change=amount, source=source)
        self.log_store.append(log)
        logger.info(f"入库: [{code}] +{amount}")
        return True

    def batch_update_threshold(self, codes: list[str], threshold: int) -> int:
        """Batch update warning threshold for given codes. Returns count of updated."""
        updated = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for code in codes:
            item = self.store.get_by_code(code)
            if item:
                item.warning_threshold = threshold
                item.update_time = now
                self.store.upsert(item)
                updated += 1
        if updated:
            logger.info(f"批量更新阈值: {updated} 项 -> {threshold}")
        return updated

    def batch_adjust_stock(self, codes: list[str], mode: str, value: int) -> int:
        """
        Batch adjust stock for given codes.
        mode: set | add | subtract
        """
        if mode not in {"set", "add", "subtract"}:
            raise ValueError(f"unsupported mode: {mode}")

        updated = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delta = int(value)
        for code in codes:
            item = self.store.get_by_code(code)
            if not item:
                continue
            if mode == "set":
                item.current_stock = delta
            elif mode == "add":
                item.current_stock += delta
            else:
                item.current_stock -= delta
            item.update_time = now
            self.store.upsert(item)
            updated += 1

        if updated:
            logger.info(f"批量调整库存: {updated} 项, mode={mode}, value={value}")
        return updated
