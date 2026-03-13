"""Tests for the message merge (debounce) feature in BaseChannel."""

import asyncio
from types import SimpleNamespace

import pytest

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel


class _DummyChannel(BaseChannel):
    name = "dummy"

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def send(self, msg: OutboundMessage) -> None:
        return None


def _make_channel(merge_window: float = 0.0) -> tuple[_DummyChannel, MessageBus]:
    bus = MessageBus()
    ch = _DummyChannel(SimpleNamespace(allow_from=["*"]), bus)
    ch._merge_window_s = merge_window
    return ch, bus


@pytest.mark.asyncio
async def test_no_merge_when_disabled():
    """With merge_window_s=0, messages dispatch immediately."""
    ch, bus = _make_channel(0)

    await ch._handle_message("user1", "chat1", "hello")
    await ch._handle_message("user1", "chat1", "world")

    msg1 = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    msg2 = await asyncio.wait_for(bus.consume_inbound(), timeout=1)

    assert msg1.content == "hello"
    assert msg2.content == "world"


@pytest.mark.asyncio
async def test_merge_text_messages():
    """Messages within the merge window are combined into one."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "hello")
    await ch._handle_message("user1", "chat1", "world")

    # Should get one merged message after the window
    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.content == "hello\nworld"


@pytest.mark.asyncio
async def test_merge_photo_then_text():
    """Photo followed by text within window → single message with both."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "", media=["/tmp/photo.jpg"])
    await ch._handle_message("user1", "chat1", "Look at this!")

    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.content == "Look at this!"
    assert msg.media == ["/tmp/photo.jpg"]


@pytest.mark.asyncio
async def test_merge_multiple_photos_and_text():
    """Multiple photos + text within window → all merged."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "", media=["/tmp/a.jpg"])
    await ch._handle_message("user1", "chat1", "", media=["/tmp/b.jpg"])
    await ch._handle_message("user1", "chat1", "Two photos for you!")

    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.content == "Two photos for you!"
    assert msg.media == ["/tmp/a.jpg", "/tmp/b.jpg"]


@pytest.mark.asyncio
async def test_merge_deduplicates_media():
    """Duplicate media paths are deduplicated."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "hi", media=["/tmp/a.jpg"])
    await ch._handle_message("user1", "chat1", "again", media=["/tmp/a.jpg"])

    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.media == ["/tmp/a.jpg"]
    assert msg.content == "hi\nagain"


@pytest.mark.asyncio
async def test_different_senders_not_merged():
    """Messages from different senders are NOT merged."""
    ch, bus = _make_channel(0.5)

    await ch._handle_message("user1", "chat1", "from user1")
    await ch._handle_message("user2", "chat1", "from user2")

    # Both should flush independently
    msgs = []
    for _ in range(2):
        msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
        msgs.append(msg)

    contents = {m.content for m in msgs}
    assert contents == {"from user1", "from user2"}


@pytest.mark.asyncio
async def test_different_chats_not_merged():
    """Messages to different chats are NOT merged."""
    ch, bus = _make_channel(0.5)

    await ch._handle_message("user1", "chat1", "in chat1")
    await ch._handle_message("user1", "chat2", "in chat2")

    msgs = []
    for _ in range(2):
        msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
        msgs.append(msg)

    contents = {m.content for m in msgs}
    assert contents == {"in chat1", "in chat2"}


@pytest.mark.asyncio
async def test_merge_preserves_session_key():
    """Session key override is preserved through merge."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "hi", session_key="custom:key")
    await ch._handle_message("user1", "chat1", "there", session_key="custom:key")

    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.session_key_override == "custom:key"
    assert msg.content == "hi\nthere"


@pytest.mark.asyncio
async def test_merge_window_resets_on_new_message():
    """Each new message resets the merge timer (debounce behavior)."""
    ch, bus = _make_channel(0.3)

    await ch._handle_message("user1", "chat1", "first")
    await asyncio.sleep(0.15)  # 150ms - within window
    await ch._handle_message("user1", "chat1", "second")
    await asyncio.sleep(0.15)  # 150ms more - still within reset window
    await ch._handle_message("user1", "chat1", "third")

    # All three should merge (each resets the 300ms timer)
    msg = await asyncio.wait_for(bus.consume_inbound(), timeout=1)
    assert msg.content == "first\nsecond\nthird"
