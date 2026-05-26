import re
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QSplitter, QProgressBar, QMessageBox, QFrame, QDialog,
    QFormLayout, QLineEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from services.ai_service import AIService, AIServiceError
from services.inventory_service import InventoryService
from services.pattern_service import PatternService
from services.color_mapping_service import ColorMappingService
from models.models import RecognitionResult
from ui.widgets import StatusLabel
from ui.color_mapping_page import _make_color_icon
from utils.helpers import copy_image_to_data

CODE_PATTERN = re.compile(r'^[A-Z]{1,2}\d+$')
HEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


class _AnalyzeThread(QThread):
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            ai = AIService()
            result = ai.analyze(self.image_path)
            self.finished_signal.emit(result)
        except AIServiceError as e:
            self.error_signal.emit(str(e))
        except Exception as e:
            self.error_signal.emit(f"未知错误: {e}")


class DropFrame(QFrame):
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imagePreview")
        self.setAcceptDrops(True)
        self.setMinimumHeight(250)
        self.setMaximumHeight(400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("拖拽图片到此处\n或点击下方按钮选择文件")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #606080; font-size: 15px; background: transparent;")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            ext = Path(path).suffix.lower()
            if ext in (".jpg", ".jpeg", ".png"):
                self.file_dropped.emit(path)


class RecognitionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_service = InventoryService()
        self.pattern_service = PatternService()
        self.mapping_service = ColorMappingService()
        self.current_image_path: str | None = None
        self.recognition_result: RecognitionResult | None = None
        self.analyze_thread: _AnalyzeThread | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("图纸识别")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("上传拼豆图纸，AI 自动识别颜色编码与数量")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Horizontal)

        # Left panel - image & upload
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 12, 0)

        self.drop_frame = DropFrame()
        self.drop_frame.file_dropped.connect(self._on_file_dropped)
        left_layout.addWidget(self.drop_frame)

        btn_layout = QHBoxLayout()
        btn_select = QPushButton("选择图片")
        btn_select.setObjectName("secondaryBtn")
        btn_select.clicked.connect(self._on_select_file)
        btn_layout.addWidget(btn_select)

        self.btn_analyze = QPushButton("开始 AI 识别")
        self.btn_analyze.clicked.connect(self._on_analyze)
        self.btn_analyze.setEnabled(False)
        btn_layout.addWidget(self.btn_analyze)

        left_layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        left_layout.addWidget(self.progress)

        self.status = StatusLabel("等待上传图片...")
        left_layout.addWidget(self.status)

        left_layout.addStretch()
        splitter.addWidget(left)

        # Right panel - results
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 0, 0, 0)

        right_header = QLabel("识别结果")
        right_header.setObjectName("pageTitle")
        right_layout.addWidget(right_header)

        self.pattern_name_label = QLabel("图纸名称: --")
        self.pattern_name_label.setStyleSheet("font-size: 14px; padding: 4px 0;")
        right_layout.addWidget(self.pattern_name_label)

        # Result table: code | color preview | count
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["颜色编码", "颜色", "数量"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.result_table.setColumnWidth(1, 70)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.result_table.verticalHeader().setDefaultSectionSize(50)
        self.result_table.cellChanged.connect(self._on_result_cell_changed)
        right_layout.addWidget(self.result_table, 1)

        # Unknown codes warning
        self.unknown_label = QLabel()
        self.unknown_label.setStyleSheet(
            "background-color: #5c3a1a; color: #f39c12; padding: 8px 16px; "
            "border-radius: 8px; font-weight: bold;"
        )
        self.unknown_label.setVisible(False)
        self.unknown_label.setWordWrap(True)
        right_layout.addWidget(self.unknown_label)

        result_actions = QHBoxLayout()

        btn_add_row = QPushButton("+ 添加行")
        btn_add_row.setObjectName("secondaryBtn")
        btn_add_row.clicked.connect(self._on_add_row)
        result_actions.addWidget(btn_add_row)

        btn_delete_row = QPushButton("删除选中行")
        btn_delete_row.setObjectName("dangerBtn")
        btn_delete_row.clicked.connect(self._on_delete_row)
        result_actions.addWidget(btn_delete_row)

        result_actions.addStretch()

        self.btn_confirm = QPushButton("确认并更新库存")
        self.btn_confirm.clicked.connect(self._on_confirm)
        self.btn_confirm.setEnabled(False)
        result_actions.addWidget(self.btn_confirm)

        right_layout.addLayout(result_actions)
        splitter.addWidget(right)
        splitter.setSizes([450, 600])

        layout.addWidget(splitter, 1)

    def _on_file_dropped(self, path: str):
        self._load_image(path)

    def _on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择拼豆图纸", "",
            "图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)",
        )
        if path:
            self._load_image(path)

    def _load_image(self, path: str):
        self.current_image_path = path
        pixmap = QPixmap(path)
        scaled = pixmap.scaled(400, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.drop_frame.label.setPixmap(scaled)
        self.drop_frame.label.setText("")
        self.btn_analyze.setEnabled(True)
        self.status.set_idle("图片已加载，点击「开始 AI 识别」")
        self.btn_confirm.setEnabled(False)

    def _on_analyze(self):
        if not self.current_image_path:
            return

        self.btn_analyze.setEnabled(False)
        self.progress.setVisible(True)
        self.status.set_loading("AI 正在识别颜色编码...")

        self._dots = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_status)
        self._anim_timer.start(500)

        self.analyze_thread = _AnalyzeThread(self.current_image_path)
        self.analyze_thread.finished_signal.connect(self._on_analyze_done)
        self.analyze_thread.error_signal.connect(self._on_analyze_error)
        self.analyze_thread.start()

    def _animate_status(self):
        self._dots = (self._dots + 1) % 4
        self.status.set_loading("AI 正在识别颜色编码" + "." * self._dots)

    def _on_analyze_done(self, result: RecognitionResult):
        self._anim_timer.stop()
        self.progress.setVisible(False)
        self.btn_analyze.setEnabled(True)

        # Validate beads
        valid, invalid = AIService.validate_beads(result.beads)
        if invalid:
            invalid_info = ", ".join(f"{b['code']}({b['reason']})" for b in invalid)
            self.status.set_error(f"部分编码不合法: {invalid_info}")
        else:
            self.status.set_success(f"识别完成！共 {len(result.beads)} 个编码")

        self.recognition_result = result
        self.pattern_name_label.setText(f"图纸名称: {result.pattern_name}")

        # Populate table with mapping
        self._populate_result_table()
        self.btn_confirm.setEnabled(True)

    def _on_analyze_error(self, error_msg: str):
        self._anim_timer.stop()
        self.progress.setVisible(False)
        self.btn_analyze.setEnabled(True)
        self.status.set_error(f"识别失败: {error_msg}")
        QMessageBox.critical(self, "AI 识别失败", error_msg)

    def _populate_result_table(self):
        if not self.recognition_result:
            return
        beads = self.recognition_result.beads
        self.result_table.setRowCount(len(beads))
        self.result_table.blockSignals(True)

        unknown_codes = []
        for row, bead in enumerate(beads):
            code = bead["code"]
            count = bead["count"]

            self.result_table.setItem(row, 0, QTableWidgetItem(code))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(count)))

            # Color preview from mapping
            mapping = self.mapping_service.get_by_code(code)
            if mapping and mapping.color_hex:
                icon_label = QLabel()
                icon_label.setPixmap(_make_color_icon(mapping.color_hex, 20))
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setToolTip(mapping.color_hex)
                self.result_table.setCellWidget(row, 1, icon_label)
            else:
                unknown_codes.append(code)
                self.result_table.setItem(row, 1, QTableWidgetItem("?"))

        self.result_table.blockSignals(False)

        # Show unknown codes warning
        if unknown_codes:
            self.unknown_label.setText(
                f"⚠ 发现未知颜色编码: {', '.join(unknown_codes)}\n"
                f"请先在「颜色编码管理」中添加映射"
            )
            self.unknown_label.setVisible(True)
        else:
            self.unknown_label.setVisible(False)

    def _on_result_cell_changed(self, row: int, col: int):
        """Auto-update color preview when code changes."""
        if col == 0:
            code_item = self.result_table.item(row, 0)
            if code_item:
                code = code_item.text().strip().upper()
                mapping = self.mapping_service.get_by_code(code)
                if mapping and mapping.color_hex:
                    icon_label = QLabel()
                    icon_label.setPixmap(_make_color_icon(mapping.color_hex, 20))
                    icon_label.setAlignment(Qt.AlignCenter)
                    icon_label.setToolTip(mapping.color_hex)
                    self.result_table.blockSignals(True)
                    self.result_table.setCellWidget(row, 1, icon_label)
                    self.result_table.blockSignals(False)

    def _get_table_data(self) -> list[dict]:
        beads = []
        for row in range(self.result_table.rowCount()):
            code_item = self.result_table.item(row, 0)
            count_item = self.result_table.item(row, 2)
            if code_item and count_item:
                code = code_item.text().strip().upper()
                try:
                    count = int(count_item.text())
                except ValueError:
                    count = 0
                if code:
                    beads.append({"code": code, "count": count})
        return beads

    def _on_add_row(self):
        row = self.result_table.rowCount()
        self.result_table.insertRow(row)
        self.result_table.setItem(row, 0, QTableWidgetItem(""))
        self.result_table.setItem(row, 1, QTableWidgetItem(""))
        self.result_table.setItem(row, 2, QTableWidgetItem("0"))

    def _on_delete_row(self):
        rows = set()
        for item in self.result_table.selectedItems():
            rows.add(item.row())
        for row in sorted(rows, reverse=True):
            self.result_table.removeRow(row)

    def _on_confirm(self):
        beads = self._get_table_data()
        if not beads:
            QMessageBox.warning(self, "提示", "识别结果为空")
            return

        # Check for unknown codes
        unknown = self.mapping_service.find_unknown_codes([b["code"] for b in beads])
        if unknown:
            msg = f"以下颜色编码在映射表中不存在:\n\n{', '.join(unknown)}\n\n"
            msg += "是否打开「新增映射」对话框？"
            reply = QMessageBox.question(
                self, "未知编码", msg,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                for code in unknown:
                    dialog = _QuickAddMappingDialog(code, self)
                    if dialog.exec() == QDialog.Accepted:
                        self.mapping_service.add_or_update(dialog.code, dialog.color_hex)
                        self.inventory_service.ensure_inventory_exists(dialog.code)
            # Refresh mapping display
            self._populate_result_table()

        pattern_name = self.pattern_name_label.text().replace("图纸名称: ", "")

        # Ensure all codes have inventory entries
        for bead in beads:
            self.inventory_service.ensure_inventory_exists(bead["code"])

        # Check inventory
        ok, insufficient = self.inventory_service.check_and_deduct(beads, pattern_name)
        if not ok:
            msg = "以下编码库存不足:\n\n"
            for item in insufficient:
                msg += f"• [{item['code']}]: 需要 {item['need']}, 当前 {item['current']}, 缺 {item['shortage']}\n"
            msg += "\n是否仍然继续？"
            reply = QMessageBox.question(self, "库存不足", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            # Force deduct (also writes inventory logs)
            self.inventory_service.force_deduct(beads, pattern_name)

        # Save pattern
        saved_path = copy_image_to_data(self.current_image_path, pattern_name)
        self.pattern_service.save_recognition(saved_path, RecognitionResult(
            pattern_name=pattern_name, beads=beads,
        ))

        QMessageBox.information(self, "成功", f"库存已更新！\n{pattern_name} - {len(beads)} 个编码")

        # Reset
        self.recognition_result = None
        self.result_table.setRowCount(0)
        self.pattern_name_label.setText("图纸名称: --")
        self.btn_confirm.setEnabled(False)
        self.unknown_label.setVisible(False)
        self.status.set_idle("库存已更新，可以上传新图纸")

    def refresh(self):
        pass


class _QuickAddMappingDialog(QDialog):
    """Quick dialog to add a new color mapping for an unknown code."""
    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"新增颜色映射 - {code}")
        self.setMinimumWidth(360)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QFormLayout(self)
        layout.setSpacing(12)

        code_label = QLabel(f"<b>{code}</b>")
        layout.addRow("编码:", code_label)

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("如: #FF5733")
        layout.addRow("颜色编号(HEX):", self.hex_input)

        # Color picker
        picker_layout = QHBoxLayout()
        self.pick_btn = QPushButton("选择颜色")
        self.pick_btn.setObjectName("secondaryBtn")
        self.pick_btn.clicked.connect(self._on_pick_color)
        picker_layout.addWidget(self.pick_btn)
        picker_layout.addStretch()

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet(
            "background-color: #cccccc; border: 1px solid #555; border-radius: 4px;"
        )
        picker_layout.addWidget(self.color_preview)
        layout.addRow("", picker_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.code = code
        self.color_hex = ""

    def _on_pick_color(self):
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            hex_val = color.name()
            self.hex_input.setText(hex_val)
            self.color_preview.setStyleSheet(
                f"background-color: {hex_val}; border: 1px solid #555; border-radius: 4px;"
            )

    def accept(self):
        self.color_hex = self.hex_input.text().strip()
        super().accept()
