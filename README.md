# Seedream for AstrBot

Generate or edit one Seedream image in an AstrBot conversation through your own Ace Data Cloud account. The tools are `seedream_generate_image` and `seedream_get_task`; the first submits one job, and the second retrieves the same task until it finishes.

[简体中文指南](readme/README_zh_Hans.md) · [Seedream Images API](https://platform.acedata.cloud/documents/seedream-images) · [Seedream Tasks API](https://platform.acedata.cloud/documents/seedream-tasks) · [Current prices](https://platform.acedata.cloud/services/seedream?tab=pricing)

## Find and install

In AstrBot WebUI, open **Extensions → Plugins → AstrBot Plugin Market** and search **Seedream**. Confirm the card says **Seedream by Ace Data Cloud**, the author is **acedatacloud**, and the logo matches the [Seedream service icon](https://cdn.acedata.cloud/9egrbn.png). Install it, then check **Installed** for load errors.

The official AstrBot Cloud listing has not yet been published. After the source release is merged, **Installed → Install (+) → Install from URL** with `https://github.com/AceDataCloud/SeedreamAstrBot` can preview it. A URL installation does not prove official market availability.

## Configure your key

In [Ace Data Cloud Applications](https://platform.acedata.cloud/console/applications), copy a generation API key from your General application or create a key that permits both `/seedream/images` and `/seedream/tasks`. Check current pricing and your balance before submitting. Paste the key into the plugin's **Ace Data Cloud generation API key with Seedream access** setting. Do not add `Bearer ` or use a `platform-...` management token. AstrBot masks the field in WebUI but stores the original value in its data directory, which should be protected.

Select a chat model that supports tool calling. Allow both Seedream tools in the conversation's profile and persona.

## Generate once, then query

Ask the bot:

> Use `seedream_generate_image` once to make a clean product photo of a white paper boat on a blue background. Use `doubao-seedream-5-0-260128`, size `2K`, and show me the returned task ID.

The tool sends one asynchronous `POST /seedream/images` request. It returns `status: submitted` and a task ID, not a finished image. Keep that ID and ask:

> Use `seedream_get_task` with the exact task ID `<task_id>`. Tell me its status and final image URL. Do not generate another image.

If pending, query the same ID later. Only `status: succeeded`, `success: true`, and a final HTTPS `image_url` mean an image is ready. The plugin never retries a paid submission automatically and explicitly disables related image-set generation for the Lite model.

To edit an image you own or may process, include its public HTTPS URL as `image_url` and describe the desired change in `prompt`. The supported models are `doubao-seedream-5-0-260128` (5.0 Lite, `2K`/`3K`/`4K`) and `doubao-seedream-5-0-pro-260628` (5.0 Pro, `1K`/`2K`). Choose `jpeg` or `png` as `output_format`; `watermark` defaults to true. This first version handles one generated image or one input image for editing. Related image sets, streaming, web search, layer decomposition, transparent-background edits, and Base64 results are outside its scope.

## Verify and troubleshoot

In Ace Data Cloud usage, match a returned trace ID when available. Image pricing depends on model, output size, and actual result; check current pricing instead of assuming a fixed amount. A task lookup reads an existing job and does not submit a second generation. If the result contains per-item errors, the tool reports their codes separately from successful final URLs.

| Symptom | Check |
| --- | --- |
| Plugin fails to load | AstrBot version, **Failed to Load Plugins**, and **Data & Logs → Logs**. |
| Tools are missing | Plugin enabled, active profile and persona allow both tools, chat model supports tool calling. |
| HTTP 401/403 | Key type, both allowed API paths, and account access. |
| Network error after submission | Inspect request history before generating again; a timeout may already have created a paid task. |
| Pending task | Query the same task ID later. |
| Failed task | Use the task or trace ID to inspect request history. |

The key goes only to `https://api.acedata.cloud`; redirects are rejected. The plugin exposes only task status, final image URLs, and public item error codes to the model, without raw provider data. It uses Python's standard library and needs no runtime package installation.

## Verified local run and brand asset

On official AstrBot `v4.28.2`, an isolated editable installation registered both tools. ChatUI submitted one `doubao-seedream-5-0-260128` 2K image job and later queried the same task ID through `seedream_get_task`, without another generation. The final JPEG responded HTTP 200, `image/jpeg`, and decoded at 2048×2048. The exact generation trace matched a successful `/seedream/images` usage row with 0.333 Credits deducted; the current cost rule lists 0.37 Credits before the account discount. See the [sanitized evidence](tests/e2e-results.json). This is a local editable installation; official Cloud review, market installation, and a first call from a market installation remain open.

`logo.png` is the unmodified 340×340 [current Seedream service icon](https://cdn.acedata.cloud/9egrbn.png), SHA-256 `1ac6be85f2dfe64cb280c010a9894d5df7d9d34304f0fbd41b7b7170caa699d4`.
