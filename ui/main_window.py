from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from ui.inventory_page import InventoryPage
from ui.recognition_page import RecognitionPage
from ui.log_page import LogPage
from ui.statistics_page import StatisticsPage
from ui.settings_page import SettingsPage
from ui.color_mapping_page import ColorMappingPage
from ui.guide_page import GuidePage
from config import Config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        icon_path = Config.ASSETS_DIR / "??.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle("我嘞个豆~")
        self.setMinimumSize(1280, 800)
        self.resize(1400, 900)

        # Center the window
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

        self._init_ui()
        self._load_stylesheet()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left navigation
        nav = self._create_nav()
        main_layout.addWidget(nav)

        # Right content area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.pages = {}

        self.pages["inventory"] = InventoryPage()
        self.pages["recognition"] = RecognitionPage()
        self.pages["log"] = LogPage()
        self.pages["statistics"] = StatisticsPage()
        self.pages["guide"] = GuidePage()
        self.pages["settings"] = SettingsPage()
        self.pages["colormapping"] = ColorMappingPage()

        for page in self.pages.values():
            self.stack.addWidget(page)

        right_layout.addWidget(self.stack)
        main_layout.addWidget(right_panel, 1)

        # Connect nav buttons
        self.nav_buttons["inventory"].clicked.connect(lambda: self.switch_page("inventory"))
        self.nav_buttons["recognition"].clicked.connect(lambda: self.switch_page("recognition"))
        self.nav_buttons["log"].clicked.connect(lambda: self.switch_page("log"))
        self.nav_buttons["statistics"].clicked.connect(lambda: self.switch_page("statistics"))
        self.nav_buttons["guide"].clicked.connect(lambda: self.switch_page("guide"))
        self.nav_buttons["settings"].clicked.connect(lambda: self.switch_page("settings"))
        self.nav_buttons["colormapping"].clicked.connect(lambda: self.switch_page("colormapping"))

        # Default to guide page
        self.switch_page("guide")

    def _create_nav(self) -> QWidget:
        nav = QWidget()
        nav.setObjectName("navPanel")
        layout = QVBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("我嘞个豆")
        title.setObjectName("navTitle")
        layout.addWidget(title)

        subtitle = QLabel("拼豆库存管理系统")
        subtitle.setObjectName("navSubtitle")
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        layout.addWidget(sep)

        # Nav items
        self.nav_buttons = {}

        nav_items = [

            ("recognition", "🔍", "图纸识别"),
            ("inventory", "📦", "库存管理"),
            ("colormapping", "🎨", "颜色编码管理"),
            ("log", "📋", "库存日志"),
            ("statistics", "📊", "数据统计"),
            ("settings", "⚙", "系统设置"),
            ("guide", "📖", "使用说明"),
        ]

        for key, icon, label in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(44)
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        layout.addStretch()

        # Version
        ver = QLabel("v2.0.0 · @恒超燃")
        ver.setObjectName("navSubtitle")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)

        return nav

    def switch_page(self, name: str):
        # Update button states
        for key, btn in self.nav_buttons.items():
            btn.setChecked(key == name)
            btn.setProperty("active", "true" if key == name else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.stack.setCurrentWidget(self.pages[name])

        # Refresh page data when switching
        page = self.pages[name]
        if hasattr(page, "refresh"):
            page.refresh()

    def _load_stylesheet(self):
        qss_path = Config.ASSETS_DIR / "style.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def show_message(self, title: str, message: str, icon=QMessageBox.Information):
        QMessageBox.information(self, title, message) if icon == QMessageBox.Information else None
        QMessageBox.warning(self, title, message) if icon == QMessageBox.Warning else None
        QMessageBox.critical(self, title, message) if icon == QMessageBox.Critical else None
