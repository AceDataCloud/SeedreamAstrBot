# AstrBot 的 Seedream 插件

通过自己的 Ace Data Cloud 账号，在 AstrBot 对话中生成或编辑单张 Seedream 图片。`seedream_generate_image` 提交一次任务，`seedream_get_task` 用相同 ID 查询到完成。

[English guide](../README.md) · [Seedream 图片 API](https://platform.acedata.cloud/documents/seedream-images) · [Seedream 任务 API](https://platform.acedata.cloud/documents/seedream-tasks) · [当前价格](https://platform.acedata.cloud/services/seedream?tab=pricing)

## 搜索与安装

在 AstrBot WebUI 打开 **Extensions → Plugins → AstrBot Plugin Market**，搜索 **Seedream**。核对卡片名称 **Seedream by Ace Data Cloud**、作者 **acedatacloud** 和 [Seedream 服务图标](https://cdn.acedata.cloud/9egrbn.png)，安装后到 **Installed** 检查加载状态。

AstrBot Cloud 官方上架尚未完成。源码合并发布后，可在 **Installed → Install (+) → Install from URL** 输入 `https://github.com/AceDataCloud/SeedreamAstrBot` 预览。URL 安装不代表官方市场已经可用。

## 配置 Key

到 [Ace Data Cloud Applications](https://platform.acedata.cloud/console/applications) 复制 General application 的生成 API Key，或创建同时允许 `/seedream/images` 和 `/seedream/tasks` 的 Key。提交前检查当前价格和余额。在插件设置 **Ace Data Cloud generation API key with Seedream access** 中粘贴 Key 本身；不要加 `Bearer `，也不要使用 `platform-...` 管理 Token。AstrBot WebUI 会遮蔽字段，但数据目录会保存原值，请保护该目录。

选择支持工具调用的聊天模型，在当前 Profile 和 Persona 中允许两个 Seedream 工具。

## 只生成一次，再查同一任务

向机器人发送：

> 只调用一次 `seedream_generate_image`，生成蓝色背景上的白色纸船产品照。模型用 `doubao-seedream-5-0-260128`，尺寸 `2K`，告诉我 task ID。

工具向 `POST /seedream/images` 提交一次异步任务，返回 `status: submitted` 和 task ID；此时并非最终图片。保留 ID，再问：

> 用 `seedream_get_task` 查询原来的 `<task_id>`，告诉我状态和最终图片 URL，不要再次生成。

若仍为 pending，稍后查询**同一 ID**。只有 `status: succeeded`、`success: true` 且返回最终 HTTPS `image_url` 才表示图片可用。插件不会自动重试付费请求，并对 Lite 模型显式关闭关联组图。

若要编辑有处理权限的图片，将其公开 HTTPS 地址传为 `image_url`，在 `prompt` 描述修改。可选 `doubao-seedream-5-0-260128`（5.0 Lite，`2K`/`3K`/`4K`）或 `doubao-seedream-5-0-pro-260628`（5.0 Pro，`1K`/`2K`）；`output_format` 可为 `jpeg` 或 `png`，`watermark` 默认 true。首版只处理单张生成或单张参考图编辑；关联组图、流式、联网搜索、图层拆分、透明背景编辑和 Base64 返回暂未包含。

## 用量与排障

在 Ace Data Cloud 用量页按返回的 trace ID 匹配。图片计价与模型、输出尺寸和实际结果有关，请以当前价格为准。任务查询只读取已有作业，不会再提交生成。若结果存在单项错误，工具会把错误代码与成功图片链接分开返回。

| 现象 | 检查项 |
| --- | --- |
| 插件加载失败 | AstrBot 版本、**Failed to Load Plugins**、**Data & Logs → Logs**。 |
| 看不到工具 | 插件启用、当前 Profile/Persona 允许两个工具、聊天模型支持工具调用。 |
| HTTP 401/403 | Key 类型、两个 Allowed APIs 路径和账号权限。 |
| 提交后网络错误 | 再次生成前查请求历史；超时请求可能已创建付费任务。 |
| 任务 pending | 稍后查询同一个 task ID。 |
| 任务 failed | 按 task ID 或 trace ID 查看请求历史。 |

Key 只发送到 `https://api.acedata.cloud`，重定向会被拒绝。插件仅向模型返回任务状态、最终图片链接和公开单项错误代码，不透出上游原始数据。运行只需 Python 标准库。

## 已验证的本地运行与图标

官方 AstrBot `v4.28.2` 的隔离实例注册了两个工具。ChatUI 用 `doubao-seedream-5-0-260128` 提交一次 2K 图片任务，并通过 `seedream_get_task` 查询同一 task ID，没有再次生成。最终 JPEG 为 HTTP 200、`image/jpeg`，解码尺寸 2048×2048。生成 trace 精确匹配一条成功的 `/seedream/images` 用量，实扣 0.333 Credits；当前成本规则为折扣前 0.37 Credits。详见[脱敏证据](../tests/e2e-results.json)。这仍是本地 editable 安装；Cloud 审核、官方市场安装及市场安装后的首次调用尚未完成。

`logo.png` 是未经修改的 340×340 [当前 Seedream 服务图标](https://cdn.acedata.cloud/9egrbn.png)，SHA-256 `1ac6be85f2dfe64cb280c010a9894d5df7d9d34304f0fbd41b7b7170caa699d4`。
