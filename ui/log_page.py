from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QMessageBox,
)

from services.log_service import LogService
from ui.widgets import SearchBox


class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = LogService()
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("库存日志")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("查看所有库存变化记录，支持搜索和导出")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()

        self.search = SearchBox("搜索编码、图纸名...")
        self.search.textChanged.connect(self._on_search)
        toolbar.addWidget(self.search, 1)

        btn_export = QPushButton("导出 CSV")
        btn_export.setObjectName("secondaryBtn")
        btn_export.clicked.connect(self._on_export)
        toolbar.addWidget(btn_export)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("secondaryBtn")
        btn_refresh.clicked.connect(self.refresh)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Table: type, code, change, source, time
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["操作类型", "编码", "变化量", "来源", "时间"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.CurrentChanged)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

    def refresh(self):
        self._populate_table(self.service.get_all())

    def _populate_table(self, logs):
        self.table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(log.type))
            self.table.setItem(row, 1, QTableWidgetItem(log.code))

            change_text = f"+{log.change}" if log.change > 0 else str(log.change)
            self.table.setItem(row, 2, QTableWidgetItem(change_text))

            self.table.setItem(row, 3, QTableWidgetItem(log.source))
            self.table.setItem(row, 4, QTableWidgetItem(log.time))

    def _on_search(self, keyword: str):
        if not keyword:
            self.refresh()
            return
        logs = self.service.search(keyword)
        self._populate_table(logs)

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", f"inventory_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV 文件 (*.csv)",
        )
        if path:
            self.service.export(path)
            QMessageBox.information(self, "导出成功", f"日志已导出到:\n{path}")
