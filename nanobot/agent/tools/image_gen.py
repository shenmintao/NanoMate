"""Image generation tool supporting both OpenAI and Gemini API formats."""

import base64
import time
import uuid
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool
from nanobot.config.paths import get_media_dir


class ImageGenTool(Tool):
    """Generate images via OpenAI or Gemini API (auto-detects format based on model name)."""

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
            model: Model name (e.g., "dall-e-3", "gemini-3-pro-image-preview")
            proxy: Optional HTTP/SOCKS proxy URL
        """
        self._api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.proxy = proxy

    def _is_gemini_model(self) -> bool:
        """Check if the model uses Gemini API format."""
        return "gemini" in self.model.lower() and "image" in self.model.lower()

    @property
    def name(self) -> str:
        return "image_gen"

    @property
    def description(self) -> str:
        return (
            "Generate an image from a text prompt. "
            "IMPORTANT: After generating, you MUST call the 'message' tool "
            "with the returned file path in the 'media' parameter to send the image to the user. "
            "Do not just reply with text - the user expects to receive the actual image."
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

        # Route to appropriate implementation based on model
        if self._is_gemini_model():
            return await self._execute_gemini(prompt, size)
        else:
            return await self._execute_openai(prompt, size, quality, style)

    async def _execute_openai(
        self,
        prompt: str,
        size: str | None,
        quality: str,
        style: str,
    ) -> str:
        """Execute image generation using OpenAI format."""
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
            "ImageGen (OpenAI): model={} size={} quality={} prompt={!r}",
            self.model,
            size,
            quality,
            prompt[:80],
        )

        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=120.0,
                trust_env=True,
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

    async def _execute_gemini(
        self,
        prompt: str,
        size: str | None,
    ) -> str:
        """Execute image generation using Gemini format."""
        # Map size to Gemini's aspectRatio and image_size
        aspect_ratio = "1:1"
        image_size = "2K"

        if size:
            # Parse size like "1024x1024" or "1792x1024"
            parts = size.lower().split('x')
            if len(parts) == 2:
                try:
                    w, h = int(parts[0]), int(parts[1])
                    # Determine aspect ratio
                    if w == h:
                        aspect_ratio = "1:1"
                    elif w > h:
                        if w / h >= 1.7:
                            aspect_ratio = "16:9"
                        else:
                            aspect_ratio = "4:3"
                    else:
                        if h / w >= 1.7:
                            aspect_ratio = "9:16"
                        else:
                            aspect_ratio = "3:4"

                    # Determine resolution tier
                    max_dim = max(w, h)
                    if max_dim <= 1024:
                        image_size = "1K"
                    elif max_dim <= 2048:
                        image_size = "2K"
                    else:
                        image_size = "4K"
                except ValueError:
                    pass

        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "image_size": image_size,
                },
            },
        }

        logger.info(
            "ImageGen (Gemini): model={} aspectRatio={} size={} prompt={!r}",
            self.model,
            aspect_ratio,
            image_size,
            prompt[:80],
        )

        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=600.0,  # Gemini can be slower, especially for 4K
                trust_env=True,
            ) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Parse Gemini response format
                try:
                    parts = data["candidates"][0]["content"]["parts"]
                    image_part = next(p for p in parts if "inlineData" in p)
                    b64_data = image_part["inlineData"]["data"]
                    return await self._save_base64(b64_data)
                except (KeyError, IndexError, StopIteration):
                    snippet = str(data)[:500]
                    return f"Error: No image data in Gemini API response: {snippet}"

        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
                error_msg = error_detail.get("error", {}).get("message", e.response.text[:300])
            except Exception:
                error_msg = e.response.text[:300]

            return f"Error: API {e.response.status_code} - {error_msg}"
        except httpx.TimeoutException:
            return "Error: Request timed out (600s). Try again or use a smaller size."
        except Exception as e:
            logger.error("ImageGen (Gemini) error: {}", e)
            return f"Error generating image: {e}"

    async def _save_base64(self, b64_data: str) -> str:
        """Save base64-encoded image to file."""
        try:
            media_dir = get_media_dir("image_gen")
            fname = f"gen_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
            path = media_dir / fname
            path.write_bytes(base64.b64decode(b64_data))
            logger.info("ImageGen: saved {}", path)
            return f"✓ Image generated successfully.\nFile path: {path}\n\nNext step: Call the 'message' tool with media=['{path}'] to send this image to the user."
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
                return f"✓ Image generated successfully.\nFile path: {path}\n\nNext step: Call the 'message' tool with media=['{path}'] to send this image to the user."
        except Exception as e:
            return f"Error downloading image: {e}"
