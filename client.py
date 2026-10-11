"""Single-image Seedream generation and task lookup for AstrBot."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_BASE = "https://api.acedata.cloud"
LITE = "doubao-seedream-5-0-260128"
PRO = "doubao-seedream-5-0-pro-260628"
SIZES = {LITE: {"2K", "3K", "4K"}, PRO: {"1K", "2K"}}


class _NoRedirect(HTTPRedirectHandler):
    """Never forward the configured key to another host."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        """Reject every API redirect."""
        return


OPENER = build_opener(_NoRedirect)


class SeedreamError(RuntimeError):
    """An error safe to return to an AstrBot conversation."""


def _valid_https_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return bool(
        parsed.scheme == "https"
        and parsed.netloc
        and not parsed.username
        and not parsed.password
    )


class SeedreamClient:
    """Submit one image or query an existing image task."""

    def __init__(self, api_key: str) -> None:
        token = api_key.strip()
        if (
            not token
            or token.lower().startswith("bearer ")
            or token.startswith("platform-")
        ):
            raise SeedreamError(
                "Set an Ace Data Cloud generation API key in plugin settings."
            )
        self._api_key = token

    def _post(self, path: str, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        request = Request(
            API_BASE + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self._api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "AceDataCloudAstrBot/0.1.0",
            },
            method="POST",
        )
        try:
            with OPENER.open(request, timeout=90) as response:
                body = json.load(response)
                trace_id = response.headers.get(
                    "x-trace-id", ""
                ) or response.headers.get("x-request-id", "")
        except HTTPError as exc:
            raise SeedreamError(
                f"Ace Data Cloud returned HTTP {exc.code}. Check service access and request history."
            ) from None
        except (URLError, TimeoutError, OSError):
            raise SeedreamError(
                "The API connection failed. Check request history before submitting again."
            ) from None
        except (ValueError, UnicodeError):
            raise SeedreamError(
                "The API returned invalid JSON. Check request history before retrying."
            ) from None
        if not isinstance(body, dict):
            raise SeedreamError("The API returned an unexpected response format.")
        return body, str(body.get("trace_id") or trace_id)

    async def submit(
        self,
        prompt: str,
        model: str = LITE,
        size: str = "2K",
        image_url: str = "",
        output_format: str = "jpeg",
        watermark: bool = True,
    ) -> dict[str, Any]:
        """Submit one asynchronous image job without a paid retry."""
        prompt = prompt.strip()
        if not prompt or len(prompt) > 4000:
            raise SeedreamError("Provide an image prompt of 1–4000 characters.")
        if model not in SIZES:
            raise SeedreamError(
                "Choose the supported Seedream 5.0 Lite or Pro model ID."
            )
        if size not in SIZES[model]:
            raise SeedreamError("Choose a size supported by this model.")
        if output_format not in {"jpeg", "png"}:
            raise SeedreamError("Output format must be jpeg or png.")
        if not isinstance(watermark, bool):
            raise SeedreamError("Watermark must be true or false.")
        if image_url and not _valid_https_url(image_url):
            raise SeedreamError("Provide an authorized HTTPS reference image URL.")
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "output_format": output_format,
            "response_format": "url",
            "watermark": watermark,
            "async": True,
        }
        if model == LITE:
            payload["sequential_image_generation"] = "disabled"
        if image_url:
            payload["image"] = image_url
        body, trace_id = await asyncio.to_thread(
            self._post, "/seedream/images", payload
        )
        if body.get("success") is False or body.get("error"):
            raise SeedreamError(
                "Image submission was rejected. Check request history before trying again."
            )
        task_id = body.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise SeedreamError(
                "No task ID was returned. Check request history before submitting again."
            )
        return {
            "status": "submitted",
            "task_id": task_id,
            "trace_id": trace_id,
            "next_step": "Query this same task ID; do not submit another image while it is pending.",
        }

    async def query(self, task_id: str) -> dict[str, Any]:
        """Return final image URLs only after the existing task finishes."""
        task_id = task_id.strip()
        if not task_id or len(task_id) > 128:
            raise SeedreamError("Pass the exact task ID from Seedream submission.")
        body, trace_id = await asyncio.to_thread(
            self._post,
            "/seedream/tasks",
            {"id": task_id, "action": "retrieve"},
        )
        if body.get("success") is False or body.get("error"):
            raise SeedreamError("Task lookup failed. Check request history.")
        response = body.get("response")
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except ValueError:
                response = None
        if not isinstance(response, dict):
            response = {}
        trace_id = str(response.get("trace_id") or trace_id)
        if response.get("success") is False or response.get("error"):
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "failed",
                "success": False,
                "image_urls": [],
            }
        if ("finished_at" in body and body["finished_at"] is None) or (
            response and response.get("success") is not True
        ):
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "pending",
                "success": False,
                "image_urls": [],
            }
        items = response.get("data")
        if not isinstance(items, list):
            return {
                "task_id": task_id,
                "trace_id": trace_id,
                "status": "pending",
                "success": False,
                "image_urls": [],
            }
        urls = [
            item["image_url"]
            for item in items
            if isinstance(item, dict)
            and isinstance(item.get("image_url"), str)
            and _valid_https_url(item["image_url"])
        ]
        error_codes = [
            str(item["error"].get("code") or "image_failed")
            for item in items
            if isinstance(item, dict) and isinstance(item.get("error"), dict)
        ]
        return {
            "task_id": task_id,
            "trace_id": trace_id,
            "status": "succeeded" if urls else "failed",
            "success": bool(urls),
            "image_urls": urls,
            "image_count": len(urls),
            "item_error_codes": error_codes,
        }
