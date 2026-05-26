from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt


class GuidePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)

        title = QLabel("使用说明")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("拼豆库存管理 AI 系统 — 快速上手指南")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        sections = [
            ("1. 配置 API Key", [
                "打开「系统设置」页面",
                "填入火山引擎 API Key（豆包视觉模型）",
                "点击「保存 API 设置」",
                "重启应用使配置生效",
            ]),
            ("2. 管理颜色映射", [
                "进入「颜色编码管理」页面",
                "添加颜色编码映射，例如: A1 → 奶白色",
                "支持导入/导出 CSV 批量管理",
                "可导入 Artkal 等品牌的官方色号表",
            ]),
            ("3. 初始化库存", [
                "进入「库存管理」页面",
                "点击「新增库存项」添加颜色编码及初始数量",
                "设置预警阈值，库存低于阈值时红色高亮提醒",
                "支持双击单元格直接编辑",
            ]),
            ("4. 识别图纸", [
                "进入「图纸识别」页面",
                "拖拽图片到虚线框，或点击「选择图片」",
                "支持 jpg / png / jpeg 格式的拼豆图纸",
                "点击「开始 AI 识别」",
                "AI 将自动提取颜色编码和数量",
                "系统会自动将编码映射为颜色名称",
            ]),
            ("5. 确认识别结果", [
                "检查识别结果表格: 编码 → 映射颜色 → 数量",
                "可手动修改编码、颜色、数量",
                "可添加行或删除错误行",
                "如出现「未知编码」警告，可一键添加映射",
                "确认无误后点击「确认并更新库存」",
            ]),
            ("6. 库存扣减", [
                "确认后系统自动检查库存",
                "库存充足: 自动扣减，写入日志",
                "库存不足: 弹窗提示缺货详情（编码、需要量、当前库存、缺口）",
                "可选择强制继续或取消",
            ]),
            ("7. 查看日志与统计", [
                "「库存日志」: 查看所有入库/消耗记录，支持搜索和导出",
                "「数据统计」: 库存占比饼图、消耗排行柱状图、趋势折线图",
            ]),
        ]

        for section_title, items in sections:
            section = QFrame()
            section.setStyleSheet(
                "QFrame { background-color: #16213e; border: 1px solid #0f3460; "
                "border-radius: 10px; padding: 16px; margin: 4px 0; }"
            )
            sec_layout = QVBoxLayout(section)
            sec_layout.setSpacing(8)

            header = QLabel(section_title)
            header.setStyleSheet("color: #e94560; font-size: 15px; font-weight: bold; background: transparent;")
            sec_layout.addWidget(header)

            for item in items:
                label = QLabel(f"  • {item}")
                label.setStyleSheet("color: #b0b0c0; font-size: 13px; background: transparent;")
                label.setWordWrap(True)
                sec_layout.addWidget(label)

            content_layout.addWidget(section)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def refresh(self):
        pass
