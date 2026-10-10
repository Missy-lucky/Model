# LongY Studio

LongY Studio 是本地桌面版服装图片生产工作台，使用 PySide6 原生 GUI，不启动浏览器，也不启动 HTTP 服务。当前版本为 `0.2.0`。

## 启动

双击：

```text
Launch_LongY_Studio_Desktop.bat
```

或在仓库根目录执行：

```powershell
python .\LongY_Studio\desktop_app.py
```

## 界面

LongY Studio 采用深色启动器风格，左侧为 88px 图标导航，主界面使用彩色卡片、状态芯片和可缩放工作流画布。

- 启动页：视觉 Hero、生产统计、环境健康、快速启动、最近运行。
- 工作台：商品搜索、结构化属性、工作流画布、节点详情、产物预览。
- 模板库：彩色图标卡片、用途标签、节点数、一键进入链路。
- 队列：串行排队和运行进度。
- 后端：确定性处理与 OpenRouter 状态卡。
- 日志：节点提示、人工介入、失败原因。
- 帮助：快捷键、状态说明、生产原则。

## 语言

- 默认界面为全中文。
- 点击右上角 `EN` 切换英文。
- 英文界面点击 `中文` 切回中文。
- 语言选择保存在 `desktop_settings.json`。

## 快捷键

- `F1`：打开帮助。
- `Ctrl+R`：刷新数据。
- `Ctrl+Q`：退出。

## 生产链路

- `plan-view`：服装平面图。
- `white-main`：白底主图。
- `detail-sheet`：细节检查。
- `on-model`：模特上身图。
- `colorway`：颜色变体。
- `marketplace-pack`：渠道导出。
- `full-studio`：多分支全流程。

## 运行规则

- 默认后端为“无 AI / 确定性处理”。
- 选择 OpenRouter 后会先弹出确认窗口。
- 运行中继续点击“运行”会把新的商品和链路加入串行队列。
- 原始图片库只读。
- 中间产物写入 `workflow_runs/`。
- 商品记录写入 `workflow_products/`。
- 上游节点失败时，下游节点自动进入等待上游状态。

## 分割模型

Git 仓库不提交模型权重。先下载轻量模型：

```powershell
Invoke-WebRequest -Uri "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx" -OutFile ".\LongY_Studio\assets\models\u2netp.onnx"
```

如需更高精度，可将 `u2net.onnx` 放入：

```text
LongY_Studio/assets/models/
```

或用环境变量指定：

```powershell
$env:LONGY_SEGMENTATION_MODEL = "D:\models\u2net.onnx"
```

如果目录中同时存在 `u2net.onnx` 和 `u2netp.onnx`，程序优先使用 `u2net.onnx`。

## 独立版

构建 Windows 独立目录版：

```powershell
powershell -ExecutionPolicy Bypass -File .\LongY_Studio\build_windows.ps1
```

输出目录：

```text
dist/LongY_Studio/
```

构建脚本会先运行自动化测试，再调用 PyInstaller。若只想重新打包：

```powershell
powershell -ExecutionPolicy Bypass -File .\LongY_Studio\build_windows.ps1 -SkipTests
```

## 文件结构

```text
LongY_Studio/
  desktop_app.py
  apparel_studio.py
  studio_core.py
  segmentation.py
  widgets.py
  assets/
  Launch_LongY_Studio_Desktop.bat
```

## 依赖

- PySide6
- Pillow
- NumPy
- pillow-heif
- onnxruntime

## 测试

```powershell
$env:QT_QPA_PLATFORM="offscreen"
python -m pytest -q
```
