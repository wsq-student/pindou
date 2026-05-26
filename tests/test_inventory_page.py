import unittest

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.inventory_page import InventoryPage, _BatchThresholdDialog


class InventoryPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_guess_threshold_for_selection(self):
        class Item:
            def __init__(self, code, warning_threshold):
                self.code = code
                self.warning_threshold = warning_threshold

        items = [Item("A1", 5), Item("B2", 10), Item("C3", 10)]
        self.assertEqual(
            InventoryPage._guess_threshold_for_selection(["B2", "C3"], items), 10
        )
        self.assertEqual(
            InventoryPage._guess_threshold_for_selection(["A1", "B2"], items), 5
        )
        self.assertEqual(InventoryPage._guess_threshold_for_selection([], items), 10)

    def test_batch_dialog_blocks_selected_mode_without_selection(self):
        dialog = _BatchThresholdDialog(selected_count=0, default_threshold=10)
        dialog.selected_radio.setChecked(True)

        called = {"warning": 0}
        old_warning = QMessageBox.warning

        def fake_warning(*args, **kwargs):
            called["warning"] += 1
            return QMessageBox.Ok

        QMessageBox.warning = fake_warning
        try:
            dialog._validate_and_accept()
        finally:
            QMessageBox.warning = old_warning

        self.assertEqual(called["warning"], 1)
        self.assertEqual(dialog.result(), 0)


if __name__ == "__main__":
    unittest.main()
