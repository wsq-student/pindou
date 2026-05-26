from PySide6.QtWidgets import (
    QLineEdit, QPushButton, QHBoxLayout, QWidget, QLabel,
    QHeaderView, QTableView, QTableWidget, QTableWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor


class SearchBox(QWidget):
    textChanged = Signal(str)

    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setMinimumHeight(36)
        self.input.textChanged.connect(self.textChanged.emit)
        layout.addWidget(self.input)


class IconButton(QPushButton):
    def __init__(self, text: str = "", icon_text: str = "", parent=None):
        super().__init__(f"  {icon_text}  {text}" if icon_text else text, parent)
        self.setCursor(Qt.PointingHandCursor)


class StatusLabel(QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("statusLabel")

    def set_success(self, text: str):
        self.setText(f"✓ {text}")
        self.setProperty("status", "success")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_error(self, text: str):
        self.setText(f"✗ {text}")
        self.setProperty("status", "error")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_loading(self, text: str):
        self.setText(f"⟳ {text}")
        self.setProperty("status", "loading")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_idle(self, text: str = ""):
        self.setText(text)
        self.setProperty("status", "")
        self.style().unpolish(self)
        self.style().polish(self)


class SortableTableModel(QStandardItemModel):
    def __init__(self, columns: list[str], parent=None):
        super().__init__(0, len(columns), parent)
        self.setHorizontalHeaderLabels(columns)


class SortableTableView(QWidget):
    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.model = SortableTableModel(columns)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.table.verticalHeader().setDefaultSectionSize(50)

        layout.addWidget(self.table)

    def set_data(self, rows: list[list]):
        self.model.removeRows(0, self.model.rowCount())
        for row in rows:
            items = [QStandardItem(str(cell)) for cell in row]
            self.model.appendRow(items)

    def set_row_color(self, row: int, color: QColor):
        for col in range(self.model.columnCount()):
            item = self.model.item(row, col)
            if item:
                item.setBackground(color)

    def set_filter(self, keyword: str):
        self.proxy.setFilterFixedString(keyword)
