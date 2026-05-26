# PinDou（拼豆）

拼豆库存管理 AI 软件 — 基于 AI 视觉识别的拼豆图纸分析与库存管理系统。

## 功能

- **AI 图纸识别** — 上传拼豆图纸图片，AI 自动识别颜色编码和数量
- **库存管理** — 拼豆颜色库存的增删改查，预警阈值设置
- **颜色映射** — 颜色编码与 HEX 色值的映射管理
- **出入库日志** — 完整的库存变更记录追踪
- **数据统计** — 库存消耗、使用频率等可视化图表
- **导入导出** — 支持 CSV 格式的库存数据导入导出

## 技术栈

- **GUI**: PySide6
- **AI 识别**: DeepSeek / 豆包（Doubao）Vision API
- **OCR**: Tesseract
- **图像处理**: OpenCV、Pillow
- **数据**: Pandas（CSV 存储）
- **图表**: Matplotlib

## 快速开始

### 环境要求

- Python 3.12+
- Tesseract OCR（可选，用于增强识别）

### 安装

```bash
pip install -r requirements.txt
```

### 配置

在项目根目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DOUBAO_API_KEY=your_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-2-0-lite-260215
```

### 运行

```bash
python main.py
```

### 打包

```bash
pyinstaller PinDou.spec
```

## 项目结构

```
PinDou/
├── main.py              # 入口文件
├── config.py            # 配置管理
├── ui/                  # 界面模块
│   ├── main_window.py       # 主窗口
│   ├── recognition_page.py  # AI 识别页
│   ├── inventory_page.py    # 库存管理页
│   ├── color_mapping_page.py # 颜色映射页
│   ├── log_page.py          # 日志页
│   ├── statistics_page.py   # 统计页
│   ├── settings_page.py     # 设置页
│   └── guide_page.py        # 使用指南页
├── services/            # 业务服务
│   ├── ai_service.py        # AI 识别服务
│   ├── inventory_service.py # 库存服务
│   ├── pattern_service.py   # 图案服务
│   ├── log_service.py       # 日志服务
│   └── color_mapping_service.py # 颜色映射服务
├── storage/             # 数据存储层
├── models/              # 数据模型
├── utils/               # 工具模块
│   ├── ocr_engine.py        # OCR 引擎
│   └── ocr_preprocessor.py  # 图像预处理
├── assets/              # 静态资源
├── data/                # CSV 数据文件
└── exports/             # 导出文件
```
