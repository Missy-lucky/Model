from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, QThread, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QAction, QDesktopServices, QFont, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from widgets import CanvasNodeSpec, Card, ClickableCard, HeroCard, StatCard, WorkflowCanvas

from apparel_studio import (
    ROOT,
    init_product,
    product_path,
    run_paths,
    run_recipe,
)
from studio_core import (
    APP_VERSION,
    backend_catalog,
    collect_logs,
    discover_products,
    discover_runs,
    load_product,
    load_run_state,
    overview,
    product_matches,
    read_json,
    recipe_catalog,
    save_product,
    write_json_atomic,
)


SETTINGS_PATH = Path(__file__).resolve().parent / "desktop_settings.json"
APP_ICON = Path(__file__).resolve().parent / "assets" / "app-icon.ico"

TEXT = {
    "zh": {
        "app_title": "LongY Studio 服装图片工作台",
        "brand": "LongY Studio",
        "brand_sub": "服装图片生产",
        "nav_workbench": "工作台",
        "nav_home": "启动页",
        "nav_templates": "模板库",
        "nav_queue": "队列",
        "nav_backends": "后端",
        "nav_logs": "日志",
        "nav_help": "帮助",
        "products": "商品",
        "search_products": "搜索商品 / 类型 / 原图",
        "product": "商品",
        "new_number": "新编号",
        "new_type": "服装类型",
        "create": "新建",
        "refresh": "刷新",
        "language_button": "EN",
        "workbench_title": "工作台",
        "home_title": "启动页",
        "home_sub": "生产状态、环境健康与快速入口",
        "hero_ready": "生产环境就绪",
        "hero_caption": "原图只读 · 节点可追踪 · AI 后端可选",
        "go_workbench": "进入工作台",
        "launch_workflow": "一键启动",
        "environment": "环境状态",
        "runtime_ready": "桌面运行时",
        "segmentation_ready": "服装分割模型",
        "product_store": "商品数据库",
        "output_store": "产物目录",
        "ready": "正常",
        "missing": "缺失",
        "quick_actions": "快速启动",
        "recent_runs": "最近运行",
        "no_recent_runs": "暂无运行记录",
        "runtime_detail": "PySide6 与工作流引擎已加载",
        "segmentation_detail": "本地 ONNX 分割可用",
        "product_detail": "workflow_products 已连接",
        "output_detail": "workflow_runs 已连接",
        "workbench_sub": "商品资料、节点链路与运行状态",
        "templates_title": "模板库",
        "templates_sub": "按用途选择生产链路",
        "queue_title": "队列",
        "queue_sub": "全部运行状态与进度",
        "backends_title": "后端",
        "backends_sub": "生成服务与密钥状态",
        "logs_title": "日志",
        "logs_sub": "节点提示、人工介入与失败原因",
        "help_title": "帮助",
        "help_sub": "快捷键、状态和生产原则",
        "announcement": "公告",
        "garment_type": "服装类型",
        "input_class": "输入分类",
        "pieces": "件数",
        "capture_state": "拍摄状态",
        "attribute_group": "关键属性",
        "color": "颜色 / 图案",
        "pattern_direction": "图案方向",
        "button_count": "扣子数量",
        "collar_style": "领型",
        "sleeve_style": "袖型 / 袖口",
        "pocket_list": "口袋（逗号分隔）",
        "seam_list": "缝线（逗号分隔）",
        "lining": "内衬",
        "lining_no": "无内衬",
        "lining_yes": "有内衬",
        "fabric_texture": "面料 / 质感",
        "must_preserve_list": "必须保留（每行一条）",
        "product_json": "商品 JSON",
        "save": "保存",
        "recipe": "生产链路",
        "backend": "后端",
        "rerun": "重跑",
        "run": "运行",
        "running": "运行中",
        "open_folder": "打开目录",
        "node_chain": "节点链路",
        "node": "节点",
        "branch": "分支",
        "status": "状态",
        "message": "说明",
        "node_details": "节点详情",
        "artifacts": "产物",
        "open_artifact": "打开产物",
        "preview": "产物预览",
        "preview_empty": "选择图片产物后显示预览",
        "template_open": "打开链路",
        "nodes": "节点",
        "use_case": "用途",
        "tags": "标签",
        "queue_updated": "更新时间",
        "progress": "进度",
        "directory": "目录",
        "available": "可用",
        "unavailable": "不可用",
        "no_key": "缺少密钥",
        "no_key_needed": "无需密钥",
        "key_note": "只检查密钥是否存在，不在界面显示密钥。",
        "time": "时间",
        "shortcuts": "快捷键",
        "shortcut_refresh": "刷新数据",
        "shortcut_help": "打开帮助",
        "status_help": "状态说明",
        "principles": "生产原则",
        "principle_text": "原图只读；属性数据是 QC 依据；AI 只作为可选后端；信息不足的 C 类图片应补拍或补工艺数据。",
        "status_pending": "等待",
        "status_running": "运行中",
        "status_passed": "通过",
        "status_failed": "失败",
        "status_needs_human": "需人工",
        "status_blocked": "等待上游",
        "status_skipped": "已跳过",
        "status_idle": "空闲",
        "confirm_ai": "将调用生图接口，是否继续？",
        "confirm_title": "确认调用生图",
        "save_ok": "商品资料已保存",
        "create_ok": "商品已创建",
        "run_started": "工作流已启动",
        "run_done": "工作流完成",
        "queued_run": "已加入队列",
        "start_next": "继续队列",
        "queue_pending": "排队中",
        "json_error": "JSON 格式错误",
        "select_product": "请选择商品",
        "select_node": "请选择节点",
        "product_count": "商品",
        "run_count": "运行",
        "active_count": "进行",
        "human_count": "人工",
        "status_bar": "原始图库只读 · 成品与中间产物分目录保存",
        "menu_file": "文件",
        "menu_view": "视图",
        "menu_language": "语言",
        "menu_help": "帮助",
        "menu_about": "关于",
        "menu_exit": "退出",
        "about_text": "LongY Studio 是本地服装图片生产工作台。",
        "no_products": "暂无商品",
        "no_logs": "暂无日志",
        "no_queue": "队列中没有任务",
        "no_artifacts": "当前节点没有产物",
    },
    "en": {
        "app_title": "LongY Studio Apparel Workbench",
        "brand": "LongY Studio",
        "brand_sub": "Apparel image production",
        "nav_workbench": "Workbench",
        "nav_home": "Home",
        "nav_templates": "Templates",
        "nav_queue": "Queue",
        "nav_backends": "Backends",
        "nav_logs": "Logs",
        "nav_help": "Help",
        "products": "Products",
        "search_products": "Search product / type / source",
        "product": "Product",
        "new_number": "New number",
        "new_type": "Garment type",
        "create": "Create",
        "refresh": "Refresh",
        "language_button": "中文",
        "workbench_title": "Workbench",
        "home_title": "Home",
        "home_sub": "Production status, environment health, and quick launch",
        "hero_ready": "Production environment ready",
        "hero_caption": "Read-only sources · traceable nodes · optional AI backend",
        "go_workbench": "Open workbench",
        "launch_workflow": "Launch now",
        "environment": "Environment",
        "runtime_ready": "Desktop runtime",
        "segmentation_ready": "Segmentation model",
        "product_store": "Product database",
        "output_store": "Output store",
        "ready": "Ready",
        "missing": "Missing",
        "quick_actions": "Quick launch",
        "recent_runs": "Recent runs",
        "no_recent_runs": "No runs yet",
        "runtime_detail": "PySide6 and workflow engine loaded",
        "segmentation_detail": "Local ONNX segmentation available",
        "product_detail": "workflow_products connected",
        "output_detail": "workflow_runs connected",
        "workbench_sub": "Product record, node chain, and run state",
        "templates_title": "Templates",
        "templates_sub": "Select a production chain by use case",
        "queue_title": "Queue",
        "queue_sub": "All runs and progress",
        "backends_title": "Backends",
        "backends_sub": "Generation services and key status",
        "logs_title": "Logs",
        "logs_sub": "Node messages, human intervention, and failures",
        "help_title": "Help",
        "help_sub": "Shortcuts, states, and production principles",
        "announcement": "Notice",
        "garment_type": "Garment type",
        "input_class": "Input class",
        "pieces": "Pieces",
        "capture_state": "Capture state",
        "attribute_group": "Key attributes",
        "color": "Color / pattern",
        "pattern_direction": "Pattern direction",
        "button_count": "Button count",
        "collar_style": "Collar",
        "sleeve_style": "Sleeve / cuff",
        "pocket_list": "Pockets (comma separated)",
        "seam_list": "Seams (comma separated)",
        "lining": "Lining",
        "lining_no": "No lining",
        "lining_yes": "Has lining",
        "fabric_texture": "Fabric / texture",
        "must_preserve_list": "Must preserve (one per line)",
        "product_json": "Product JSON",
        "save": "Save",
        "recipe": "Recipe",
        "backend": "Backend",
        "rerun": "Rerun",
        "run": "Run",
        "running": "Running",
        "open_folder": "Open folder",
        "node_chain": "Node chain",
        "node": "Node",
        "branch": "Branch",
        "status": "Status",
        "message": "Message",
        "node_details": "Node details",
        "artifacts": "Artifacts",
        "open_artifact": "Open artifact",
        "preview": "Artifact preview",
        "preview_empty": "Select an image artifact to preview it",
        "template_open": "Open chain",
        "nodes": "nodes",
        "use_case": "Use case",
        "tags": "Tags",
        "queue_updated": "Updated",
        "progress": "Progress",
        "directory": "Directory",
        "available": "Available",
        "unavailable": "Unavailable",
        "no_key": "Missing key",
        "no_key_needed": "No key required",
        "key_note": "Only key presence is checked; keys are never displayed.",
        "time": "Time",
        "shortcuts": "Shortcuts",
        "shortcut_refresh": "Refresh data",
        "shortcut_help": "Open help",
        "status_help": "Status definitions",
        "principles": "Production principles",
        "principle_text": "Source images stay read-only. Attributes drive QC. AI is optional. Information-poor Class C images need reshoot or product data.",
        "status_pending": "Pending",
        "status_running": "Running",
        "status_passed": "Passed",
        "status_failed": "Failed",
        "status_needs_human": "Needs human",
        "status_blocked": "Blocked",
        "status_skipped": "Skipped",
        "status_idle": "Idle",
        "confirm_ai": "This will call a paid image API. Continue?",
        "confirm_title": "Confirm image API call",
        "save_ok": "Product record saved",
        "create_ok": "Product created",
        "run_started": "Workflow started",
        "run_done": "Workflow finished",
        "queued_run": "Added to queue",
        "start_next": "Continue queue",
        "queue_pending": "Queued",
        "json_error": "Invalid JSON",
        "select_product": "Select a product",
        "select_node": "Select a node",
        "product_count": "Products",
        "run_count": "Runs",
        "active_count": "Active",
        "human_count": "Human",
        "status_bar": "Source library is read-only · outputs and intermediates are stored separately",
        "menu_file": "File",
        "menu_view": "View",
        "menu_language": "Language",
        "menu_help": "Help",
        "menu_about": "About",
        "menu_exit": "Exit",
        "about_text": "LongY Studio is a local apparel image production workbench.",
        "no_products": "No products",
        "no_logs": "No logs",
        "no_queue": "Queue is empty",
        "no_artifacts": "No artifacts for this node",
    },
}

RECIPE_INFO = {
    "plan-view": {
        "zh": ("服装平面图", "工艺展示 / 商品主图", "平面图、半自动、关键点", "从原图分类、属性录入、分割、模板映射到平面图 QC。"),
        "en": ("Garment plan view", "Technical / main image", "plan view, semi-auto, landmarks", "Classify, record attributes, segment, map to template, then run QC."),
    },
    "white-main": {
        "zh": ("白底主图", "电商通用主图", "白底、自动、抠图", "规范化原图并生成 1536×1536 纯白背景主图。"),
        "en": ("White main image", "General e-commerce", "white background, automatic", "Normalize source and create a 1536×1536 white main image."),
    },
    "detail-sheet": {
        "zh": ("细节检查", "工艺审版 / QC", "细节、审版、自动", "生成上中下与中心区域的高清细节检查表。"),
        "en": ("Detail sheet", "Construction QC", "detail, review", "Create top/middle/bottom/center detail inspection sheets."),
    },
    "on-model": {
        "zh": ("模特上身图", "店铺展示 / 搭配页", "模特、可插拔后端", "生成模特拍摄说明、参考卡与可选 AI 生图请求。"),
        "en": ("On-model image", "Store display", "model, pluggable backend", "Create model brief, casting card, and optional AI request."),
    },
    "colorway": {
        "zh": ("颜色变体", "多色 SKU", "颜色、规格", "按商品资料生成颜色变体生产规格与素材需求。"),
        "en": ("Colorways", "Multi-color SKU", "color, specification", "Generate colorway production specs and asset requirements."),
    },
    "marketplace-pack": {
        "zh": ("渠道导出", "多渠道交付", "导出、尺寸", "从已确认主资产导出常见电商尺寸。"),
        "en": ("Marketplace pack", "Channel delivery", "export, sizes", "Export common marketplace sizes from an approved primary asset."),
    },
    "full-studio": {
        "zh": ("全流程生产", "完整商品资产包", "多分支、总控、人工审核", "并行组织平面图、白底、细节、模特、颜色与渠道导出。"),
        "en": ("Full studio", "Complete asset pack", "multi-branch, review", "Coordinate plan view, white main, detail, model, color, and exports."),
    },
}

NODE_NAMES = {
    "zh": {
        "normalize": "输入规范化", "classify": "图片分类", "attributes": "商品属性",
        "segment": "服装分割", "plan_view": "平面图", "pixel_qc": "像素 QC",
        "white_main": "白底主图", "detail_grid": "细节表", "model_brief": "模特任务",
        "model_reference_sheet": "参考卡", "model_generate": "模特生成",
        "colorway": "颜色变体", "channel_exports": "渠道导出", "final_review": "人工审核",
    },
    "en": {
        "normalize": "Normalize", "classify": "Classify", "attributes": "Attributes",
        "segment": "Segment", "plan_view": "Plan view", "pixel_qc": "Pixel QC",
        "white_main": "White main", "detail_grid": "Detail sheet", "model_brief": "Model brief",
        "model_reference_sheet": "Reference sheet", "model_generate": "Model generation",
        "colorway": "Colorway", "channel_exports": "Channel exports", "final_review": "Final review",
    },
}

BRANCH_NAMES = {
    "zh": {"common": "通用", "plan-view": "平面图", "white-main": "白底", "detail": "细节", "model": "模特", "colorway": "颜色", "channel": "渠道", "qc": "QC", "review": "审核", "legacy": "旧节点"},
    "en": {key: key for key in {"common", "plan-view", "white-main", "detail", "model", "colorway", "channel", "qc", "review", "legacy"}},
}

PAGE_KEYS = ["home", "workbench", "templates", "queue", "backends", "logs", "help"]
PAGE_ICONS = {
    "home": "home.svg",
    "workbench": "workbench.svg",
    "templates": "templates.svg",
    "queue": "queue.svg",
    "backends": "backend.svg",
    "logs": "logs.svg",
    "help": "help.svg",
}
RECIPE_ICONS = {
    "plan-view": "shirt.svg",
    "white-main": "white-main.svg",
    "detail-sheet": "detail.svg",
    "on-model": "model.svg",
    "colorway": "colorway.svg",
    "marketplace-pack": "channel.svg",
    "full-studio": "full.svg",
}
RECIPE_COLORS = {
    "plan-view": "#63B3ED",
    "white-main": "#63C8B8",
    "detail-sheet": "#B79CED",
    "on-model": "#EF8FB5",
    "colorway": "#F2A65A",
    "marketplace-pack": "#DCBM5B",
    "full-studio": "#F28B2C",
}

STATUS_COLORS = {
    "pending": "#65707d", "running": "#0054a6", "passed": "#107c10",
    "failed": "#c42b1c", "needs_human": "#9d5d00", "blocked": "#68717a", "skipped": "#68717a",
}

MESSAGE_ZH = {
    "Normalized source image.": "输入图片已完成规范化。",
    "Classification copied from the product record.": "已按商品记录确认图片分类。",
    "Structured garment attributes are ready.": "结构化商品属性已就绪。",
    "Garment cutout created.": "服装抠图已完成。",
    "White-background main image created.": "白底主图已生成。",
    "Detail inspection sheet created.": "细节检查表已生成。",
    "Select a garment template and annotate landmarks.": "请选择服装模板并标注关键点。",
    "Model production brief created.": "模特拍摄任务单已生成。",
    "Garment/model casting sheet created.": "服装与模特参考卡已生成。",
    "Model request prepared. Re-run with --backend openrouter to generate.": "生图请求已准备好；切换到 OpenRouter 后端后可生成。",
    "Model image generated.": "模特图已生成。",
    "Colorway production specification created.": "颜色变体生产规格已生成。",
    "Marketplace export presets created.": "渠道导出尺寸已生成。",
    "Ready for human final review.": "已准备好进行人工最终审核。",
    "No colorway list in the product record.": "商品记录中没有颜色变体。",
    "No approved primary asset for channel export.": "缺少可用于渠道导出的已确认主资产。",
}

ANNOUNCEMENTS = {
    "zh": [
        "默认使用“无 AI”后端；调用生图接口前必须显式选择并确认。",
        "原始图片库只读；中间产物与成品分目录保存。",
        "C 类输入图缺少扣子、缝线、内衬或背面结构时应补拍或补工艺数据。",
        "每个节点可单独定位失败原因；上游失败时下游自动阻塞。",
    ],
    "en": [
        "The default backend is deterministic; image API calls require explicit confirmation.",
        "Source images are read-only; intermediates and finals are stored separately.",
        "Information-poor Class C images need reshoot or product data.",
        "Each node is independently diagnosable; downstream nodes block on upstream failure.",
    ],
}


STYLE = """
QWidget {
    font-family: "Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI";
    font-size: 12px; color: #E7EBF0; background: transparent;
}
QMainWindow, #Central { background: #171B20; }
#Sidebar { background: #1D2228; border-right: 1px solid #2C323B; }
#BrandMark { background: #F28B2C; color: #201307; border-radius: 6px; font-weight: 800; }
#BrandName { font-size: 10px; font-weight: 750; color: #F7F9FB; }
#BrandSub { font-size: 8.5px; color: #8792A0; letter-spacing: 1px; }
#SectionLabel { color: #8792A0; font-size: 10.5px; font-weight: 650; }
#Muted { color: #8B96A3; }
#Header { background: #1B2026; border-bottom: 1px solid #2C323B; }
#PageTitle { font-size: 16px; font-weight: 650; }
#Announcement { background: #212730; border: 1px solid #353D49; border-radius: 6px; }
QToolTip { background: #252B33; color: #EEF2F6; border: 1px solid #3C4551; }
QPushButton, QLineEdit, QComboBox { min-height: 26px; padding: 3px 8px; border-radius: 5px; }
QPushButton { background: #283039; color: #E9EDF2; border: 1px solid #3A434F; font-weight: 550; }
QPushButton:hover { background: #313A45; border-color: #556070; }
QPushButton:pressed { background: #232932; }
QPushButton:disabled { color: #737D89; background: #232830; border-color: #2C333D; }
QPushButton#Primary { background: #F28B2C; border: 1px solid #C9701B; color: #201307; font-weight: 700; }
QPushButton#Primary:hover { background: #FF9B3D; }
QPushButton#QuickAction { background: #242B33; border: 1px solid #3A434F; color: #E9EDF2; text-align: left; }
QPushButton#QuickAction:hover { background: #2C3540; border-color: #5E6B7B; }
QPushButton#NavButton {
    background: transparent; border: 1px solid transparent; border-radius: 8px;
    padding: 4px 2px; font-size: 10px; text-align: center; color: #C8D1DB;
}
QPushButton#NavButton:hover { background: #272E37; }
QPushButton#NavButton:checked { background: #332720; border: 1px solid #6C4424; color: #FFCF95; font-weight: 700; }
QLineEdit, QComboBox, QTextEdit, QTreeWidget, QTableWidget, QListWidget {
    background: #191F25; border: 1px solid #353D48; border-radius: 5px;
    selection-background-color: #644021; selection-color: #FFFFFF; alternate-background-color: #1D242B;
}
QComboBox QAbstractItemView { background: #20262E; border: 1px solid #3E4854; }
QFrame#Panel { background: #1E242B; border: 1px solid #303843; border-radius: 8px; }
QLabel#PanelTitle { font-size: 12px; font-weight: 700; color: #F2F5F8; }
QLabel#StatTitle { color: #9AA5B1; font-size: 11px; }
QLabel#StatValue { color: #FFFFFF; font-size: 22px; font-weight: 750; }
QLabel#StatCaption { color: #8792A0; font-size: 10.5px; }
QLabel#HeroTitle { color: #FFFFFF; font-size: 22px; font-weight: 780; }
QLabel#HeroSubtitle { color: #B9C2CC; font-size: 12px; }
QLabel#SectionHeader { color: #D9DEE5; font-size: 13px; font-weight: 700; }
QTreeWidget::item, QTableWidget::item { min-height: 24px; }
QHeaderView::section {
    background: #232A32; color: #98A3AF; border: 0; border-bottom: 1px solid #333C47;
    padding: 6px; font-size: 11px;
}
QListWidget::item { height: 27px; padding: 3px 6px; border-radius: 4px; }
QListWidget::item:selected { background: #3A2B21; color: #FFD4A5; }
QTableWidget::item:selected { background: #3A2B21; color: #FFD4A5; }
QStatusBar { color: #8B96A3; background: #1B2026; border-top: 1px solid #2C323B; }
QScrollArea { border: 0; background: transparent; }
QSplitter::handle { background: #22282F; }
QCheckBox::indicator, QRadioButton::indicator { width: 14px; height: 14px; }
QTabWidget::pane { border: 1px solid #333C47; border-radius: 6px; background: #1D232A; }
QTabBar::tab { background: #232A32; color: #A9B3BE; padding: 6px 11px; border-radius: 5px; margin-right: 3px; }
QTabBar::tab:selected { background: #3A2B21; color: #FFD0A0; font-weight: 700; }
"""


class RunWorker(QThread):
    finished_run = Signal(dict)
    failed_run = Signal(str)

    def __init__(self, product: dict, recipe: str, backend: str, force: bool):
        super().__init__()
        self.product = product
        self.recipe = recipe
        self.backend = backend
        self.force = force
        self.item = {
            "number": str(product["id"]),
            "recipe": recipe,
            "backend": backend,
            "force": force,
        }

    def run(self) -> None:
        try:
            state = run_recipe(self.product, self.recipe, self.backend, self.force)
            self.finished_run.emit(state)
        except Exception as exc:
            self.failed_run.emit(f"{type(exc).__name__}: {exc}")


DEFAULT_SETTINGS = {
    "language": "zh",
    "backend": "none",
    "last_product": None,
    "last_recipe": "full-studio",
}


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.exists():
        try:
            saved = read_json(SETTINGS_PATH)
            if isinstance(saved, dict):
                settings.update(saved)
        except Exception:
            pass
    if settings.get("language") not in {"zh", "en"}:
        settings["language"] = "zh"
    if settings.get("backend") not in {"none", "openrouter"}:
        settings["backend"] = "none"
    return settings


def save_settings(settings: dict) -> None:
    write_json_atomic(SETTINGS_PATH, settings)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.language = self.settings["language"]
        self.products: list[dict] = []
        self.product_records: dict[str, dict] = {}
        self.recipe_nodes: dict[str, list] = {}
        self.current_number = self.settings.get("last_product")
        self.current_recipe = self.settings.get("last_recipe", "full-studio")
        self.run_states: list[dict] = []
        self.current_state: dict | None = None
        self.worker: RunWorker | None = None
        self.pending_runs: list[dict] = []
        self.setWindowTitle(TEXT[self.language]["app_title"])
        self.setWindowIcon(QIcon(str(APP_ICON)))
        self.resize(1380, 840)
        self.setMinimumSize(1120, 700)
        geometry = self.settings.get("window_geometry")
        if isinstance(geometry, str):
            self.restoreGeometry(QByteArray.fromBase64(geometry.encode("ascii")))
        self.setup_ui()
        self.load_data()
        backend_index = self.backend_combo.findData(self.settings.get("backend", "none"))
        if backend_index >= 0:
            self.backend_combo.setCurrentIndex(backend_index)
        self.retranslate()
        self.runtime_timer = QTimer(self)
        self.runtime_timer.setInterval(2000)
        self.runtime_timer.timeout.connect(self.refresh_runtime_data)
        self.runtime_timer.start()

    def tr(self, key: str) -> str:
        return TEXT[self.language].get(key, key)

    def status_text(self, status: str) -> str:
        if status == "pending":
            return self.tr("queue_pending")
        return TEXT[self.language].get(f"status_{status}", status)

    def recipe_title(self, recipe: str) -> str:
        return RECIPE_INFO.get(recipe, {}).get(self.language, (recipe,))[0]

    def localized_message(self, message: str) -> str:
        if self.language == "en" or not message:
            return message
        if message in MESSAGE_ZH:
            return MESSAGE_ZH[message]
        if message.startswith("Waiting for: "):
            names = message.removeprefix("Waiting for: ").split(", ")
            translated = ", ".join(NODE_NAMES["zh"].get(name, name) for name in names)
            return f"等待上游：{translated}"
        if message.startswith("QC completed for "):
            count = message.split()[3]
            return f"已完成 {count} 张图片 QC。"
        if message.startswith("Segmentation coverage is suspicious:"):
            return "分割覆盖率异常，请人工检查掩膜：" + message.split(":", 1)[-1].strip()
        if message.startswith("Using approved plan view:"):
            return "使用已确认平面图：" + message.split(":", 1)[-1].strip()
        return message

    def setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Central")
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setCentralWidget(central)

        root.addWidget(self.create_sidebar())
        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        root.addLayout(main, 1)
        main.addWidget(self.create_header())
        main.addWidget(self.create_announcement())

        self.stack = QStackedWidget()
        self.stack.setObjectName("Stack")
        main.addWidget(self.stack, 1)
        self.create_home()
        self.create_workbench()
        self.create_templates()
        self.create_queue()
        self.create_backends()
        self.create_logs()
        self.create_help()

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel()
        status.addWidget(self.status_label)
        self.create_menus()

    def create_menus(self) -> None:
        self.menus: dict[str, QMenu] = {}
        self.menu_actions: dict[str, QAction] = {}

        file_menu = self.menuBar().addMenu("")
        self.menus["file"] = file_menu
        refresh_action = QAction(self)
        refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        refresh_action.triggered.connect(self.load_data)
        file_menu.addAction(refresh_action)
        self.menu_actions["refresh"] = refresh_action
        file_menu.addSeparator()
        exit_action = QAction(self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        self.menu_actions["exit"] = exit_action

        view_menu = self.menuBar().addMenu("")
        self.menus["view"] = view_menu
        self.view_actions: dict[str, QAction] = {}
        for index, key in enumerate(PAGE_KEYS):
            action = QAction(self)
            action.triggered.connect(lambda _=False, page_index=index, page_key=key: self.switch_page(page_index, page_key))
            view_menu.addAction(action)
            self.view_actions[key] = action

        language_menu = self.menuBar().addMenu("")
        self.menus["language"] = language_menu
        self.language_actions: dict[str, QAction] = {}
        for language, title in (("zh", "中文"), ("en", "English")):
            action = QAction(title, self)
            action.setCheckable(True)
            action.triggered.connect(lambda _=False, selected=language: self.select_language(selected))
            language_menu.addAction(action)
            self.language_actions[language] = action

        help_menu = self.menuBar().addMenu("")
        self.menus["help"] = help_menu
        help_action = QAction(self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(lambda: self.switch_page(6, "help"))
        help_menu.addAction(help_action)
        self.menu_actions["help"] = help_action
        about_action = QAction(self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        self.menu_actions["about"] = about_action

    def create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        self.sidebar_widget = sidebar
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(88)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(7)

        mark = QLabel("LY")
        mark.setObjectName("BrandMark")
        mark.setFixedSize(42, 42)
        mark.setAlignment(Qt.AlignCenter)
        self.brand_label = QLabel()
        self.brand_label.setObjectName("BrandName")
        self.brand_label.setAlignment(Qt.AlignCenter)
        self.brand_sublabel = QLabel()
        self.brand_sublabel.setObjectName("BrandSub")
        self.brand_sublabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)
        layout.addWidget(self.brand_label)
        layout.addWidget(self.brand_sublabel)

        self.section_nav = QLabel()
        self.section_nav.setObjectName("SectionLabel")
        layout.addWidget(self.section_nav)
        self.nav_buttons: dict[str, QPushButton] = {}
        for index, key in enumerate(PAGE_KEYS):
            button = QPushButton()
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setChecked(index == 0)
            button.setIconSize(QSize(20, 20))
            icon_path = Path(__file__).resolve().parent / "assets" / "icons" / PAGE_ICONS[key]
            if icon_path.exists():
                button.setIcon(QIcon(str(icon_path)))
            button.clicked.connect(lambda _=False, page_index=index, key=key: self.switch_page(page_index, key))
            self.nav_buttons[key] = button
            button.setMinimumHeight(62)
            layout.addWidget(button, 0)

        layout.addStretch(1)

        self.refresh_button = QPushButton()
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.clicked.connect(self.load_data)
        layout.addWidget(self.refresh_button)
        self.language_button_side = QPushButton()
        self.language_button_side.setMinimumHeight(40)
        self.language_button_side.clicked.connect(self.toggle_language)
        layout.addWidget(self.language_button_side)
        return sidebar

    def create_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("Header")
        header.setFixedHeight(58)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(13, 7, 13, 7)
        layout.setSpacing(10)
        title_column = QVBoxLayout()
        title_column.setSpacing(0)
        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("Muted")
        title_column.addWidget(self.page_title)
        title_column.addWidget(self.page_subtitle)
        layout.addLayout(title_column, 1)

        self.chips_layout = QHBoxLayout()
        self.chips_layout.setSpacing(5)
        layout.addLayout(self.chips_layout)
        self.language_button = QPushButton()
        self.language_button.setFixedWidth(50)
        self.language_button.clicked.connect(self.toggle_language)
        layout.addWidget(self.language_button)
        return header

    def create_home(self) -> None:
        page = QWidget()
        page.setObjectName("HomePage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(12, 10, 12, 10)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        self.stack.addWidget(page)

        hero = HeroCard(str(Path(__file__).resolve().parent / "assets" / "hero-bg.jpg"))
        self.hero_card = hero
        hero.setMinimumHeight(142)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 14, 18, 14)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        self.hero_title = QLabel()
        self.hero_title.setObjectName("HeroTitle")
        self.hero_subtitle = QLabel()
        self.hero_subtitle.setObjectName("HeroSubtitle")
        self.hero_caption = QLabel()
        self.hero_caption.setObjectName("Muted")
        hero_text.addWidget(self.hero_title)
        hero_text.addWidget(self.hero_subtitle)
        hero_text.addWidget(self.hero_caption)
        hero_layout.addLayout(hero_text, 1)
        self.home_workbench_button = QPushButton()
        self.home_workbench_button.setObjectName("Primary")
        self.home_workbench_button.setMinimumSize(126, 34)
        self.home_workbench_button.clicked.connect(lambda: self.switch_page(1, "workbench"))
        self.home_run_button = QPushButton()
        self.home_run_button.setObjectName("Primary")
        self.home_run_button.setMinimumSize(126, 40)
        self.home_run_button.clicked.connect(self.launch_from_home)
        hero_actions = QVBoxLayout()
        hero_actions.setSpacing(6)
        hero_actions.addWidget(self.home_run_button)
        hero_actions.addWidget(self.home_workbench_button)
        hero_layout.addLayout(hero_actions)
        layout.addWidget(hero)

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(10)
        self.home_stat_cards = {
            "products": StatCard("", "0", "", "#63B3ED"),
            "runs": StatCard("", "0", "", "#63C8B8"),
            "running": StatCard("", "0", "", "#F5A524"),
            "human": StatCard("", "0", "", "#EF8FB5"),
        }
        for card in self.home_stat_cards.values():
            self.stats_row.addWidget(card, 1)
        layout.addLayout(self.stats_row)

        environment_label = QLabel()
        environment_label.setObjectName("SectionHeader")
        self.environment_header = environment_label
        layout.addWidget(environment_label)
        environment_row = QHBoxLayout()
        environment_row.setSpacing(10)
        self.environment_cards: list[tuple[Card, QLabel, QLabel, QLabel]] = []
        environment_specs = [
            ("runtime_ready", "runtime_detail", "#63C8B8"),
            ("segmentation_ready", "segmentation_detail", "#F2A65A"),
            ("product_store", "product_detail", "#63B3ED"),
            ("output_store", "output_detail", "#B79CED"),
        ]
        for key, detail, color in environment_specs:
            card = ClickableCard(key, color)
            card.setMinimumHeight(92)
            card.clicked.connect(self.open_environment_path)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 9, 12, 9)
            title = QLabel()
            title.setObjectName("PanelTitle")
            caption = QLabel()
            caption.setObjectName("Muted")
            caption.setWordWrap(True)
            status = QLabel(self.tr("ready"))
            status.setObjectName("Muted")
            card_layout.addWidget(title)
            card_layout.addWidget(caption, 1)
            card_layout.addWidget(status)
            environment_row.addWidget(card, 1)
            self.environment_cards.append((card, title, caption, status))
        layout.addLayout(environment_row)

        quick_header = QLabel()
        quick_header.setObjectName("SectionHeader")
        self.quick_header = quick_header
        layout.addWidget(quick_header)
        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)
        self.quick_buttons: dict[str, QPushButton] = {}
        quick_specs = [
            ("plan-view", "#63B3ED"),
            ("white-main", "#63C8B8"),
            ("detail-sheet", "#B79CED"),
            ("on-model", "#EF8FB5"),
            ("colorway", "#F2A65A"),
            ("marketplace-pack", "#DCBM5B"),
        ]
        for index, (recipe, color) in enumerate(quick_specs):
            button = QPushButton()
            button.setObjectName("QuickAction")
            button.setMinimumHeight(48)
            button.setStyleSheet(
                f"QPushButton#QuickAction {{ border-left: 3px solid {color}; }}"
            )
            button.clicked.connect(lambda _=False, key=recipe: self.launch_recipe_from_home(key))
            quick_grid.addWidget(button, index // 3, index % 3)
            self.quick_buttons[recipe] = button
        layout.addLayout(quick_grid)

        recent_header = QLabel()
        recent_header.setObjectName("SectionHeader")
        self.recent_header = recent_header
        layout.addWidget(recent_header)
        self.home_recent_table = QTableWidget(0, 5)
        self.home_recent_table.verticalHeader().setVisible(False)
        self.home_recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.home_recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.home_recent_table.setMinimumHeight(210)
        layout.addWidget(self.home_recent_table, 1)

    def create_announcement(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("Announcement")
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(7)
        self.announcement_label = QLabel()
        self.announcement_label.setObjectName("Muted")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(26)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self.announcement_label)
        layout.addWidget(scroll, 1)
        wrapper.setFixedHeight(34)
        return wrapper

    def panel(self, title_key: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(7)
        label = QLabel()
        label.setObjectName("PanelTitle")
        setattr(self, f"{title_key}_panel_label", label)
        layout.addWidget(label)
        return frame, layout

    def create_workbench(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)
        outer.addWidget(splitter, 1)
        self.stack.addWidget(page)

        product_frame, product_layout = self.panel("product")
        product_frame.setMinimumWidth(290)
        product_frame.setMaximumWidth(370)
        splitter.addWidget(product_frame)

        self.section_products = QLabel()
        self.section_products.setObjectName("SectionLabel")
        product_layout.addWidget(self.section_products)
        self.product_search = QLineEdit()
        self.product_search.setClearButtonEnabled(True)
        self.product_search.textChanged.connect(self.render_products)
        product_layout.addWidget(self.product_search)
        self.product_list = QListWidget()
        self.product_list.setMinimumHeight(132)
        self.product_list.itemSelectionChanged.connect(self.on_product_selected)
        product_layout.addWidget(self.product_list)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(6)
        self.new_number_edit = QLineEdit()
        self.new_number_edit.setPlaceholderText("172")
        self.new_type_edit = QLineEdit()
        self.new_type_edit.setPlaceholderText("上衣 / 裤子 / 套装")
        self.create_button = QPushButton()
        self.create_button.clicked.connect(self.create_product)
        new_row = QHBoxLayout()
        new_row.addWidget(self.new_type_edit, 1)
        new_row.addWidget(self.create_button)
        form.addRow(self.tr("new_number"), self.new_number_edit)
        self.new_number_label = form.labelForField(self.new_number_edit)
        new_type_title = QLabel(self.tr("new_type"))
        form.addRow(new_type_title, new_row)
        self.new_type_label = new_type_title
        product_layout.addLayout(form)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color:#dfe3e7;background:#dfe3e7;max-height:1px;border:0")
        product_layout.addWidget(divider)

        record_form = QFormLayout()
        record_form.setLabelAlignment(Qt.AlignRight)
        record_form.setSpacing(6)
        self.garment_type_edit = QLineEdit()
        self.input_class_combo = QComboBox()
        self.input_class_combo.addItems(["A", "B", "C"])
        self.piece_count_edit = QLineEdit()
        self.capture_state_edit = QLineEdit()
        record_form.addRow(self.tr("garment_type"), self.garment_type_edit)
        record_form.addRow(self.tr("input_class"), self.input_class_combo)
        record_form.addRow(self.tr("pieces"), self.piece_count_edit)
        record_form.addRow(self.tr("capture_state"), self.capture_state_edit)
        self.record_labels = [record_form.labelForField(widget) for widget in [self.garment_type_edit, self.input_class_combo, self.piece_count_edit, self.capture_state_edit]]
        product_layout.addLayout(record_form)

        self.attribute_group_label = QLabel()
        self.attribute_group_label.setObjectName("SectionLabel")
        product_layout.addWidget(self.attribute_group_label)

        attribute_form = QFormLayout()
        attribute_form.setLabelAlignment(Qt.AlignRight)
        attribute_form.setSpacing(6)
        self.attr_color_edit = QLineEdit()
        self.attr_pattern_edit = QLineEdit()
        self.attr_buttons_spin = QSpinBox()
        self.attr_buttons_spin.setRange(0, 99)
        self.attr_collar_edit = QLineEdit()
        self.attr_sleeve_edit = QLineEdit()
        self.attr_pockets_edit = QLineEdit()
        self.attr_seams_edit = QLineEdit()
        self.attr_lining_combo = QComboBox()
        self.attr_fabric_edit = QLineEdit()
        self.attr_must_edit = QTextEdit()
        self.attr_must_edit.setAcceptRichText(False)
        self.attr_must_edit.setFixedHeight(76)
        attribute_form.addRow(self.tr("color"), self.attr_color_edit)
        self.attr_color_label = attribute_form.labelForField(self.attr_color_edit)
        attribute_form.addRow(self.tr("pattern_direction"), self.attr_pattern_edit)
        self.attr_pattern_label = attribute_form.labelForField(self.attr_pattern_edit)
        attribute_form.addRow(self.tr("button_count"), self.attr_buttons_spin)
        self.attr_buttons_label = attribute_form.labelForField(self.attr_buttons_spin)
        attribute_form.addRow(self.tr("collar_style"), self.attr_collar_edit)
        self.attr_collar_label = attribute_form.labelForField(self.attr_collar_edit)
        attribute_form.addRow(self.tr("sleeve_style"), self.attr_sleeve_edit)
        self.attr_sleeve_label = attribute_form.labelForField(self.attr_sleeve_edit)
        attribute_form.addRow(self.tr("pocket_list"), self.attr_pockets_edit)
        self.attr_pockets_label = attribute_form.labelForField(self.attr_pockets_edit)
        attribute_form.addRow(self.tr("seam_list"), self.attr_seams_edit)
        self.attr_seams_label = attribute_form.labelForField(self.attr_seams_edit)
        attribute_form.addRow(self.tr("lining"), self.attr_lining_combo)
        self.attr_lining_label = attribute_form.labelForField(self.attr_lining_combo)
        attribute_form.addRow(self.tr("fabric_texture"), self.attr_fabric_edit)
        self.attr_fabric_label = attribute_form.labelForField(self.attr_fabric_edit)
        attribute_form.addRow(self.tr("must_preserve_list"), self.attr_must_edit)
        self.attr_must_label = attribute_form.labelForField(self.attr_must_edit)
        self.attribute_labels = [
            self.attr_color_label,
            self.attr_pattern_label,
            self.attr_buttons_label,
            self.attr_collar_label,
            self.attr_sleeve_label,
            self.attr_pockets_label,
            self.attr_seams_label,
            self.attr_lining_label,
            self.attr_fabric_label,
            self.attr_must_label,
        ]
        product_layout.addLayout(attribute_form)

        self.product_json_label = QLabel()
        self.product_json_label.setObjectName("Muted")
        product_layout.addWidget(self.product_json_label)
        self.product_json_edit = QTextEdit()
        self.product_json_edit.setFont(QFont("Cascadia Mono", 9))
        product_layout.addWidget(self.product_json_edit, 1)
        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.save_product)
        product_layout.addWidget(self.save_button)

        workflow_frame, workflow_layout = self.panel("workflow")
        workflow_frame.setMinimumWidth(370)
        splitter.addWidget(workflow_frame)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.recipe_combo = QComboBox()
        self.recipe_combo.currentIndexChanged.connect(self.on_recipe_changed)
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("无 AI / 确定性处理", "none")
        self.backend_combo.addItem("OpenRouter", "openrouter")
        self.backend_combo.currentIndexChanged.connect(self.on_backend_changed)
        self.force_check = QCheckBox()
        self.run_button = QPushButton()
        self.run_button.setObjectName("Primary")
        self.run_button.clicked.connect(self.run_workflow)
        self.folder_button = QPushButton()
        self.folder_button.clicked.connect(self.open_run_folder)
        controls.addWidget(self.recipe_combo, 2)
        controls.addWidget(self.backend_combo, 1)
        controls.addWidget(self.force_check)
        controls.addWidget(self.run_button)
        controls.addWidget(self.folder_button)
        workflow_layout.addLayout(controls)

        self.workflow_canvas = WorkflowCanvas()
        self.workflow_canvas.selection_changed.connect(self.show_selected_node_by_name)
        workflow_layout.addWidget(self.workflow_canvas, 1)

        detail_frame, detail_layout = self.panel("details")
        detail_frame.setMinimumWidth(280)
        splitter.addWidget(detail_frame)
        self.node_detail_browser = QTextBrowser()
        self.node_detail_browser.setOpenExternalLinks(True)
        detail_layout.addWidget(self.node_detail_browser)
        self.preview_label_title = QLabel()
        self.preview_label_title.setObjectName("Muted")
        detail_layout.addWidget(self.preview_label_title)
        self.artifact_preview = QLabel()
        self.artifact_preview.setMinimumHeight(220)
        self.artifact_preview.setAlignment(Qt.AlignCenter)
        self.artifact_preview.setStyleSheet(
            "background:#191F25;border:1px solid #353D48;border-radius:6px;color:#79838F"
        )
        detail_layout.addWidget(self.artifact_preview, 1)
        self.artifact_list = QListWidget()
        self.artifact_list.currentItemChanged.connect(
            lambda *_: self.update_artifact_preview()
        )
        detail_layout.addWidget(self.artifact_list, 1)
        self.open_artifact_button = QPushButton()
        self.open_artifact_button.clicked.connect(self.open_selected_artifact)
        detail_layout.addWidget(self.open_artifact_button)
        splitter.setSizes([330, 520, 350])

    def create_templates(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        frame, layout = self.panel("templates")
        outer.addWidget(frame, 1)
        self.stack.addWidget(page)
        self.template_search = QLineEdit()
        self.template_search.textChanged.connect(self.render_templates)
        layout.addWidget(self.template_search)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.template_container = QWidget()
        self.template_grid = QGridLayout(self.template_container)
        self.template_grid.setContentsMargins(0, 0, 0, 0)
        self.template_grid.setSpacing(8)
        scroll.setWidget(self.template_container)
        layout.addWidget(scroll, 1)

    def create_queue(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        frame, layout = self.panel("queue")
        outer.addWidget(frame, 1)
        self.stack.addWidget(page)
        columns = [4, 1, 2, 1, 1, 3]
        self.queue_table = QTableWidget(0, len(columns))
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.queue_table, 1)

    def create_backends(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        frame, layout = self.panel("backends")
        outer.addWidget(frame, 1)
        self.stack.addWidget(page)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.backend_grid = QGridLayout(container)
        self.backend_grid.setContentsMargins(2, 2, 2, 2)
        self.backend_grid.setSpacing(9)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def create_logs(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        frame, layout = self.panel("logs")
        outer.addWidget(frame, 1)
        self.stack.addWidget(page)
        self.log_table = QTableWidget(0, 6)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.log_table, 1)

    def create_help(self) -> None:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(10, 8, 10, 10)
        frame, layout = self.panel("help")
        outer.addWidget(frame, 1)
        self.stack.addWidget(page)
        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(False)
        layout.addWidget(self.help_browser, 1)

    def switch_page(self, index: int, key: str) -> None:
        self.stack.setCurrentIndex(index)
        for button in self.nav_buttons.values():
            button.setChecked(False)
        self.nav_buttons[key].setChecked(True)
        self.page_title.setText(self.tr(f"{key}_title"))
        self.page_subtitle.setText(self.tr(f"{key}_sub"))

    def toggle_language(self) -> None:
        self.select_language("en" if self.language == "zh" else "zh")

    def select_language(self, language: str) -> None:
        if language not in {"zh", "en"} or language == self.language:
            return
        self.language = language
        self.settings["language"] = language
        save_settings(self.settings)
        self.retranslate()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            self.tr("menu_about"),
            f"{self.tr('app_title')}\nVersion {APP_VERSION}\n\n{self.tr('about_text')}",
        )

    def closeEvent(self, event) -> None:
        self.settings["window_geometry"] = bytes(self.saveGeometry().toBase64()).decode("ascii")
        save_settings(self.settings)
        super().closeEvent(event)

    def load_data(self) -> None:
        self.recipe_nodes = recipe_catalog()
        if self.current_recipe not in self.recipe_nodes:
            self.current_recipe = "full-studio"
            self.settings["last_recipe"] = self.current_recipe
        self.products.clear()
        self.product_records.clear()
        for product in discover_products():
            try:
                record = load_product(product.number)
            except (OSError, ValueError):
                continue
            self.product_records[product.number] = record
            self.products.append(
                {
                    "id": product.number,
                    "garment_type": product.garment_type,
                    "source": product.source,
                    "has_plan_view": product.has_plan_view,
                }
            )
        valid_numbers = {product["id"] for product in self.products}
        if self.current_number not in valid_numbers:
            self.current_number = self.products[0]["id"] if self.products else None
            self.settings["last_product"] = self.current_number
        if self.products and not self.current_number:
            self.current_number = self.products[0]["id"]
            self.settings["last_product"] = self.current_number
        self.load_run_states()
        self.current_state = self.state_for(self.current_number, self.current_recipe)
        self.render_all()

    def refresh_runtime_data(self) -> None:
        """Refresh lightweight runtime views without rebuilding product editors."""
        self.load_run_states()
        self.current_state = self.state_for(self.current_number, self.current_recipe)
        self.render_nodes()
        self.render_queue()
        self.render_logs()
        self.render_chips()

    def load_run_states(self) -> None:
        self.run_states.clear()
        for run in discover_runs():
            self.run_states.append(
                {
                    "number": run.number,
                    "recipe": run.recipe,
                    "updated_at": run.updated_at,
                    "passed": run.passed,
                    "needs_human": run.needs_human,
                    "failed": run.failed,
                    "running": run.running,
                    "total": run.total,
                    "path": run.path,
                }
            )

    def state_for(self, number: str | None, recipe: str) -> dict | None:
        if not number:
            return None
        return load_run_state(number, recipe)

    def render_all(self) -> None:
        self.render_home()
        self.render_products()
        self.render_recipe_combo()
        self.render_product_form()
        self.render_nodes()
        self.render_templates()
        self.render_queue()
        self.render_backends()
        self.render_logs()
        self.render_help()
        self.render_chips()
        self.retranslate()

    def render_products(self) -> None:
        self.product_list.blockSignals(True)
        self.product_list.clear()
        query = self.product_search.text().strip().lower()
        for product in self.products:
            if query:
                searchable = " ".join(
                    [
                        product["id"],
                        product.get("garment_type", ""),
                        product.get("source", ""),
                    ]
                ).lower()
                if query not in searchable:
                    continue
            item = QListWidgetItem(f"{product['id']} · {product['garment_type']}")
            item.setData(Qt.UserRole, product["id"])
            self.product_list.addItem(item)
            if product["id"] == self.current_number:
                item.setSelected(True)
        if not self.products:
            self.product_list.addItem(self.tr("no_products"))
        self.product_list.blockSignals(False)

    def render_recipe_combo(self) -> None:
        self.recipe_combo.blockSignals(True)
        self.recipe_combo.clear()
        for key in self.recipe_nodes:
            title = RECIPE_INFO.get(key, {}).get(self.language, (key,))[0]
            self.recipe_combo.addItem(title, key)
            if key == self.current_recipe:
                self.recipe_combo.setCurrentIndex(self.recipe_combo.count() - 1)
        self.recipe_combo.blockSignals(False)

    def render_product_form(self) -> None:
        record = self.product_records.get(self.current_number or "", {})
        attributes = record.get("attributes", {}) if record else {}
        self.garment_type_edit.setText(record.get("garment_type", ""))
        self.input_class_combo.setCurrentText(record.get("input_class", "B"))
        self.piece_count_edit.setText(str(record.get("piece_count", 1)))
        self.capture_state_edit.setText(record.get("capture_state", ""))
        self.attr_color_edit.setText(str(attributes.get("color", "")))
        self.attr_pattern_edit.setText(str(attributes.get("pattern", "")))
        self.attr_buttons_spin.setValue(int(attributes.get("buttons", 0) or 0))
        self.attr_collar_edit.setText(str(attributes.get("collar", "")))
        self.attr_sleeve_edit.setText(str(attributes.get("sleeves", "")))
        self.attr_pockets_edit.setText(", ".join(str(value) for value in attributes.get("pockets", [])))
        self.attr_seams_edit.setText(", ".join(str(value) for value in attributes.get("seams", [])))
        lining_index = 1 if attributes.get("lining") else 0
        if self.attr_lining_combo.count():
            self.attr_lining_combo.setCurrentIndex(lining_index)
        self.attr_fabric_edit.setText(str(attributes.get("fabric", "")))
        self.attr_must_edit.setPlainText("\n".join(str(value) for value in attributes.get("must_preserve", [])))
        self.product_json_edit.setPlainText(json.dumps(record, ensure_ascii=False, indent=2) if record else "")

    def render_home(self) -> None:
        report = overview()
        self.hero_title.setText(self.tr("hero_ready"))
        self.hero_subtitle.setText(f"LongY Studio {APP_VERSION}")
        self.hero_caption.setText(self.tr("hero_caption"))
        self.home_workbench_button.setText(self.tr("go_workbench"))
        self.home_run_button.setText(self.tr("launch_workflow"))

        cards = self.home_stat_cards
        cards["products"].set_value(
            str(report.product_count), self.tr("product_count")
        )
        cards["products"].title_label.setText(self.tr("product_count"))
        cards["runs"].set_value(str(report.run_count), self.tr("run_count"))
        cards["runs"].title_label.setText(self.tr("run_count"))
        cards["running"].set_value(str(report.running_count), self.tr("active_count"))
        cards["running"].title_label.setText(self.tr("active_count"))
        cards["human"].set_value(str(report.needs_human_count), self.tr("human_count"))
        cards["human"].title_label.setText(self.tr("human_count"))

        self.environment_header.setText(self.tr("environment"))
        try:
            from segmentation import model_path

            model_ready = model_path().exists()
        except Exception:
            model_ready = False

        states = [
            (True, self.tr("runtime_detail")),
            (model_ready, self.tr("segmentation_detail")),
            ((ROOT / "workflow_products").exists(), self.tr("product_detail")),
            ((ROOT / "workflow_runs").exists(), self.tr("output_detail")),
        ]
        titles = [
            self.tr("runtime_ready"),
            self.tr("segmentation_ready"),
            self.tr("product_store"),
            self.tr("output_store"),
        ]
        for (_, title, caption, status), (ready, detail), label in zip(
            self.environment_cards, states, titles
        ):
            title.setText(label)
            caption.setText(detail)
            status.setText(self.tr("ready") if ready else self.tr("missing"))
            status.setStyleSheet(
                f"color:{'#63C8B8' if ready else '#E5484D'};font-weight:700"
            )

        self.quick_header.setText(self.tr("quick_actions"))
        for recipe, button in self.quick_buttons.items():
            info = RECIPE_INFO.get(recipe, {}).get(self.language, (recipe,))
            button.setText(f"{info[0]}  ·  {info[1]}")

        self.recent_header.setText(self.tr("recent_runs"))
        headers = [
            self.tr("time"),
            self.tr("product"),
            self.tr("recipe"),
            self.tr("progress"),
            self.tr("status"),
        ]
        self.home_recent_table.setColumnCount(len(headers))
        self.home_recent_table.setHorizontalHeaderLabels(headers)
        self.home_recent_table.setRowCount(min(6, len(self.run_states)))
        for row, run in enumerate(self.run_states[:6]):
            status = (
                "running" if run["running"]
                else "failed" if run["failed"]
                else "needs_human" if run["needs_human"]
                else "passed"
            )
            values = [
                run["updated_at"],
                run["number"],
                self.recipe_title(run["recipe"]),
                f"{run['passed']}/{run['total']}",
                self.status_text(status),
            ]
            for column, value in enumerate(values):
                self.home_recent_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.home_recent_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.home_recent_table.horizontalHeader().setStretchLastSection(True)

    def launch_recipe_from_home(self, recipe: str) -> None:
        self.current_recipe = recipe
        self.settings["last_recipe"] = recipe
        save_settings(self.settings)
        self.render_recipe_combo()
        self.switch_page(1, "workbench")

    def launch_from_home(self) -> None:
        recipe = self.settings.get("last_recipe", "full-studio")
        if recipe not in self.recipe_nodes:
            recipe = "full-studio"
        self.current_recipe = recipe
        index = self.backend_combo.findData("none")
        if index >= 0:
            self.backend_combo.setCurrentIndex(index)
        self.render_recipe_combo()
        self.switch_page(1, "workbench")
        self.run_workflow()

    def render_nodes(self) -> None:
        state = self.current_state or {}
        nodes = state.get("nodes", {})
        node_defs = self.recipe_nodes.get(self.current_recipe, [])
        known = {node["name"] for node in node_defs}
        specs: list[CanvasNodeSpec] = []
        for definition in node_defs:
            name = definition["name"]
            data = nodes.get(name, {})
            specs.append(
                CanvasNodeSpec(
                    name=name,
                    title=NODE_NAMES[self.language].get(name, name),
                    branch=definition["branch"],
                    status=self.status_text(data.get("status", "pending")),
                    status_key=data.get("status", "pending"),
                    message=self.localized_message(data.get("message", "")),
                    requires=list(definition.get("requires", [])),
                )
            )
        for name, data in nodes.items():
            if name not in known:
                specs.append(
                    CanvasNodeSpec(
                        name=name,
                        title=NODE_NAMES[self.language].get(name, name),
                        branch="legacy",
                        status=self.status_text(data.get("status", "pending")),
                        status_key=data.get("status", "pending"),
                        message=self.localized_message(data.get("message", "")),
                        requires=[],
                    )
                )
        self.workflow_canvas.render_workflow(specs)

    def render_templates(self) -> None:
        while self.template_grid.count():
            item = self.template_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        query = self.template_search.text().strip().lower()
        position = 0
        for key, nodes in self.recipe_nodes.items():
            info = RECIPE_INFO.get(key, {}).get(self.language, (key, "", "", ""))
            searchable = " ".join([key, *info]).lower()
            if query and query not in searchable:
                continue
            accent = RECIPE_COLORS.get(key, "#F28B2C")
            card = ClickableCard(key, accent)
            card.setMinimumHeight(132)
            card.clicked.connect(lambda value, recipe=key: self.open_recipe(recipe))
            layout = QVBoxLayout(card)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(7)
            header = QHBoxLayout()
            header.setSpacing(10)
            icon_label = QLabel()
            icon_path = Path(__file__).resolve().parent / "assets" / "icons" / RECIPE_ICONS.get(key, "full.svg")
            icon = QPixmap(str(icon_path)).scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon)
            icon_label.setFixedSize(34, 34)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("background:#232B33;border:1px solid #3A434F;border-radius:8px")
            header.addWidget(icon_label)
            title_column = QVBoxLayout()
            title_column.setSpacing(0)
            title_row = QHBoxLayout()
            title = QLabel(info[0])
            title.setStyleSheet("font-weight:700;font-size:13px;color:#F5F8FB")
            count = QLabel(f"{len(nodes)} {self.tr('nodes')}")
            count.setObjectName("Muted")
            title_row.addWidget(title, 1)
            title_row.addWidget(count)
            title_column.addLayout(title_row)
            use = QLabel(info[1])
            use.setObjectName("Muted")
            title_column.addWidget(use)
            header.addLayout(title_column, 1)
            layout.addLayout(header)
            desc = QLabel(info[3])
            desc.setWordWrap(True)
            desc.setObjectName("Muted")
            layout.addWidget(desc, 1)
            tags_row = QHBoxLayout()
            tags_row.setSpacing(4)
            for tag in info[2].split("、"):
                chip = QLabel(tag.strip())
                chip.setStyleSheet(
                    "color:#9AA5B1;background:#242B33;border:1px solid #3A434F;"
                    "border-radius:8px;padding:2px 7px;font-size:10px"
                )
                tags_row.addWidget(chip)
            tags_row.addStretch(1)
            layout.addLayout(tags_row)
            button = QPushButton(self.tr("template_open"))
            button.clicked.connect(lambda _=False, recipe=key: self.open_recipe(recipe))
            layout.addWidget(button, 0, Qt.AlignLeft)
            self.template_grid.addWidget(card, position // 3, position % 3)
            position += 1

    def render_queue(self) -> None:
        headers = [self.tr("queue_updated"), self.tr("product"), self.tr("recipe"), self.tr("progress"), self.tr("status"), self.tr("directory")]
        self.queue_table.setColumnCount(len(headers))
        self.queue_table.setHorizontalHeaderLabels(headers)
        queue_rows = [
            {
                "updated_at": "-",
                "number": item["number"],
                "recipe": item["recipe"],
                "passed": 0,
                "total": len(self.recipe_nodes.get(item["recipe"], [])),
                "running": False,
                "failed": 0,
                "needs_human": 0,
                "path": self.tr("queue_pending"),
                "pending": True,
            }
            for item in self.pending_runs
        ] + self.run_states
        self.queue_table.setRowCount(len(queue_rows))
        for row, run in enumerate(queue_rows):
            status = (
                "running" if run["running"]
                else "failed" if run["failed"]
                else "needs_human" if run["needs_human"]
                else "pending" if run.get("pending")
                else "passed"
            )
            values = [run["updated_at"], run["number"], self.recipe_title(run["recipe"]), f"{run['passed']}/{run['total']}", self.status_text(status), run["path"]]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 5:
                    item.setToolTip(run["path"])
                self.queue_table.setItem(row, column, item)
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setStretchLastSection(True)

    def render_backends(self) -> None:
        while self.backend_grid.count():
            item = self.backend_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, backend in enumerate(backend_catalog()):
            accent = "#63C8B8" if backend.key == "none" else "#F2A65A"
            card = Card(accent)
            card.setMinimumHeight(150)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(13, 10, 13, 10)
            layout.setSpacing(6)
            title = QLabel(backend.name)
            title.setStyleSheet("color:#F5F8FB;font-size:13px;font-weight:700")
            state = self.tr("available") if backend.available else self.tr("no_key")
            state_color = "#63C8B8" if backend.available else "#E5484D"
            state_label = QLabel(state)
            state_label.setStyleSheet(
                f"color:{state_color};border:1px solid {state_color};"
                "border-radius:9px;padding:2px 8px;font-size:10px;font-weight:700"
            )
            state_label.setMaximumWidth(90)
            state_label.setAlignment(Qt.AlignCenter)
            title_row = QHBoxLayout()
            title_row.addWidget(title, 1)
            title_row.addWidget(state_label)
            description = QLabel(backend.description)
            description.setWordWrap(True)
            description.setObjectName("Muted")
            key_note = self.tr("no_key_needed") if not backend.requires_key else self.tr("key_note")
            note = QLabel(key_note)
            note.setWordWrap(True)
            note.setObjectName("Muted")
            layout.addLayout(title_row)
            layout.addWidget(description, 1)
            layout.addWidget(note)
            self.backend_grid.addWidget(card, index // 2, index % 2)
        self.backend_grid.setColumnStretch(0, 1)
        self.backend_grid.setColumnStretch(1, 1)

    def render_logs(self) -> None:
        headers = [self.tr("time"), self.tr("product"), self.tr("recipe"), self.tr("node"), self.tr("status"), self.tr("message")]
        self.log_table.setColumnCount(len(headers))
        self.log_table.setHorizontalHeaderLabels(headers)
        rows = [
            (
                entry.updated_at,
                entry.number,
                self.recipe_title(entry.recipe),
                NODE_NAMES[self.language].get(entry.node, entry.node),
                entry.status,
                self.localized_message(entry.message),
            )
            for entry in collect_logs()
        ]
        self.log_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                display = self.status_text(value) if column == 4 else str(value)
                item = QTableWidgetItem(display)
                if column == 5:
                    item.setToolTip(str(value))
                self.log_table.setItem(row, column, item)
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setStretchLastSection(True)

    def render_help(self) -> None:
        if self.language == "zh":
            html = """
            <h3>快捷键</h3><p>F1：打开帮助<br>Ctrl+R：刷新数据</p>
            <h3>状态</h3><p>通过 / 运行中 / 需人工 / 失败 / 等待上游</p>
            <h3>生产原则</h3><p>原图只读；属性数据是 QC 依据；AI 只作为可选后端；C 类图片应补拍或补工艺数据。</p>
            """
        else:
            html = """
            <h3>Shortcuts</h3><p>F1: Help<br>Ctrl+R: Refresh</p>
            <h3>States</h3><p>Passed / Running / Needs human / Failed / Blocked</p>
            <h3>Principles</h3><p>Source images are read-only; attributes drive QC; AI is optional; Class C images need reshoot or product data.</p>
            """
        self.help_browser.setHtml(html)

    def render_chips(self) -> None:
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        running = sum(bool(run["running"]) for run in self.run_states)
        human = sum(run["needs_human"] for run in self.run_states)
        values = [
            (self.tr("product_count"), str(len(self.products)), "#63B3ED"),
            (self.tr("run_count"), str(len(self.run_states)), "#63C8B8"),
            (self.tr("active_count"), str(running), "#F5A524"),
            (self.tr("human_count"), str(human), "#EF8FB5"),
        ]
        for label, value, color in values:
            chip = QLabel(f"{value} {label}")
            chip.setStyleSheet(
                f"background:#222931;border:1px solid {color}55;border-radius:10px;"
                f"padding:2px 9px;color:{color};font-size:11px;font-weight:650"
            )
            self.chips_layout.addWidget(chip)

    def retranslate(self) -> None:
        self.setWindowTitle(f"{self.tr('app_title')} {APP_VERSION}")
        self.brand_label.setText("LongY")
        self.brand_sublabel.setText("Studio")
        self.section_nav.setText(self.tr("nav_workbench"))
        self.section_products.setText(self.tr("products"))
        for key, button in self.nav_buttons.items():
            button.setText(self.tr(f"nav_{key}"))
        self.refresh_button.setText(self.tr("refresh"))
        self.language_button.setText(self.tr("language_button"))
        self.language_button_side.setText("EN" if self.language == "zh" else "中文")
        self.product_search.setPlaceholderText(self.tr("search_products"))
        self.new_type_edit.setPlaceholderText(self.tr("new_type") if self.language == "en" else "上衣 / 裤子 / 套装")
        self.attribute_group_label.setText(self.tr("attribute_group"))
        attribute_keys = [
            "color",
            "pattern_direction",
            "button_count",
            "collar_style",
            "sleeve_style",
            "pocket_list",
            "seam_list",
            "lining",
            "fabric_texture",
            "must_preserve_list",
        ]
        for label, key in zip(self.attribute_labels, attribute_keys):
            label.setText(self.tr(key))
        current_lining = self.attr_lining_combo.currentData()
        if current_lining is None:
            current_lining = False
        self.attr_lining_combo.blockSignals(True)
        self.attr_lining_combo.clear()
        self.attr_lining_combo.addItem(self.tr("lining_no"), False)
        self.attr_lining_combo.addItem(self.tr("lining_yes"), True)
        self.attr_lining_combo.setCurrentIndex(self.attr_lining_combo.findData(current_lining))
        self.attr_lining_combo.blockSignals(False)
        current_backend = self.backend_combo.currentData() or "none"
        self.backend_combo.blockSignals(True)
        self.backend_combo.clear()
        if self.language == "zh":
            self.backend_combo.addItem("无 AI / 确定性处理", "none")
            self.backend_combo.addItem("OpenRouter 生图", "openrouter")
        else:
            self.backend_combo.addItem("No AI / deterministic", "none")
            self.backend_combo.addItem("OpenRouter image API", "openrouter")
        index = self.backend_combo.findData(current_backend)
        if index >= 0:
            self.backend_combo.setCurrentIndex(index)
        self.backend_combo.blockSignals(False)
        self.page_title.setText(self.tr("workbench_title"))
        self.page_subtitle.setText(self.tr("workbench_sub"))
        self.announcement_label.setText(" · ".join(ANNOUNCEMENTS[self.language]))
        self.product_panel_label.setText(self.tr("product"))
        self.workflow_panel_label.setText(self.tr("node_chain"))
        self.details_panel_label.setText(self.tr("node_details"))
        self.templates_panel_label.setText(self.tr("templates_title"))
        self.queue_panel_label.setText(self.tr("queue_title"))
        self.backends_panel_label.setText(self.tr("backends_title"))
        self.logs_panel_label.setText(self.tr("logs_title"))
        self.help_panel_label.setText(self.tr("help_title"))
        self.new_number_label.setText(self.tr("new_number"))
        self.new_type_label.setText(self.tr("new_type"))
        self.create_button.setText(self.tr("create"))
        self.record_labels[0].setText(self.tr("garment_type"))
        self.record_labels[1].setText(self.tr("input_class"))
        self.record_labels[2].setText(self.tr("pieces"))
        self.record_labels[3].setText(self.tr("capture_state"))
        self.product_json_label.setText(self.tr("product_json"))
        self.save_button.setText(self.tr("save"))
        self.force_check.setText(self.tr("rerun"))
        if self.worker and self.worker.isRunning():
            self.run_button.setText(self.tr("running"))
        elif self.pending_runs:
            self.run_button.setText(self.tr("queued_run"))
        else:
            self.run_button.setText(self.tr("run"))
        self.folder_button.setText(self.tr("open_folder"))
        self.artifact_list.setToolTip(self.tr("artifacts"))
        self.open_artifact_button.setText(self.tr("open_artifact"))
        self.preview_label_title.setText(self.tr("preview"))
        if self.artifact_preview.pixmap().isNull():
            self.artifact_preview.setText(self.tr("preview_empty"))
        self.template_search.setPlaceholderText(self.tr("templates_title"))
        self.status_label.setText(self.tr("status_bar"))
        self.menus["file"].setTitle(self.tr("menu_file"))
        self.menus["view"].setTitle(self.tr("menu_view"))
        self.menus["language"].setTitle(self.tr("menu_language"))
        self.menus["help"].setTitle(self.tr("menu_help"))
        self.menu_actions["refresh"].setText(self.tr("refresh"))
        self.menu_actions["exit"].setText(self.tr("menu_exit"))
        self.menu_actions["help"].setText(self.tr("nav_help"))
        self.menu_actions["about"].setText(self.tr("menu_about"))
        for key, action in self.view_actions.items():
            action.setText(self.tr(f"nav_{key}"))
        for language, action in self.language_actions.items():
            action.setChecked(language == self.language)
        self.render_nodes()
        self.render_queue()
        self.render_logs()
        self.render_backends()
        self.render_help()
        self.render_templates()
        self.render_chips()

    def on_product_selected(self) -> None:
        items = self.product_list.selectedItems()
        if not items:
            return
        number = items[0].data(Qt.UserRole)
        if not number:
            return
        self.current_number = str(number)
        self.settings["last_product"] = self.current_number
        save_settings(self.settings)
        self.current_state = self.state_for(self.current_number, self.current_recipe)
        self.render_product_form()
        self.render_nodes()

    def on_recipe_changed(self) -> None:
        data = self.recipe_combo.currentData()
        if not data:
            return
        self.current_recipe = str(data)
        self.settings["last_recipe"] = self.current_recipe
        save_settings(self.settings)
        self.current_state = self.state_for(self.current_number, self.current_recipe)
        self.render_nodes()

    def on_backend_changed(self) -> None:
        self.settings["backend"] = self.backend_combo.currentData() or "none"
        save_settings(self.settings)

    def open_recipe(self, recipe: str) -> None:
        self.current_recipe = recipe
        self.settings["last_recipe"] = recipe
        save_settings(self.settings)
        self.current_state = self.state_for(self.current_number, self.current_recipe)
        self.switch_page(0, "workbench")
        self.render_recipe_combo()
        self.render_nodes()

    def create_product(self) -> None:
        text = self.new_number_edit.text().strip()
        if not text.isdigit() or int(text) <= 0:
            QMessageBox.warning(self, self.tr("create"), self.tr("select_product"))
            return
        number = int(text)
        if product_path(number).exists():
            QMessageBox.warning(self, self.tr("create"), self.tr("select_product"))
            return
        init_product(number, self.new_type_edit.text().strip() or None)
        self.current_number = str(number)
        self.load_data()
        QMessageBox.information(self, self.tr("create"), self.tr("create_ok"))

    def save_product(self) -> None:
        if not self.current_number:
            return
        try:
            record = json.loads(self.product_json_edit.toPlainText())
            record["id"] = self.current_number
            record["garment_type"] = self.garment_type_edit.text().strip() or record.get("garment_type", "")
            record["input_class"] = self.input_class_combo.currentText()
            record["piece_count"] = int(self.piece_count_edit.text() or 1)
            record["capture_state"] = self.capture_state_edit.text().strip()
            pockets = [value.strip() for value in self.attr_pockets_edit.text().split(",") if value.strip()]
            seams = [value.strip() for value in self.attr_seams_edit.text().split(",") if value.strip()]
            must_preserve = [
                value.strip()
                for value in self.attr_must_edit.toPlainText().splitlines()
                if value.strip()
            ]
            record["attributes"] = {
                "color": self.attr_color_edit.text().strip(),
                "pattern": self.attr_pattern_edit.text().strip(),
                "buttons": self.attr_buttons_spin.value(),
                "collar": self.attr_collar_edit.text().strip(),
                "sleeves": self.attr_sleeve_edit.text().strip(),
                "pockets": pockets,
                "seams": seams,
                "lining": self.attr_lining_combo.currentData() is True,
                "fabric": self.attr_fabric_edit.text().strip(),
                "must_preserve": must_preserve,
            }
            record["must_preserve"] = must_preserve
            save_product(record)
            self.load_data()
            self.statusBar().showMessage(self.tr("save_ok"), 3000)
        except Exception as exc:
            QMessageBox.warning(self, self.tr("json_error"), str(exc))

    def run_workflow(self) -> None:
        if not self.current_number:
            QMessageBox.warning(self, self.tr("run"), self.tr("select_product"))
            return
        backend = self.backend_combo.currentData() or "none"
        if backend != "none":
            answer = QMessageBox.question(self, self.tr("confirm_title"), self.tr("confirm_ai"))
            if answer != QMessageBox.Yes:
                return
        self.save_product()
        record = self.product_records.get(self.current_number)
        if not record:
            return
        item = {
            "number": str(self.current_number),
            "recipe": self.current_recipe,
            "backend": backend,
            "force": self.force_check.isChecked(),
            "record": record,
        }
        if self.worker and self.worker.isRunning():
            self.pending_runs.append(item)
            self.run_button.setText(self.tr("queued_run"))
            self.statusBar().showMessage(self.tr("queued_run"), 2500)
            self.render_queue()
            return
        self._start_worker(item)

    def _start_worker(self, item: dict) -> None:
        record = item["record"]
        self.current_number = item["number"]
        self.current_recipe = item["recipe"]
        self.worker = RunWorker(
            record, item["recipe"], item["backend"], bool(item["force"])
        )
        self.worker.finished_run.connect(self.on_run_finished)
        self.worker.failed_run.connect(self.on_run_failed)
        self.run_button.setEnabled(True)
        self.run_button.setText(self.tr("running"))
        self.worker.start()
        self.statusBar().showMessage(self.tr("run_started"), 3000)

    def on_run_finished(self, state: dict) -> None:
        item = self.worker.item if self.worker else {}
        self.worker = None
        self.current_number = item.get("number", self.current_number)
        self.current_recipe = item.get("recipe", self.current_recipe)
        self.current_state = state
        self.load_data()
        self.statusBar().showMessage(self.tr("run_done"), 4000)
        self._continue_queue()

    def on_run_failed(self, message: str) -> None:
        item = self.worker.item if self.worker else {}
        self.worker = None
        self.current_number = item.get("number", self.current_number)
        self.current_recipe = item.get("recipe", self.current_recipe)
        QMessageBox.critical(self, self.tr("status_failed"), message)
        self.load_data()
        self._continue_queue()

    def _continue_queue(self) -> None:
        if not self.pending_runs:
            self.run_button.setText(self.tr("run"))
            return
        item = self.pending_runs.pop(0)
        self.statusBar().showMessage(self.tr("start_next"), 2500)
        self._start_worker(item)

    def open_run_folder(self) -> None:
        if not self.current_number:
            return
        run_dir, _ = run_paths(int(self.current_number), self.current_recipe)
        if run_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(run_dir)))

    def open_environment_path(self, key: str) -> None:
        paths = {
            "runtime": Path(__file__).resolve().parent,
            "segmentation": Path(__file__).resolve().parent / "assets" / "models",
            "products": ROOT / "workflow_products",
            "outputs": ROOT / "workflow_runs",
        }
        path = paths.get(key)
        if path and path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def show_selected_node_by_name(self, name: str) -> None:
        if not name:
            return
        data = (self.current_state or {}).get("nodes", {}).get(name, {})
        title = NODE_NAMES[self.language].get(name, name)
        html = f"<h3>{title}</h3><p><b>{self.tr('status')}</b>: {self.status_text(data.get('status', 'pending'))}</p><p>{self.localized_message(data.get('message', ''))}</p>"
        self.node_detail_browser.setHtml(html)
        self.artifact_list.clear()
        for artifact in data.get("artifacts", []):
            self.artifact_list.addItem(artifact)
        if self.artifact_list.count():
            self.artifact_list.setCurrentRow(0)
        else:
            self.update_artifact_preview()

    def update_artifact_preview(self) -> None:
        item = self.artifact_list.currentItem()
        if not item:
            self.artifact_preview.setPixmap(QPixmap())
            self.artifact_preview.setText(self.tr("preview_empty"))
            return
        path = ROOT / item.text()
        pixmap = QPixmap(str(path))
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"} or pixmap.isNull():
            self.artifact_preview.setPixmap(QPixmap())
            self.artifact_preview.setText(self.tr("preview_empty"))
            return
        scaled = pixmap.scaled(
            self.artifact_preview.width(),
            self.artifact_preview.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.artifact_preview.setText("")
        self.artifact_preview.setPixmap(scaled)

    def open_selected_artifact(self) -> None:
        item = self.artifact_list.currentItem()
        if not item:
            return
        path = ROOT / item.text()
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--self-test", action="store_true")
        parser.add_argument("--segment-self-test")
        args = parser.parse_args()
        if args.segment_self_test:
            from PIL import Image
            from segmentation import remove_background

            source = Image.open(args.segment_self_test)
            output = _runtime_dir() / "segment_selftest.png"
            remove_background(source).save(output, format="PNG", optimize=True)
            return
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLE)
        app.setWindowIcon(QIcon(str(APP_ICON)))
        window = MainWindow()
        window.show()
        if args.self_test:
            app.processEvents()
            output = _runtime_dir() / "desktop_selftest.png"
            window.grab().save(str(output))
            window.runtime_timer.stop()
            window.hide()
            window.deleteLater()
            app.processEvents()
            del window
            del app
            return
        sys.exit(app.exec())
    except Exception:
        import traceback

        log = _runtime_dir() / "desktop_error.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        raise


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


if __name__ == "__main__":
    main()
