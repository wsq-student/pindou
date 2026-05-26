import unittest

from ui.statistics_page import _aggregate_stock_for_pie, _is_consumption_log


class _Log:
    def __init__(self, t, change):
        self.type = t
        self.change = change


class _Item:
    def __init__(self, code, stock):
        self.code = code
        self.current_stock = stock


class StatisticsPageTests(unittest.TestCase):
    def test_is_consumption_log(self):
        self.assertTrue(_is_consumption_log(_Log("消耗", -5)))
        self.assertTrue(_is_consumption_log(_Log("其他", -2)))
        self.assertFalse(_is_consumption_log(_Log("入库", 10)))

    def test_aggregate_stock_for_pie_with_other(self):
        items = [_Item(f"A{i}", i) for i in range(1, 20)]
        labels, values = _aggregate_stock_for_pie(items, max_slices=5)
        self.assertEqual(len(labels), 5)
        self.assertEqual(labels[0], "A19")
        self.assertEqual(sum(values), 19 + 18 + 17 + 16 + 15)


if __name__ == "__main__":
    unittest.main()
