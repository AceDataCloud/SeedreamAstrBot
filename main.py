"""Seedream image tools for AstrBot through Ace Data Cloud."""

from __future__ import annotations

import json

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .client import SeedreamClient, SeedreamError


class SeedreamPlugin(Star):
    """Expose one image submission and one existing-task lookup tool."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @filter.llm_tool(name="seedream_generate_image")
    async def seedream_generate_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        model: str = "doubao-seedream-5-0-260128",
        size: str = "2K",
        image_url: str = "",
        output_format: str = "jpeg",
        watermark: bool = True,
    ) -> str:
        """Submit one billable Seedream image or edit job.

        Args:
            prompt(string): Description of the image or requested edit.
            model(string): Explicit Seedream 5.0 Lite or Pro model ID.
            size(string): Model-supported output size preset.
            image_url(string): Optional authorized HTTPS image to edit.
            output_format(string): jpeg or png.
            watermark(boolean): Whether to add a watermark.

        Returns:
            JSON submission status and task ID, never a finished-image claim.
        """
        try:
            result = await SeedreamClient(self.config.get("api_key", "")).submit(
                prompt, model, size, image_url, output_format, watermark
            )
        except SeedreamError as exc:
            result = {"status": "error", "message": str(exc)}
        return json.dumps(result, ensure_ascii=False)

    @filter.llm_tool(name="seedream_get_task")
    async def seedream_get_task(self, event: AstrMessageEvent, task_id: str) -> str:
        """Query a prior Seedream task ID without another generation.

        Args:
            task_id(string): Exact task ID from seedream_generate_image.

        Returns:
            JSON status and final image URLs only after task completion.
        """
        try:
            result = await SeedreamClient(self.config.get("api_key", "")).query(task_id)
        except SeedreamError as exc:
            result = {"status": "error", "message": str(exc), "task_id": task_id}
        return json.dumps(result, ensure_ascii=False)
