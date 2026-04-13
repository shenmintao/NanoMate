"""Video generation tool using xAI Grok Video API."""

import asyncio
import base64
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool
from nanobot.config.paths import get_media_dir


class VideoGenTool(Tool):
    """Generate, edit, or extend videos via xAI Grok Video API."""

    _POLL_INTERVAL = 5  # seconds between status checks
    _POLL_TIMEOUT = 600  # 10 minutes max wait

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.x.ai/v1",
        model: str = "grok-imagine-video",
        proxy: str | None = None,
        default_duration: int = 6,
        default_resolution: str = "480p",
    ):
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.proxy = proxy
        self.default_duration = default_duration
        self.default_resolution = default_resolution

    @property
    def name(self) -> str:
        return "video_gen"

    @property
    def description(self) -> str:
        return (
            "Generate a video from a text prompt, animate a still image into video, "
            "edit an existing video, or extend a video with new content. "
            "Modes: 'generate' (text/image to video), 'edit' (modify existing video), "
            "'extend' (continue existing video). "
            "Video generation takes several minutes — the tool will poll until complete. "
            "MANDATORY WORKFLOW for any video with a character: "
            "1) FIRST call 'image_gen' with reference_image='__default__' to generate a static image of the character. "
            "2) THEN call 'video_gen' with source_image=<generated image path> to animate it into video. "
            "NEVER skip step 1 — calling video_gen directly without a source_image from image_gen "
            "will produce inconsistent character appearance. "
            "IMPORTANT: After generating, you MUST call the 'message' tool "
            "with the returned file path in the 'media' parameter to send the video to the user. "
            "Do not just reply with text — the user expects to receive the actual video."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text description of the video to generate, editing instructions, or what should happen next (for extend).",
                },
                "source_image": {
                    "type": "string",
                    "description": "Optional: file path to a source image for image-to-video generation. "
                    "The image becomes the starting frame of the video.",
                },
                "source_video": {
                    "type": "string",
                    "description": "Optional: file path to a source video for editing or extending. "
                    "For edit mode: the video to modify (max 8.7s). "
                    "For extend mode: the video to continue (2-15s).",
                },
                "reference_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: list of file paths to reference images. "
                    "Used to incorporate specific people, objects, or styles into the generated video. "
                    "Max 7 images. Use <IMAGE_1>, <IMAGE_2>, etc. in prompt to reference them.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["generate", "edit", "extend"],
                    "description": "Operation mode: 'generate' (text/image to video, default), "
                    "'edit' (modify existing video), 'extend' (continue existing video).",
                },
                "duration": {
                    "type": "integer",
                    "description": "Video duration in seconds (1-15 for generate, 2-10 for extend). "
                    "Not supported for edit mode.",
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Aspect ratio: '1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3'. "
                    "Default: '16:9'. Not supported for edit/extend modes.",
                },
                "resolution": {
                    "type": "string",
                    "enum": ["480p", "720p"],
                    "description": "Video resolution. Default: '480p'. Not supported for edit/extend modes.",
                },
            },
            "required": ["prompt"],
        }

    async def execute(
        self,
        prompt: str,
        source_image: str | None = None,
        source_video: str | None = None,
        reference_images: list[str] | None = None,
        mode: str = "generate",
        duration: int | None = None,
        aspect_ratio: str | None = None,
        resolution: str | None = None,
        **kwargs: Any,
    ) -> str:
        if not self._api_key:
            return "Error: Video generation API key not configured. Set tools.videoGen.apiKey in config."

        if mode == "edit":
            return await self._execute_edit(prompt, source_video)
        elif mode == "extend":
            return await self._execute_extend(prompt, source_video, duration)
        else:
            return await self._execute_generate(
                prompt, source_image, reference_images, duration, aspect_ratio, resolution
            )

    async def _execute_generate(
        self,
        prompt: str,
        source_image: str | None,
        reference_images: list[str] | None,
        duration: int | None,
        aspect_ratio: str | None,
        resolution: str | None,
    ) -> str:
        """Generate video from text prompt, optionally with a source image or reference images."""
        url = f"{self.base_url}/videos/generations"
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
        }

        dur = duration or self.default_duration
        body["duration"] = max(1, min(15, dur))

        if aspect_ratio:
            body["aspect_ratio"] = aspect_ratio
        else:
            body["aspect_ratio"] = "16:9"

        body["resolution"] = resolution or self.default_resolution

        # Image-to-video: source image as starting frame
        if source_image:
            image_data = self._load_image_as_data_uri(source_image)
            if image_data.startswith("Error:"):
                return image_data
            body["image"] = {"url": image_data, "type": "image_url"}
            # Max duration for reference images is 10s
            if reference_images:
                body["duration"] = min(body["duration"], 10)

        # Reference images
        if reference_images and not source_image:
            if len(reference_images) > 7:
                return "Error: Maximum 7 reference images allowed."
            refs = []
            for ref_path in reference_images:
                data_uri = self._load_image_as_data_uri(ref_path)
                if data_uri.startswith("Error:"):
                    return data_uri
                refs.append({"url": data_uri, "type": "image_url"})
            body["reference_images"] = refs
            body["duration"] = min(body["duration"], 10)

        mode_desc = "image-to-video" if source_image else (
            f"ref-images ({len(reference_images)})" if reference_images else "text-to-video"
        )
        logger.info(
            "VideoGen ({}): model={} duration={}s prompt={!r}",
            mode_desc, self.model, body.get("duration"), prompt[:80],
        )

        return await self._submit_and_poll(url, body)

    async def _execute_edit(self, prompt: str, source_video: str | None) -> str:
        """Edit an existing video."""
        if not source_video:
            return "Error: source_video is required for edit mode."

        video_url = self._load_video_as_url(source_video)
        if video_url.startswith("Error:"):
            return video_url

        url = f"{self.base_url}/videos/edits"
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "video": {"url": video_url},
        }

        logger.info("VideoGen (edit): model={} prompt={!r}", self.model, prompt[:80])
        return await self._submit_and_poll(url, body)

    async def _execute_extend(
        self, prompt: str, source_video: str | None, duration: int | None
    ) -> str:
        """Extend an existing video."""
        if not source_video:
            return "Error: source_video is required for extend mode."

        video_url = self._load_video_as_url(source_video)
        if video_url.startswith("Error:"):
            return video_url

        url = f"{self.base_url}/videos/extensions"
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "video": {"url": video_url},
        }

        if duration:
            body["duration"] = max(2, min(10, duration))
        else:
            body["duration"] = 6

        logger.info(
            "VideoGen (extend): model={} duration={}s prompt={!r}",
            self.model, body.get("duration"), prompt[:80],
        )
        return await self._submit_and_poll(url, body)

    async def _submit_and_poll(self, url: str, body: dict[str, Any]) -> str:
        """Submit a video generation request and poll until completion."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            async with httpx.AsyncClient(
                proxy=self.proxy, timeout=30.0, trust_env=True,
            ) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                request_id = data.get("request_id")
                if not request_id:
                    return f"Error: No request_id in API response: {str(data)[:300]}"

                logger.info("VideoGen: submitted request_id={}", request_id)

        except httpx.HTTPStatusError as e:
            return self._format_http_error(e)
        except httpx.TimeoutException:
            return "Error: Request submission timed out."
        except Exception as e:
            logger.error("VideoGen submit error: {}", e)
            return f"Error submitting video generation request: {e}"

        # Poll for completion
        return await self._poll_result(request_id, headers)

    async def _poll_result(self, request_id: str, headers: dict[str, str]) -> str:
        """Poll for video generation result."""
        poll_url = f"{self.base_url}/videos/{request_id}"
        start_time = time.monotonic()

        async with httpx.AsyncClient(
            proxy=self.proxy, timeout=30.0, trust_env=True,
        ) as client:
            while True:
                elapsed = time.monotonic() - start_time
                if elapsed > self._POLL_TIMEOUT:
                    return (
                        f"Error: Video generation timed out after {self._POLL_TIMEOUT}s. "
                        f"request_id={request_id}"
                    )

                await asyncio.sleep(self._POLL_INTERVAL)

                try:
                    resp = await client.get(poll_url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                except httpx.HTTPStatusError as e:
                    return self._format_http_error(e)
                except Exception as e:
                    logger.warning("VideoGen poll error (retrying): {}", e)
                    continue

                status = data.get("status", "")
                logger.debug("VideoGen poll: status={} elapsed={:.0f}s", status, elapsed)

                if status == "done":
                    video_info = data.get("video", {})
                    video_url = video_info.get("url")
                    if not video_url:
                        return "Error: Video completed but no URL returned."
                    return await self._download_video(video_url)

                elif status == "failed":
                    return "Error: Video generation failed on the server."

                elif status == "expired":
                    return "Error: Video generation request expired."

                # status == "pending" or unknown — keep polling

    async def _download_video(self, url: str) -> str:
        """Download video from URL and save to file."""
        try:
            async with httpx.AsyncClient(
                proxy=self.proxy, timeout=120.0, trust_env=True,
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                media_dir = get_media_dir("video_gen")
                fname = f"gen_{int(time.time())}_{uuid.uuid4().hex[:8]}.mp4"
                path = media_dir / fname
                path.write_bytes(resp.content)

                logger.info("VideoGen: downloaded and saved {} ({} bytes)", path, len(resp.content))
                return (
                    f"\u2713 Video generated successfully.\n"
                    f"File path: {path}\n\n"
                    f"Next step: Call the 'message' tool with media=['{path}'] "
                    f"to send this video to the user."
                )
        except Exception as e:
            return f"Error downloading video: {e}"

    def _load_image_as_data_uri(self, file_path: str) -> str:
        """Load an image file and return as data URI."""
        path = Path(file_path)
        if not path.exists():
            return f"Error: Image file not found: {file_path}"
        try:
            image_bytes = path.read_bytes()
            ext = path.suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif",
            }.get(ext, "image/jpeg")
            b64_str = base64.b64encode(image_bytes).decode()
            return f"data:{mime_type};base64,{b64_str}"
        except Exception as e:
            return f"Error reading image {file_path}: {e}"

    def _load_video_as_url(self, file_path: str) -> str:
        """Validate a video file path. For local files, returns the path as-is.

        The xAI API requires a URL, so local files need to be accessible via URL.
        If the path is already a URL (http/https), return as-is.
        For local files, encode as data URI.
        """
        if file_path.startswith(("http://", "https://")):
            return file_path

        path = Path(file_path)
        if not path.exists():
            return f"Error: Video file not found: {file_path}"
        if path.suffix.lower() != ".mp4":
            return f"Error: Video must be .mp4 format, got: {path.suffix}"

        try:
            video_bytes = path.read_bytes()
            b64_str = base64.b64encode(video_bytes).decode()
            return f"data:video/mp4;base64,{b64_str}"
        except Exception as e:
            return f"Error reading video {file_path}: {e}"

    def _format_http_error(self, e: httpx.HTTPStatusError) -> str:
        """Format HTTP error response."""
        try:
            error_detail = e.response.json()
            error_msg = error_detail.get("error", {}).get("message", e.response.text[:300])
        except Exception:
            error_msg = e.response.text[:300]
        return f"Error: API {e.response.status_code} - {error_msg}"
