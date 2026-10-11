"""Single-image submission and terminal-result boundaries."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from client import LITE, PRO, SeedreamClient, SeedreamError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.headers = {"x-trace-id": "trace-seedream"}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return json.dumps(self.payload).encode()


@pytest.mark.asyncio
async def test_lite_submit_requests_one_async_image():
    calls = []

    def fake_open(request, timeout):
        calls.append((request.full_url, json.loads(request.data), timeout))
        return FakeResponse({"task_id": "task-123"})

    with patch("client.OPENER.open", side_effect=fake_open):
        result = await SeedreamClient("test-key").submit("A white paper boat")
    assert calls == [
        (
            "https://api.acedata.cloud/seedream/images",
            {
                "model": LITE,
                "prompt": "A white paper boat",
                "size": "2K",
                "output_format": "jpeg",
                "response_format": "url",
                "watermark": True,
                "async": True,
                "sequential_image_generation": "disabled",
            },
            90,
        )
    ]
    assert result["status"] == "submitted"
    assert result["task_id"] == "task-123"
    assert "image_urls" not in result


@pytest.mark.asyncio
async def test_pro_edit_omits_unsupported_lite_parameter():
    with patch(
        "client.OPENER.open", return_value=FakeResponse({"task_id": "task-456"})
    ) as opening:
        await SeedreamClient("test-key").submit(
            "Turn the boat blue",
            model=PRO,
            size="1K",
            image_url="https://example.org/boat.png",
            output_format="png",
        )
    payload = json.loads(opening.call_args.args[0].data)
    assert payload["image"] == "https://example.org/boat.png"
    assert payload["output_format"] == "png"
    assert "sequential_image_generation" not in payload


@pytest.mark.asyncio
async def test_lookup_withholds_preview_until_terminal_success():
    preview = {
        "finished_at": None,
        "response": {
            "success": True,
            "data": [{"image_url": "https://cdn.example.org/preview.jpg"}],
        },
    }
    finished = {
        "finished_at": 123.0,
        "response": {
            "success": True,
            "data": [
                {"image_url": "https://cdn.example.org/final.jpg", "size": "2048x2048"},
                {"error": {"code": "partial_error", "message": "internal supplier"}},
            ],
        },
    }
    with patch(
        "client.OPENER.open",
        side_effect=[FakeResponse(preview), FakeResponse(finished)],
    ) as opening:
        first = await SeedreamClient("test-key").query("task-123")
        last = await SeedreamClient("test-key").query("task-123")
    assert opening.call_count == 2
    assert first["status"] == "pending"
    assert first["image_urls"] == []
    assert last["status"] == "succeeded"
    assert last["image_urls"] == ["https://cdn.example.org/final.jpg"]
    assert last["item_error_codes"] == ["partial_error"]
    assert "supplier" not in str(last)


@pytest.mark.asyncio
async def test_invalid_input_never_submits_a_paid_job():
    with patch("client.OPENER.open") as opening, pytest.raises(SeedreamError):
        await SeedreamClient("test-key").submit(" ")
    assert opening.call_count == 0
    with patch("client.OPENER.open") as opening, pytest.raises(SeedreamError):
        await SeedreamClient("test-key").submit("A boat", model="unknown")
    assert opening.call_count == 0
    with patch("client.OPENER.open") as opening, pytest.raises(SeedreamError):
        await SeedreamClient("test-key").submit(
            "A boat", image_url="http://example.org/boat.png"
        )
    assert opening.call_count == 0
