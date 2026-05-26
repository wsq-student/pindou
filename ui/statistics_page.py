import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from services.inventory_service import InventoryService
from services.log_service import LogService
from collections import Counter


plt.style.use("dark_background")
plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#0f3460",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#a0a0b0",
    "ytick.color": "#a0a0b0",
    "grid.color": "#0f3460",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "font.family": "sans-serif",
    "axes.unicode_minus": False,
})


def _is_consumption_log(log) -> bool:
    log_type = str(getattr(log, "type", "")).strip()
    change = int(getattr(log, "change", 0) or 0)
    return log_type == "消耗" or change < 0


def _aggregate_stock_for_pie(items: list, max_slices: int = 12) -> tuple[list[str], list[int]]:
    pairs = [(i.code, i.current_stock) for i in items if int(i.current_stock) > 0]
    pairs.sort(key=lambda x: x[1], reverse=True)
    if len(pairs) <= max_slices:
        return [p[0] for p in pairs], [p[1] for p in pairs]

    top = pairs[:max_slices]
    return [p[0] for p in top], [p[1] for p in top]


class StatisticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_service = InventoryService()
        self.log_service = LogService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("数据统计")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("库存占比、消耗排行、近30天消耗趋势")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        self.canvas = FigureCanvas(Figure(figsize=(12, 8), dpi=100))
        layout.addWidget(self.canvas, 1)

    def refresh(self):
        self._draw_charts()

    def _draw_charts(self):
        self.canvas.figure.clear()
        items = self.inventory_service.get_all()
        logs = self.log_service.get_all()
        consumption_logs = [l for l in logs if _is_consumption_log(l)]

        gs = self.canvas.figure.add_gridspec(2, 2, hspace=0.35, wspace=0.3)

        # 1. Pie chart - stock distribution
        ax1 = self.canvas.figure.add_subplot(gs[0, 0])
        labels, sizes = _aggregate_stock_for_pie(items, max_slices=20)
        if labels and sizes:
            colors = plt.cm.Set3(range(len(labels)))
            wedges, _, _ = ax1.pie(
                sizes,
                labels=None,
                autopct="%1.1f%%",
                colors=colors,
                startangle=90,
                textprops={"fontsize": 8},
            )
            ax1.legend(
                wedges,
                labels,
                title="颜色",
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
                fontsize=8,
                labelcolor="#e0e0e0",
                borderaxespad=0.0,
            )
            ax1.set_title("各颜色库存占比", fontsize=13, fontweight="bold")
        else:
            ax1.text(0.5, 0.5, "暂无库存数据", ha="center", va="center", transform=ax1.transAxes, fontsize=14, color="#606080")

        # 2. Bar chart - consumption ranking
        ax2 = self.canvas.figure.add_subplot(gs[0, 1])
        if consumption_logs:
            color_consumption = Counter()
            for log in consumption_logs:
                color_consumption[log.code] += abs(int(log.change))

            top = color_consumption.most_common(10)
            if top:
                names, values = zip(*top)
                ax2.barh(range(len(names)), values, color="#533483", height=0.6)
                ax2.set_yticks(range(len(names)))
                ax2.set_yticklabels(names, fontsize=10)
                ax2.set_xlabel("消耗量")
                ax2.set_title("颜色消耗排行 TOP10", fontsize=13, fontweight="bold")
                ax2.invert_yaxis()
            else:
                ax2.text(0.5, 0.5, "暂无消耗数据", ha="center", va="center", transform=ax2.transAxes, fontsize=14, color="#606080")
        else:
            ax2.text(0.5, 0.5, "暂无消耗数据", ha="center", va="center", transform=ax2.transAxes, fontsize=14, color="#606080")

        # 3. Line chart - daily consumption trend
        ax3 = self.canvas.figure.add_subplot(gs[1, 0])
        if consumption_logs:
            daily = Counter()
            for log in consumption_logs:
                date_key = str(log.time)[:10]
                daily[date_key] += abs(int(log.change))

            dates = sorted(daily.keys())[-30:]
            values = [daily[d] for d in dates]
            if dates:
                x = list(range(len(dates)))
                ax3.plot(x, values, marker="o", color="#e94560", linewidth=2, markersize=4)
                ax3.fill_between(x, values, alpha=0.2, color="#e94560")
                ax3.set_xticks(x)
                ax3.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)
                ax3.set_ylabel("消耗量")
                ax3.set_title("最近30天消耗趋势", fontsize=13, fontweight="bold")
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, "暂无趋势数据", ha="center", va="center", transform=ax3.transAxes, fontsize=14, color="#606080")
        else:
            ax3.text(0.5, 0.5, "暂无消耗数据", ha="center", va="center", transform=ax3.transAxes, fontsize=14, color="#606080")

        # 4. Summary stats
        ax4 = self.canvas.figure.add_subplot(gs[1, 1])
        ax4.axis("off")

        total_colors = len(items)
        total_stock = sum(int(i.current_stock) for i in items)
        low_stock_count = sum(1 for i in items if i.is_low_stock)
        total_consumed = sum(abs(int(l.change)) for l in consumption_logs)

        stats_text = (
            "库存概览\n\n"
            f"颜色种类:   {total_colors}\n"
            f"总库存量:   {total_stock:,}\n"
            f"低库存预警: {low_stock_count}\n"
            f"总消耗量:   {total_consumed:,}\n"
        )
        ax4.text(
            0.1,
            0.9,
            stats_text,
            transform=ax4.transAxes,
            fontsize=14,
            verticalalignment="top",
            fontfamily="Microsoft YaHei",
            color="#e0e0e0",
            linespacing=2,
        )
        ax4.set_title("数据概览", fontsize=13, fontweight="bold")

        self.canvas.figure.tight_layout()
        self.canvas.draw()
