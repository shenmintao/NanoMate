"""Base channel interface for chat platforms."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class BaseChannel(ABC):
    """
    Abstract base class for chat channel implementations.

    Each channel (Telegram, Discord, etc.) should implement this interface
    to integrate with the nanobot message bus.
    """

    name: str = "base"
    display_name: str = "Base"
    transcription_api_key: str = ""

    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize the channel.

        Args:
            config: Channel-specific configuration.
            bus: The message bus for communication.
        """
        self.config = config
        self.bus = bus
        self._running = False
        # Message merge buffers: key → {content, media, metadata, ...}
        self._merge_buffers: dict[str, dict[str, Any]] = {}
        self._merge_timers: dict[str, asyncio.Task] = {}

    async def transcribe_audio(self, file_path: str | Path) -> str:
        """Transcribe an audio file via Groq Whisper. Returns empty string on failure."""
        if not self.transcription_api_key:
            return ""
        try:
            from nanobot.providers.transcription import GroqTranscriptionProvider

            provider = GroqTranscriptionProvider(api_key=self.transcription_api_key)
            return await provider.transcribe(file_path)
        except Exception as e:
            logger.warning("{}: audio transcription failed: {}", self.name, e)
            return ""

    @abstractmethod
    async def start(self) -> None:
        """
        Start the channel and begin listening for messages.

        This should be a long-running async task that:
        1. Connects to the chat platform
        2. Listens for incoming messages
        3. Forwards messages to the bus via _handle_message()
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources."""
        pass

    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through this channel.

        Args:
            msg: The message to send.
        """
        pass

    def is_allowed(self, sender_id: str) -> bool:
        """Check if *sender_id* is permitted.  Empty list → deny all; ``"*"`` → allow all."""
        allow_list = getattr(self.config, "allow_from", [])
        if not allow_list:
            logger.warning("{}: allow_from is empty — all access denied", self.name)
            return False
        if "*" in allow_list:
            return True
        return str(sender_id) in allow_list

    def _get_merge_window(self) -> float:
        """Get merge window from channels config. Returns 0 if disabled."""
        try:
            # Access the parent channels config via bus (set by ChannelManager)
            merge_s = getattr(self, "_merge_window_s", 0.0)
            return float(merge_s) if merge_s else 0.0
        except Exception:
            return 0.0

    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        session_key: str | None = None,
    ) -> None:
        """
        Handle an incoming message from the chat platform.

        This method checks permissions and forwards to the bus.
        If merge_window_s > 0, messages from the same sender in the same chat
        are buffered and merged before dispatch.

        Args:
            sender_id: The sender's identifier.
            chat_id: The chat/channel identifier.
            content: Message text content.
            media: Optional list of media URLs.
            metadata: Optional channel-specific metadata.
            session_key: Optional session key override (e.g. thread-scoped sessions).
        """
        if not self.is_allowed(sender_id):
            logger.warning(
                "Access denied for sender {} on channel {}. "
                "Add them to allowFrom list in config to grant access.",
                sender_id, self.name,
            )
            return

        merge_window = self._get_merge_window()

        if merge_window <= 0:
            # No merging — dispatch immediately (original behavior)
            msg = InboundMessage(
                channel=self.name,
                sender_id=str(sender_id),
                chat_id=str(chat_id),
                content=content,
                media=media or [],
                metadata=metadata or {},
                session_key_override=session_key,
            )
            await self.bus.publish_inbound(msg)
            return

        # --- Merge mode ---
        merge_key = f"{self.name}:{chat_id}:{sender_id}"

        if merge_key in self._merge_buffers:
            # Append to existing buffer
            buf = self._merge_buffers[merge_key]
            if content and content.strip():
                buf["contents"].append(content)
            if media:
                buf["media"].extend(media)
            # Keep latest metadata (merge dicts)
            if metadata:
                buf["metadata"].update(metadata)
            logger.debug(
                "{}: merged message into buffer for {} (now {} parts, {} media)",
                self.name, merge_key, len(buf["contents"]), len(buf["media"]),
            )
        else:
            # Create new buffer
            self._merge_buffers[merge_key] = {
                "sender_id": str(sender_id),
                "chat_id": str(chat_id),
                "contents": [content] if content and content.strip() else [],
                "media": list(media or []),
                "metadata": dict(metadata or {}),
                "session_key": session_key,
            }
            logger.debug("{}: new merge buffer for {}", self.name, merge_key)

        # Cancel existing timer and start a new one (debounce reset)
        if merge_key in self._merge_timers:
            self._merge_timers[merge_key].cancel()

        self._merge_timers[merge_key] = asyncio.create_task(
            self._flush_merge_buffer(merge_key, merge_window)
        )

    async def _flush_merge_buffer(self, merge_key: str, delay: float) -> None:
        """Wait for the merge window, then flush the buffered messages as one."""
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        buf = self._merge_buffers.pop(merge_key, None)
        self._merge_timers.pop(merge_key, None)

        if not buf:
            return

        # Merge all content parts with newlines, deduplicate media
        merged_content = "\n".join(buf["contents"]) if buf["contents"] else ""
        merged_media = list(dict.fromkeys(buf["media"]))  # preserve order, deduplicate

        parts_count = len(buf["contents"])
        media_count = len(merged_media)
        if parts_count > 1 or media_count > 0:
            logger.info(
                "{}: flushing merged message for {} ({} text parts, {} media)",
                self.name, merge_key, parts_count, media_count,
            )

        msg = InboundMessage(
            channel=self.name,
            sender_id=buf["sender_id"],
            chat_id=buf["chat_id"],
            content=merged_content,
            media=merged_media,
            metadata=buf["metadata"],
            session_key_override=buf["session_key"],
        )

        await self.bus.publish_inbound(msg)

    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
