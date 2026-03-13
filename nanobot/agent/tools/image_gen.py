"""Image generation tool using OpenAI-compatible API."""

import base64
import time
import uuid
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool
from nanobot.config.paths import get_media_dir


class ImageGenTool(Tool):
    """Generate images via OpenAI-compatible API (supports DALL-E, custom endpoints, etc.)."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "dall-e-3",
        proxy: str | None = None,
    ):
        """
        Initialize image generation tool.

        Args:
            api_key: API key for authentication
            base_url: Base URL for the API (e.g., "https://api.openai.com/v1" or custom relay)
            model: Model name (e.g., "dall-e-3", "dall-e-2", or custom model)
            proxy: Optional HTTP/SOCKS proxy URL
        """
        self._api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.proxy = proxy

    @property
    def name(self) -> str:
        return "image_gen"

    @property
    def description(self) -> str:
        return (
            "Generate an image from a text prompt. "
            "Returns the local file path. Use the message "
            "tool with the media parameter to send it."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the image to generate",
                },
                "size": {
                    "type": "string",
                    "description": "Image size (e.g., '1024x1024', '1792x1024', '1024x1792')",
                },
                "quality": {
                    "type": "string",
                    "enum": ["standard", "hd"],
                    "description": "Image quality (for DALL-E 3, default: standard)",
                },
                "style": {
                    "type": "string",
                    "enum": ["vivid", "natural"],
                    "description": "Image style (for DALL-E 3, default: vivid)",
                },
            },
            "required": ["prompt"],
        }

    async def execute(
        self,
        prompt: str,
        size: str | None = None,
        quality: str = "standard",
        style: str = "vivid",
        **kwargs: Any,
    ) -> str:
        if not self._api_key:
            return "Error: Image generation API key not configured. Set tools.imageGen.apiKey in config."

        # Default size based on common models
        if not size:
            size = "1024x1024"

        url = f"{self.base_url}/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "n": 1,
        }

        # Add optional parameters if provided
        if quality and quality != "standard":
            body["quality"] = quality
        if style and style != "vivid":
            body["style"] = style

        logger.info(
            "ImageGen: model={} size={} quality={} prompt={!r}",
            self.model,
            size,
            quality,
            prompt[:80],
        )

        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=120.0,
                trust_env=True,  # Support proxy from environment variables
            ) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Handle response with either URL or base64
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]

                    if "b64_json" in image_data:
                        return await self._save_base64(image_data["b64_json"])
                    elif "url" in image_data:
                        return await self._download_image(image_data["url"])

                return "Error: No image data in API response"

        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("error", {}).get("message", e.response.text[:300])
            except Exception:
                error_msg = e.response.text[:300]

            return f"Error: API {e.response.status_code} - {error_msg}"
        except httpx.TimeoutException:
            return "Error: Request timed out (120s). Try again or use a smaller size."
        except Exception as e:
            logger.error("ImageGen error: {}", e)
            return f"Error generating image: {e}"

    async def _save_base64(self, b64_data: str) -> str:
        """Save base64-encoded image to file."""
        try:
            media_dir = get_media_dir("image_gen")
            fname = f"gen_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
            path = media_dir / fname
            path.write_bytes(base64.b64decode(b64_data))
            logger.info("ImageGen: saved {}", path)
            return f"Image saved to: {path}"
        except Exception as e:
            return f"Error saving image: {e}"

    async def _download_image(self, url: str) -> str:
        """Download image from URL and save to file."""
        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=60.0,
                trust_env=True,
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                # Detect extension from Content-Type
                content_type = resp.headers.get("content-type", "")
                ext = "png"
                if "jpeg" in content_type or "jpg" in content_type:
                    ext = "jpg"
                elif "webp" in content_type:
                    ext = "webp"

                media_dir = get_media_dir("image_gen")
                fname = f"gen_{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
                path = media_dir / fname
                path.write_bytes(resp.content)

                logger.info("ImageGen: downloaded and saved {}", path)
                return f"Image saved to: {path}"
        except Exception as e:
            return f"Error downloading image: {e}"
