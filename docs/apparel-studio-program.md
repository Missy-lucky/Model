# Apparel Studio 多链路图片生产程序

日期：2026-10-10

## 1. 定位

`LongY_Studio/apparel_studio.py` 是一个服装图片生产工作台引擎。它不是单一生成脚本，而是把服装企业常见的图片资产拆成多条 recipe：

- 服装平面图
- 白底主图
- 细节检查图
- 模特上身图
- 颜色变体
- 市场渠道导出
- 全流程生产

程序的核心思想：

```text
商品资料是唯一事实源
多个 recipe 共享同一批节点
每个节点有状态、产物和失败原因
生图模型只是可插拔后端
默认不调用付费 AI
```

## 2. 已支持的生产链路

### `plan-view`

用于服装平面图：

```text
normalize
-> classify
-> attributes
-> segment
-> plan_view
-> pixel_qc
```

如果商品记录里已有 `plan_view_source`，程序直接复用已确认成品；否则生成模板/关键点任务请求，状态停在 `needs_human`。

### `white-main`

用于白底主图：

```text
normalize
-> segment
-> white_main
-> pixel_qc
```

当前实现会生成 `1536 × 1536` 白底图。该链路只做规范化，不承诺把挂拍图变成工艺平面图。

### `detail-sheet`

用于细节检查：

```text
normalize
-> classify
-> attributes
-> detail_grid
```

输出上、中、下、中心四个区域的细节检查表，便于确认扣子、缝线、腰头、袖口等区域。

### `on-model`

用于模特图：

```text
normalize
-> classify
-> attributes
-> model_brief
-> model_reference_sheet
-> model_generate
-> pixel_qc
```

默认后端为 `none`：

- 会生成模特拍摄 brief。
- 会生成衣服和模特参考卡。
- 会生成生图请求 JSON 和提示词。
- 状态停在 `needs_human`，不会消耗 API。

显式使用：

```powershell
python .\LongY_Studio\apparel_studio.py run --number 172 --recipe on-model --backend openrouter
```

才会调用 OpenRouter 图像编辑接口。

### `colorway`

用于颜色变体：

```text
normalize
-> classify
-> attributes
-> colorway
```

当前先生成颜色变体生产规格。每个颜色必须有对应原图或受控重上色请求，不允许凭空改色。

### `marketplace-pack`

用于渠道导出：

```text
normalize
-> classify
-> attributes
-> channel_exports
```

输出：

- `800 × 800`
- `1536 × 1536`
- `1200 × 1600`

导出来源优先级：

1. 商品记录中的 `marketplace_source`
2. 已确认平面图
3. 白底主图

### `full-studio`

完整生产链：

```text
normalize
-> classify
-> attributes
-> segment
-> plan-view branch
-> white-main branch
-> detail branch
-> model branch
-> colorway branch
-> channel branch
-> pixel QC
-> human final review
```

这个 recipe 用于展示企业式多链路生产结构。任何一条分支缺数据时，只阻塞依赖它的后续节点，不影响其他分支继续执行。

## 3. 商品资料

商品记录位于：

```text
workflow_products/<number>/product.json
```

172 号示例已创建：

```text
workflow_products/172/product.json
```

关键字段：

```json
{
  "id": "172",
  "source": "work_library/IMG_1113.HEIC",
  "garment_type": "shirt",
  "attributes": {
    "buttons": 5,
    "collar": "wide pointed collar",
    "pattern": "vertical stripe"
  },
  "model_references": [
    {
      "key": "modern",
      "path": "model_library/modern-chinese/fullbody-final.png"
    }
  ],
  "colorways": [],
  "plan_view_source": "work_library_plan_view/172.png"
}
```

### 必填属性建议

上衣：

- `buttons`
- `collar`
- `sleeves`
- `pockets`
- `seams`
- `lining`
- `hem`
- `pattern`

裤子：

- `rise`
- `waistband`
- `fly`
- `belt_loops`
- `pockets`
- `waist_stitch_lines`
- `leg_width`
- `taper`
- `hem`

套装：

- `piece_count`
- 每件衣服的独立属性
- 每件衣服的独立素材

## 4. 使用方法

启动原生桌面 GUI：

```powershell
python .\LongY_Studio\desktop_app.py
```

GUI 页面：

- `工作台`：商品资料、节点链路、运行报告
- `模板库`：按用途和关键词筛选生产链路
- `队列`：查看全部运行进度
- `后端`：查看确定性处理与可选生图后端
- `日志`：查看节点提示、人工介入和失败原因
- `帮助`：快捷键、状态定义和生产原则

工作台商品区包含两层编辑：

- 结构化表单：服装类型、输入分类、件数、拍摄状态、颜色、图案方向、扣子数量、领型、袖型、口袋、缝线、内衬、面料和必须保留项。
- 商品 JSON：保留完整数据视图，适合高级字段和批量修正。

查看全部 recipe：

```powershell
python .\LongY_Studio\apparel_studio.py recipes
```

查看节点依赖：

```powershell
python .\LongY_Studio\apparel_studio.py recipes --verbose
```

创建商品记录：

```powershell
python .\LongY_Studio\apparel_studio.py init --number 172 --type shirt
```

只查看某个 recipe 的计划：

```powershell
python .\LongY_Studio\apparel_studio.py plan --number 172 --recipe full-studio
```

运行白底主图链路：

```powershell
python .\LongY_Studio\apparel_studio.py run --number 172 --recipe white-main
```

运行模特图链路，但不调用 AI：

```powershell
python .\LongY_Studio\apparel_studio.py run --number 172 --recipe on-model --backend none
```

生成模特图：

```powershell
python .\LongY_Studio\apparel_studio.py run --number 172 --recipe on-model --backend openrouter
```

查看状态：

```powershell
python .\LongY_Studio\apparel_studio.py status --number 172 --recipe on-model
```

强制重跑：

```powershell
python .\LongY_Studio\apparel_studio.py run --number 172 --recipe white-main --force
```

## 5. 运行产物

每个商品和 recipe 的运行目录独立：

```text
workflow_runs/<number>/<recipe>/
```

例如：

```text
workflow_runs/172/white-main/
  01-normalized.jpg
  04-segmentation.png
  05-white-main.png
  14-pixel-qc.json
  state.json
  report.html
```

模特链路：

```text
workflow_runs/172/on-model/
  01-normalized.jpg
  08-model-brief.json
  08-model-brief.md
  09-model-reference-sheet.jpg
  10-model-request.json
  10-model-prompt.txt
  state.json
  report.html
```

`report.html` 是本地可打开的工作流状态页面，每个节点显示：

- 状态
- 所属分支
- 依赖
- 提示信息
- 输出产物

## 6. 状态含义

| 状态 | 含义 |
| --- | --- |
| `pending` | 等待执行 |
| `running` | 正在执行 |
| `passed` | 已通过 |
| `failed` | 节点执行失败 |
| `needs_human` | 需要人工补数据、确认或选择 |
| `blocked` | 上游节点未完成 |
| `skipped` | 已跳过 |

## 7. 与企业工作流的对应关系

| 企业环节 | 程序节点 |
| --- | --- |
| 商品资料 / PIM | `product.json`、`attributes` |
| 拍摄输入审核 | `normalize`、`classify` |
| 抠图修图 | `segment`、`white_main` |
| 工艺平面图 | `plan_view` |
| 细节审版 | `detail_grid` |
| 模特拍摄 / AI 模特图 | `model_brief`、`model_reference_sheet`、`model_generate` |
| 颜色变体管理 | `colorway` |
| 渠道交付 | `channel_exports` |
| 质检 | `pixel_qc`、`final_review` |

## 8. 当前边界

当前程序是可运行的桌面工作台，还不是完整生产系统：

1. `plan_view` 尚未实现部件级模板变形。
2. `white_main` 是确定性白底合成，不等同于最终工艺平面图。
3. `colorway` 只生成生产规格，不做自动重上色。
4. `model_generate` 默认不调用 AI。
5. 原生 GUI 已包含关键属性表单和商品 JSON 编辑。
6. 人工关键点标注界面尚未实现。
7. 属性 QC 目前依赖商品 JSON，尚未自动识别扣子和缝线数量。

## 9. 下一步开发顺序

1. 实现上衣关键点标注。
2. 实现衣身、左袖、右袖三个部件的模板映射。
3. 实现裤子腰头和左右裤腿模板映射。
4. 实现扣子、缝线、条纹细节回填。
5. 增加属性 QC：扣子数量、缝线数量、条纹方向。
6. 增加批量队列，按 A / B / C 图片类型选择 recipe。
7. 将 OpenRouter、Qwen-Image-Edit、ComfyUI 做成同级后端适配器。

## 10. 设计结论

这个程序把“多图片生成”从单个大模型调用拆成了企业式生产结构：

```text
数据层：商品属性和素材索引
处理层：分割、白底、细节、导出
生成层：可插拔模特图后端
质检层：像素 QC + 属性 QC + 人工审核
状态层：每个节点可追踪、可重跑
```

这样可以同时支持平面图、模特图、颜色变体和渠道图，而不是把所有目标塞进一个提示词。
