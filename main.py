"""
拼豆库存管理 AI 软件
PinDou - Bead Sprite Inventory Management with AI Recognition
"""

import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config import Config
from ui.main_window import MainWindow
from utils.logger import get_logger

logger = get_logger(__name__)

NEW_SCHEMAS = {
    Config.INVENTORY_CSV: ["code", "current_stock", "warning_threshold", "update_time"],
    Config.COLOR_MAPPING_CSV: ["code", "color_hex"],
    Config.PATTERN_RECORDS_CSV: ["id", "pattern_name", "image_path", "create_time"],
    Config.PATTERN_DETAILS_CSV: ["pattern_id", "code", "count"],
    Config.INVENTORY_LOGS_CSV: ["type", "code", "change", "source", "time"],
}


def main():
    Config.ensure_dirs()
    _init_data_files()
    _migrate_if_needed()

    app = QApplication(sys.argv)
    app.setApplicationName("PinDou AI")
    app.setApplicationVersion("2.0.0")
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app_icon_path = Config.ASSETS_DIR / "边牧.svg"
    if app_icon_path.exists():
        app.setWindowIcon(QIcon(str(app_icon_path)))

    logger.info("启动拼豆库存管理 AI 系统 v2.0...")

    window = MainWindow()
    window.show()

    logger.info("主窗口已显示")
    sys.exit(app.exec())


def _init_data_files():
    """Ensure all CSV data files exist with proper headers."""
    for csv_path, columns in NEW_SCHEMAS.items():
        if not csv_path.exists():
            df = pd.DataFrame(columns=columns)
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            logger.info(f"创建数据文件: {csv_path.name}")


def _migrate_if_needed():
    """Detect old-format CSV files and migrate them."""
    old_inventory_cols = {"color", "current_stock"}
    old_log_cols = {"type", "color", "change"}
    old_detail_cols = {"pattern_id", "color", "count"}

    for csv_path in [Config.INVENTORY_CSV, Config.INVENTORY_LOGS_CSV, Config.PATTERN_DETAILS_CSV]:
        if not csv_path.exists() or csv_path.stat().st_size == 0:
            continue
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            cols = set(df.columns)
            if csv_path == Config.INVENTORY_CSV and "color" in cols and "code" not in cols:
                logger.info(f"迁移旧格式库存文件: {csv_path.name}")
                csv_path.rename(csv_path.with_suffix(".csv.bak"))
                _init_data_files()
            elif csv_path == Config.INVENTORY_LOGS_CSV and "color" in cols and "code" not in cols:
                logger.info(f"迁移旧格式日志文件: {csv_path.name}")
                csv_path.rename(csv_path.with_suffix(".csv.bak"))
                _init_data_files()
            elif csv_path == Config.PATTERN_DETAILS_CSV and "color" in cols and "code" not in cols:
                logger.info(f"迁移旧格式详情文件: {csv_path.name}")
                csv_path.rename(csv_path.with_suffix(".csv.bak"))
                _init_data_files()
        except Exception as e:
            logger.warning(f"迁移检查失败 {csv_path.name}: {e}")


if __name__ == "__main__":
    main()
