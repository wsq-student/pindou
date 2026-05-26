from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QFileDialog, QMessageBox, QColorDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QPixmap, QPainter

from services.color_mapping_service import ColorMappingService
from ui.widgets import SearchBox

HEX_PATTERN = __import__('re').compile(r'^#[0-9a-fA-F]{6}$')


def _make_color_icon(hex_color: str, size: int = 24) -> QPixmap:
    """Create a small colored square pixmap from a hex color string."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    color = QColor(hex_color) if hex_color and HEX_PATTERN.match(hex_color) else QColor("#cccccc")
    if not color.isValid():
        color = QColor("#cccccc")
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.darkGray)
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 4, 4)
    painter.end()
    return pixmap


class ColorMappingPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ColorMappingService()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("颜色编码管理")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("管理颜色编码与十六进制颜色值的映射关系")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        # Toolbar
        toolbar = QHBoxLayout()

        self.search = SearchBox("搜索编码...")
        self.search.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        btn_add = QPushButton("+ 新增映射")
        btn_add.setObjectName("successBtn")
        btn_add.clicked.connect(self._on_add)
        toolbar.addWidget(btn_add)

        btn_import = QPushButton("导入 CSV")
        btn_import.setObjectName("secondaryBtn")
        btn_import.clicked.connect(self._on_import)
        toolbar.addWidget(btn_import)

        btn_export = QPushButton("导出 CSV")
        btn_export.setObjectName("secondaryBtn")
        btn_export.clicked.connect(self._on_export)
        toolbar.addWidget(btn_export)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("secondaryBtn")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Table: color preview | code | color_hex
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["颜色", "编码", "颜色编号(HEX)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table, 1)

        # Bottom actions
        bottom = QHBoxLayout()
        btn_delete = QPushButton("删除选中映射")
        btn_delete.setObjectName("dangerBtn")
        btn_delete.clicked.connect(self._on_delete)
        bottom.addWidget(btn_delete)

        bottom.addStretch()
        layout.addLayout(bottom)

    def refresh(self):
        items = self.service.get_all()
        self.table.setRowCount(len(items))
        self.table.blockSignals(True)
        for row, item in enumerate(items):
            # color preview
            icon_label = QLabel()
            icon_label.setPixmap(_make_color_icon(item.color_hex))
            icon_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, icon_label)
            # code
            self.table.setItem(row, 1, QTableWidgetItem(item.code))
            # color_hex
            self.table.setItem(row, 2, QTableWidgetItem(item.color_hex))
        self.table.blockSignals(False)

    def _on_search(self, keyword: str):
        if not keyword:
            self.refresh()
            return
        items = self.service.search(keyword)
        self.table.setRowCount(len(items))
        self.table.blockSignals(True)
        for row, item in enumerate(items):
            icon_label = QLabel()
            icon_label.setPixmap(_make_color_icon(item.color_hex))
            icon_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, icon_label)
            self.table.setItem(row, 1, QTableWidgetItem(item.code))
            self.table.setItem(row, 2, QTableWidgetItem(item.color_hex))
        self.table.blockSignals(False)

    def _on_cell_changed(self, row: int, col: int):
        if col == 2:  # color_hex changed
            code_item = self.table.item(row, 1)
            hex_item = self.table.item(row, 2)
            if code_item and hex_item:
                code = code_item.text().strip().upper()
                hex_val = hex_item.text().strip()
                self.service.add_or_update(code, hex_val)
                # refresh the color preview
                icon_label = QLabel()
                icon_label.setPixmap(_make_color_icon(hex_val))
                icon_label.setAlignment(Qt.AlignCenter)
                self.table.setCellWidget(row, 0, icon_label)

    def _on_add(self):
        dialog = _AddMappingDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.service.add_or_update(dialog.code, dialog.color_hex)
            self.refresh()

    def _on_delete(self):
        rows = set()
        for item in self.table.selectedItems():
            rows.add(item.row())
        if not rows:
            return
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(rows)} 个映射吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for row in sorted(rows, reverse=True):
                code = self.table.item(row, 1).text().strip()
                self.service.delete(code)
            self.refresh()

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入颜色映射", "", "CSV 文件 (*.csv)",
        )
        if path:
            count = self.service.import_csv(path)
            QMessageBox.information(self, "导入成功", f"已导入/更新映射，新增 {count} 条")
            self.refresh()

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出颜色映射", "color_mapping_export.csv", "CSV 文件 (*.csv)",
        )
        if path:
            self.service.export_csv(path)
            QMessageBox.information(self, "导出成功", f"映射已导出到:\n{path}")


class _AddMappingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增颜色映射")
        self.setMinimumWidth(380)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("如: A1, B10, H7")
        layout.addRow("颜色编码:", self.code_input)

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("如: #FF5733")
        layout.addRow("颜色编号(HEX):", self.hex_input)

        # Color picker button
        picker_layout = QHBoxLayout()
        self.pick_btn = QPushButton("选择颜色")
        self.pick_btn.setObjectName("secondaryBtn")
        self.pick_btn.clicked.connect(self._on_pick_color)
        picker_layout.addWidget(self.pick_btn)
        picker_layout.addStretch()

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet("background-color: #cccccc; border: 1px solid #555; border-radius: 4px;")
        picker_layout.addWidget(self.color_preview)
        layout.addRow("", picker_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_val = color.name()
            self.hex_input.setText(hex_val)
            self.color_preview.setStyleSheet(
                f"background-color: {hex_val}; border: 1px solid #555; border-radius: 4px;"
            )

    def _validate_and_accept(self):
        code = self.code_input.text().strip().upper()
        if not code:
            QMessageBox.warning(self, "提示", "请输入颜色编码")
            return
        self.code = code
        self.color_hex = self.hex_input.text().strip()
        self.accept()
