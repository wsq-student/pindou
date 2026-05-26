import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QMessageBox,
    QFileDialog,
)

from config import Config


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)

        title = QLabel("系统设置")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("配置 API Key、数据路径等")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        api_group = QGroupBox("豆包 (Doubao) API 设置")
        api_form = QFormLayout(api_group)
        api_form.setSpacing(12)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入你的火山引擎 API Key")
        api_form.addRow("API Key:", self.api_key_input)

        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://ark.cn-beijing.volces.com/api/v3")
        api_form.addRow("API Base URL:", self.api_url_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("doubao-seed-2-0-lite-260215")
        api_form.addRow("模型名称:", self.model_input)

        btn_save_api = QPushButton("保存 API 设置")
        btn_save_api.clicked.connect(self._save_api_settings)
        api_form.addRow("", btn_save_api)

        layout.addWidget(api_group)

        data_group = QGroupBox("数据存储设置")
        data_form = QFormLayout(data_group)
        data_form.setSpacing(12)

        self.data_dir_label = QLabel(str(Config.DATA_DIR))
        self.data_dir_label.setStyleSheet("color: #a0a0b0; padding: 4px 0;")
        data_form.addRow("数据目录:", self.data_dir_label)

        btn_export_dir = QPushButton("选择导出目录")
        btn_export_dir.setObjectName("secondaryBtn")
        btn_export_dir.clicked.connect(self._select_export_dir)
        data_form.addRow("导出目录:", btn_export_dir)

        self.export_dir_label = QLabel(str(Config.EXPORTS_DIR))
        self.export_dir_label.setStyleSheet("color: #a0a0b0; padding: 4px 0;")
        data_form.addRow("", self.export_dir_label)

        layout.addWidget(data_group)

        ai_group = QGroupBox("AI 识别设置")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(12)

        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(10, 300)
        self.timeout_input.setValue(Config.AI_TIMEOUT)
        self.timeout_input.setSuffix(" 秒")
        ai_form.addRow("请求超时:", self.timeout_input)

        self.retries_input = QSpinBox()
        self.retries_input.setRange(1, 10)
        self.retries_input.setValue(Config.AI_MAX_RETRIES)
        ai_form.addRow("重试次数:", self.retries_input)

        btn_save_ai = QPushButton("保存 AI 设置")
        btn_save_ai.clicked.connect(self._save_ai_settings)
        ai_form.addRow("", btn_save_ai)

        layout.addWidget(ai_group)
        layout.addStretch()

    def _load_settings(self):
        self.api_key_input.setText(Config.DOUBAO_API_KEY)
        self.api_url_input.setText(Config.DOUBAO_BASE_URL)
        self.model_input.setText(Config.DOUBAO_MODEL)

    def _save_api_settings(self):
        try:
            api_key = self.api_key_input.text().strip()
            api_url = self.api_url_input.text().strip()
            model = self.model_input.text().strip()

            self._update_env("DOUBAO_API_KEY", api_key)
            self._update_env("ARK_API_KEY", api_key)
            self._update_env("DOUBAO_BASE_URL", api_url)
            self._update_env("DOUBAO_MODEL", model)

            Config.DOUBAO_API_KEY = api_key
            Config.DOUBAO_BASE_URL = api_url
            Config.DOUBAO_MODEL = model

            QMessageBox.information(self, "保存成功", "API 设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存 API 设置失败：{e}")

    def _save_ai_settings(self):
        Config.AI_TIMEOUT = self.timeout_input.value()
        Config.AI_MAX_RETRIES = self.retries_input.value()
        QMessageBox.information(self, "保存成功", "AI 设置已保存")

    def _update_env(self, key: str, value: str):
        env_path = self._get_env_path()
        env_path.parent.mkdir(parents=True, exist_ok=True)
        if not env_path.exists():
            env_path.write_text("", encoding="utf-8")

        lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)

        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}=") or line.startswith(f"# {key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break

        if not found:
            lines.append(f"{key}={value}\n")

        env_path.write_text("".join(lines), encoding="utf-8")

    def _get_env_path(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / ".env"
        return Config.BASE_DIR / ".env"

    def _select_export_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if dir_path:
            Config.EXPORTS_DIR = dir_path
            self.export_dir_label.setText(dir_path)

    def refresh(self):
        self._load_settings()
