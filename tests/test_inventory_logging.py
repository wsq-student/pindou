import tempfile
import unittest
from pathlib import Path

from services.inventory_service import InventoryService
from storage.inventory_store import InventoryStore
from storage.log_store import LogStore


class InventoryLoggingTests(unittest.TestCase):
    def test_force_deduct_writes_logs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            inventory_csv = base / "inventory.csv"
            logs_csv = base / "inventory_logs.csv"

            service = InventoryService()
            service.store = InventoryStore(inventory_csv)
            service.log_store = LogStore(logs_csv)

            service.add_or_update("A1", 5, 10)
            service.force_deduct([{"code": "A1", "count": 8}], "图纸X")

            item = service.get_by_code("A1")
            self.assertIsNotNone(item)
            self.assertEqual(item.current_stock, -3)

            logs = service.log_store.get_all()
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].type, "消耗")
            self.assertEqual(logs[0].code, "A1")
            self.assertEqual(logs[0].change, -8)
            self.assertEqual(logs[0].source, "图纸X")

    def test_batch_adjust_stock_modes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            inventory_csv = base / "inventory.csv"
            logs_csv = base / "inventory_logs.csv"

            service = InventoryService()
            service.store = InventoryStore(inventory_csv)
            service.log_store = LogStore(logs_csv)

            service.add_or_update("A1", 10, 5)
            service.add_or_update("B2", 20, 5)

            self.assertEqual(service.batch_adjust_stock(["A1", "B2"], "add", 5), 2)
            self.assertEqual(service.get_by_code("A1").current_stock, 15)
            self.assertEqual(service.get_by_code("B2").current_stock, 25)

            self.assertEqual(service.batch_adjust_stock(["A1"], "subtract", 3), 1)
            self.assertEqual(service.get_by_code("A1").current_stock, 12)

            self.assertEqual(service.batch_adjust_stock(["B2"], "set", 100), 1)
            self.assertEqual(service.get_by_code("B2").current_stock, 100)


if __name__ == "__main__":
    unittest.main()
