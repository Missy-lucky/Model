# Model 图库与成品平面图

这个仓库包含服装原图库、平面图成品、生成脚本和相关模型资料。大多数使用者只需要下载成品平面图，不需要克隆整个约 2GB 的仓库。

## 只下载成品平面图

### 方式一：直接下载 ZIP

点击下面的链接会下载 `plan-view-only` 分支的压缩包，里面只有成品平面图：

<https://github.com/Missy-lucky/Model/archive/refs/heads/plan-view-only.zip>

这是最简单的方式，不需要安装 Git。

### 方式二：浅克隆成品图分支

如果安装了 Git，在 PowerShell、CMD、Terminal 或 Bash 中执行：

```bash
git clone --depth 1 --branch plan-view-only https://github.com/Missy-lucky/Model.git
```

克隆完成后，`Model` 目录里就是成品图，不包含原图库、脚本和归档文件。

以后想更新成品图，可以进入该目录执行：

```bash
git fetch origin
git reset --hard origin/plan-view-only
```

### 方式三：只检出主仓库中的成品图目录

如果希望保留主分支结构，但只下载 `work_library_plan_view` 目录，可以使用 sparse checkout：

```bash
git clone --filter=blob:none --no-checkout https://github.com/Missy-lucky/Model.git
cd Model
git sparse-checkout set work_library_plan_view
git checkout main
```

完成后只有 `work_library_plan_view` 目录会被下载到本地。

## 在线浏览

成品图目录：

<https://github.com/Missy-lucky/Model/tree/main/work_library_plan_view>

成品图专用分支：

<https://github.com/Missy-lucky/Model/tree/plan-view-only>

## 文件说明

- `work_library/`：服装原图库。
- `work_library_plan_view/`：主分支中的成品平面图目录。
- `work_library/final_plan_view_mapping.csv`：编号、原文件名和输出文件名的映射表。
- `py/`、`ps1/`：批量生成和质检脚本。
- `model_library/`、`shop_model_800/`：其他模型展示图和模型资料。
- `_archive/`：历史试错版本和缓存归档。

## 当前进度

当前成品图包括：

- `1.png` 到 `8.png`：早期确认的 800×800 成品。
- `9.png` 到 `77.png`：新流程生成的 1536×1536 成品，其中 `72.png` 暂缺。
- `389.png`：已确认的套装精修成品。

后续生成完成后，`plan-view-only` 分支会同步更新。
