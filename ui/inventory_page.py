from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDialogButtonBox,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
    QComboBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush

from services.inventory_service import InventoryService
from services.color_mapping_service import ColorMappingService
from ui.widgets import SearchBox
from ui.color_mapping_page import _make_color_icon


class InventoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = InventoryService()
        self.mapping_service = ColorMappingService()
        self._refresh_in_progress = False
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("库存管理")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("管理拼豆颜色库存并设置预警阈值")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()

        self.search = SearchBox("搜索编码或颜色名...")
        self.search.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        btn_add = QPushButton("+ 新增库存项")
        btn_add.setObjectName("successBtn")
        btn_add.clicked.connect(self._on_add)
        toolbar.addWidget(btn_add)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setObjectName("secondaryBtn")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        toolbar.addWidget(self.btn_refresh)

        layout.addLayout(toolbar)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet(
            "background-color: #5c1a1a; color: #e74c3c; padding: 8px 16px; "
            "border-radius: 8px; font-weight: bold;"
        )
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["颜色", "编码", "当前库存", "预警阈值", "更新时间"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 60)
        for col in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.cellChanged.connect(self._on_cell_changed)
        layout.addWidget(self.table, 1)

        bottom = QHBoxLayout()

        btn_delete = QPushButton("删除选中项")
        btn_delete.setObjectName("dangerBtn")
        btn_delete.clicked.connect(self._on_delete)
        bottom.addWidget(btn_delete)

        btn_add_stock = QPushButton("入库")
        btn_add_stock.setObjectName("secondaryBtn")
        btn_add_stock.clicked.connect(self._on_add_stock)
        bottom.addWidget(btn_add_stock)

        btn_batch_threshold = QPushButton("一键调整阈值")
        btn_batch_threshold.setObjectName("secondaryBtn")
        btn_batch_threshold.clicked.connect(self._on_batch_threshold)
        bottom.addWidget(btn_batch_threshold)

        btn_batch_stock = QPushButton("一键调整库存")
        btn_batch_stock.setObjectName("secondaryBtn")
        btn_batch_stock.clicked.connect(self._on_batch_stock)
        bottom.addWidget(btn_batch_stock)

        bottom.addStretch()
        layout.addLayout(bottom)

    def _set_refresh_state(self, in_progress: bool):
        self._refresh_in_progress = in_progress
        self.btn_refresh.setEnabled(not in_progress)
        self.btn_refresh.setText("刷新中..." if in_progress else "刷新")

    def _on_refresh_clicked(self):
        if self._refresh_in_progress:
            return
        self.refresh()
        self.btn_refresh.setText("已刷新")
        QTimer.singleShot(1000, lambda: self.btn_refresh.setText("刷新"))

    def _render_items(self, items: list):
        self.table.setRowCount(len(items))
        self.table.blockSignals(True)

        low_stock_codes = []
        for row, item in enumerate(items):
            mapping = self.mapping_service.get_by_code(item.code)
            hex_val = mapping.color_hex if mapping else ""
            icon_label = QLabel()
            icon_label.setPixmap(_make_color_icon(hex_val))
            icon_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, icon_label)

            self.table.setItem(row, 1, QTableWidgetItem(item.code))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.current_stock)))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.warning_threshold)))
            self.table.setItem(row, 4, QTableWidgetItem(item.update_time))

            if item.is_low_stock:
                low_stock_codes.append(item.code)
                for col in range(5):
                    cell = self.table.item(row, col)
                    if cell:
                        cell.setBackground(QBrush(QColor("#5c1a1a")))
                        cell.setForeground(QBrush(QColor("#e74c3c")))

        self.table.blockSignals(False)

        if low_stock_codes:
            self.warning_label.setText(f"⚠ 低库存预警: {', '.join(low_stock_codes)}")
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setVisible(False)

    def refresh(self):
        self._set_refresh_state(True)
        try:
            self._render_items(self.service.get_all())
        finally:
            self._set_refresh_state(False)

    def _on_search(self, keyword: str):
        self._set_refresh_state(True)
        try:
            if not keyword:
                items = self.service.get_all()
            else:
                items = self.service.search(keyword)
            self._render_items(items)
        finally:
            self._set_refresh_state(False)

    def _on_cell_changed(self, row: int, col: int):
        code_item = self.table.item(row, 1)
        if not code_item:
            return

        code = code_item.text().strip().upper()
        try:
            stock = int(self.table.item(row, 2).text())
        except (ValueError, AttributeError):
            stock = 0
        try:
            threshold = int(self.table.item(row, 3).text())
        except (ValueError, AttributeError):
            threshold = 10

        if col in (2, 3):
            self.service.add_or_update(code, stock, threshold)

    def _get_selected_codes(self) -> list[str]:
        rows = {item.row() for item in self.table.selectedItems()}
        codes: list[str] = []
        for row in rows:
            code_item = self.table.item(row, 1)
            if code_item:
                code = code_item.text().strip().upper()
                if code:
                    codes.append(code)
        return codes

    @staticmethod
    def _guess_threshold_for_selection(selected_codes: list[str], items: list) -> int:
        if not selected_codes:
            return 10
        threshold_map = {i.code.upper(): i.warning_threshold for i in items}
        picked = [threshold_map[code] for code in selected_codes if code in threshold_map]
        if not picked:
            return 10
        return picked[0] if len(set(picked)) == 1 else min(picked)

    def _on_batch_threshold(self):
        selected_codes = self._get_selected_codes()
        items = self.service.get_all()
        current_threshold = self._guess_threshold_for_selection(selected_codes, items)
        dialog = _BatchThresholdDialog(
            selected_count=len(selected_codes),
            default_threshold=current_threshold,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            codes = [i.code for i in items] if dialog.apply_to_all else selected_codes
            if not codes:
                QMessageBox.warning(self, "提示", "当前未选中任何库存项")
                return
            updated = self.service.batch_update_threshold(codes, dialog.threshold)
            QMessageBox.information(self, "完成", f"已更新 {updated} 项的预警阈值为 {dialog.threshold}")
            self.refresh()

    def _on_batch_stock(self):
        selected_codes = self._get_selected_codes()
        dialog = _BatchStockDialog(selected_count=len(selected_codes), parent=self)
        if dialog.exec() == QDialog.Accepted:
            items = self.service.get_all()
            codes = [i.code for i in items] if dialog.apply_to_all else selected_codes
            if not codes:
                QMessageBox.warning(self, "提示", "当前未选中任何库存项")
                return
            updated = self.service.batch_adjust_stock(codes, dialog.mode, dialog.value)
            mode_text = {
                "set": f"设为 {dialog.value}",
                "add": f"增加 {dialog.value}",
                "subtract": f"减少 {dialog.value}",
            }[dialog.mode]
            QMessageBox.information(self, "完成", f"已更新 {updated} 项库存（{mode_text}）")
            self.refresh()

    def _on_add(self):
        dialog = _AddInventoryDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.service.add_or_update(dialog.code, dialog.stock, dialog.threshold)
            self.refresh()

    def _on_delete(self):
        rows = {item.row() for item in self.table.selectedItems()}
        if not rows:
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(rows)} 项吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for row in sorted(rows, reverse=True):
                code = self.table.item(row, 1).text().strip()
                self.service.delete_code(code)
            self.refresh()

    def _on_add_stock(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个库存项")
            return
        code = self.table.item(row, 1).text().strip()
        dialog = _AddStockDialog(code, self)
        if dialog.exec() == QDialog.Accepted:
            self.service.add_stock(code, dialog.amount, "手动入库")
            self.refresh()


class _AddInventoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增库存项")
        self.setMinimumWidth(380)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("如: A1, B10, H7")
        layout.addRow("颜色编码:", self.code_input)

        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 99999)
        self.stock_input.setValue(0)
        layout.addRow("初始库存:", self.stock_input)

        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(1, 99999)
        self.threshold_input.setValue(10)
        layout.addRow("预警阈值:", self.threshold_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _validate_and_accept(self):
        code = self.code_input.text().strip().upper()
        if not code:
            QMessageBox.warning(self, "提示", "请输入颜色编码")
            return
        self.code = code
        self.stock = self.stock_input.value()
        self.threshold = self.threshold_input.value()
        self.accept()


class _AddStockDialog(QDialog):
    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"入库 - [{code}]")
        self.setMinimumWidth(300)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QFormLayout(self)
        layout.setSpacing(12)

        label = QLabel(f"为 <b>[{code}]</b> 增加库存:")
        layout.addRow(label)

        self.amount_input = QSpinBox()
        self.amount_input.setRange(1, 99999)
        self.amount_input.setValue(100)
        layout.addRow("入库数量:", self.amount_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @property
    def amount(self) -> int:
        return self.amount_input.value()


class _BatchThresholdDialog(QDialog):
    def __init__(self, selected_count: int = 0, default_threshold: int = 10, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一键调整预警阈值")
        self.setMinimumWidth(360)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self.selected_count = selected_count

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(1, 99999)
        self.threshold_input.setValue(max(1, default_threshold))
        layout.addRow("预警阈值:", self.threshold_input)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #94a3b8;")
        layout.addRow("提示:", self.hint_label)

        self.all_radio = QRadioButton("应用于全部库存项")
        self.selected_radio = QRadioButton(f"仅应用于选中项（{selected_count}）")
        self.all_radio.setChecked(selected_count == 0)
        self.selected_radio.setChecked(selected_count > 0)
        self.group = QButtonGroup(self)
        self.group.addButton(self.all_radio)
        self.group.addButton(self.selected_radio)
        layout.addRow("范围:", self.all_radio)
        layout.addRow("", self.selected_radio)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.group.buttonClicked.connect(self._update_hint)
        self._update_hint()
        layout.addRow(self.buttons)

    def _update_hint(self):
        if self.selected_radio.isChecked():
            if self.selected_count <= 0:
                self.hint_label.setText("未选择任何行，请先选中后再使用该选项。")
            else:
                self.hint_label.setText(f"将更新已选中的 {self.selected_count} 项。")
        else:
            self.hint_label.setText("将更新当前全部库存项。")

    def _validate_and_accept(self):
        if self.selected_radio.isChecked() and self.selected_count <= 0:
            QMessageBox.warning(self, "提示", "未选择任何库存项，请切换到“全部库存项”或先进行选择。")
            return
        self.accept()

    @property
    def threshold(self) -> int:
        return self.threshold_input.value()

    @property
    def apply_to_all(self) -> bool:
        return self.all_radio.isChecked()


class _BatchStockDialog(QDialog):
    def __init__(self, selected_count: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一键调整库存")
        self.setMinimumWidth(360)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        self.selected_count = selected_count

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("设为指定值", "set")
        self.mode_combo.addItem("增加", "add")
        self.mode_combo.addItem("减少", "subtract")
        layout.addRow("调整方式:", self.mode_combo)

        self.value_input = QSpinBox()
        self.value_input.setRange(0, 999999)
        self.value_input.setValue(100)
        layout.addRow("数值:", self.value_input)

        self.hint_label = QLabel("")
        self.hint_label.setStyleSheet("color: #94a3b8;")
        layout.addRow("提示:", self.hint_label)

        self.all_radio = QRadioButton("应用于全部库存项")
        self.selected_radio = QRadioButton(f"仅应用于选中项（{selected_count}）")
        self.all_radio.setChecked(selected_count == 0)
        self.selected_radio.setChecked(selected_count > 0)
        self.group = QButtonGroup(self)
        self.group.addButton(self.all_radio)
        self.group.addButton(self.selected_radio)
        layout.addRow("范围:", self.all_radio)
        layout.addRow("", self.selected_radio)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        self.group.buttonClicked.connect(self._update_hint)
        self.mode_combo.currentIndexChanged.connect(self._update_hint)
        self._update_hint()
        layout.addRow(self.buttons)

    def _update_hint(self):
        mode_txt = self.mode_combo.currentText()
        target_txt = (
            f"已选中的 {self.selected_count} 项"
            if self.selected_radio.isChecked()
            else "当前全部库存项"
        )
        if self.selected_radio.isChecked() and self.selected_count <= 0:
            self.hint_label.setText("未选择任何行，请先选中后再使用该选项。")
            return
        self.hint_label.setText(f"将对{target_txt}执行“{mode_txt}”。")

    def _validate_and_accept(self):
        if self.selected_radio.isChecked() and self.selected_count <= 0:
            QMessageBox.warning(self, "提示", "未选择任何库存项，请切换到“全部库存项”或先进行选择。")
            return
        self.accept()

    @property
    def mode(self) -> str:
        return str(self.mode_combo.currentData())

    @property
    def value(self) -> int:
        return self.value_input.value()

    @property
    def apply_to_all(self) -> bool:
        return self.all_radio.isChecked()
