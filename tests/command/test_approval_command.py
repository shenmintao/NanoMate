from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from nanobot.agent.approvals import ApprovalStore
from nanobot.bus.events import InboundMessage
from nanobot.command.builtin import cmd_approval, maybe_handle_approval_reply
from nanobot.command.router import CommandContext
from nanobot.config.loader import load_config, save_config, set_config_path
from nanobot.config.schema import Config


def _skill_content(name: str) -> str:
    return f"""---
name: {name}
description: Help with recurring personal assistant tasks.
---

Use this workflow when the matching recurring task appears.
"""


def _payload(name: str) -> dict[str, str]:
    return {
        "action": "create",
        "name": name,
        "content": _skill_content(name),
    }


def _create_pending(tmp_path: Path, name: str, *, session_key: str = "cli:direct") -> dict:
    return ApprovalStore(tmp_path).create(
        kind="skill_manage",
        summary=f"Create workspace skill `{name}`.",
        payload=_payload(name),
        session_key=session_key,
        channel="cli",
        chat_id="direct",
    )


def _create_config_pending(tmp_path: Path, *, session_key: str = "cli:direct") -> dict:
    return ApprovalStore(tmp_path).create(
        kind="config_manage",
        summary="Set config `tools.chinaLife.amapKey` to `am******-key`.",
        payload={
            "action": "set",
            "path": "tools.chinaLife.amapKey",
            "value": "amap-secret-key",
        },
        session_key=session_key,
        channel="cli",
        chat_id="direct",
    )


def _create_life_action_pending(tmp_path: Path, *, session_key: str = "cli:direct") -> dict:
    from nanobot.agent.tools.life_action import create_life_action_proposal

    created = create_life_action_proposal(
        tmp_path,
        {
            "title": "Book train",
            "summary": "Book G123 from Beijing to Shanghai.",
            "risk": "high",
            "actionType": "booking",
            "externalSystem": "12306",
            "payloadSummary": "train=G123, route=Beijing-Shanghai",
        },
        session_key=session_key,
        channel="cli",
        chat_id="direct",
    )
    assert created["success"] is True
    return ApprovalStore(tmp_path).list(session_key=session_key)[0]


def _create_skill_curator_pending(tmp_path: Path, *, session_key: str = "cli:direct") -> dict:
    skill_dir = tmp_path / "skills" / "old-helper"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(_skill_content("old-helper"), encoding="utf-8")
    (skill_dir / ".nanomate-skill.json").write_text(
        """{
  "schema_version": 1,
  "created_by": "agent",
  "created_at": 1,
  "updated_at": 1,
  "pinned": false
}
""",
        encoding="utf-8",
    )
    return ApprovalStore(tmp_path).create(
        kind="skill_curator",
        summary="Archive agent-created skill `old-helper`.",
        payload={"action": "archive", "name": "old-helper", "reason": "duplicate"},
        session_key=session_key,
        channel="cli",
        chat_id="direct",
    )


def _pending_life_action(tmp_path: Path) -> dict:
    import json

    return json.loads((tmp_path / "life" / "pending-actions.json").read_text(encoding="utf-8"))[0]


def _ctx(tmp_path: Path, raw: str, *, session_key: str = "cli:direct") -> CommandContext:
    msg = InboundMessage(
        channel="cli",
        sender_id="user",
        chat_id="direct",
        content=raw,
        session_key_override=session_key,
    )
    args = ""
    if raw.startswith("/approval "):
        args = raw[len("/approval "):]
    elif raw.startswith("/approve "):
        args = raw[len("/approve "):]
    elif raw.startswith("/reject "):
        args = raw[len("/reject "):]
    return CommandContext(
        msg=msg,
        session=None,
        key=msg.session_key,
        raw=raw,
        args=args,
        loop=SimpleNamespace(workspace=tmp_path),
    )


@pytest.mark.asyncio
async def test_approval_command_lists_pending(tmp_path: Path) -> None:
    record = _create_pending(tmp_path, "daily-helper")

    out = await cmd_approval(_ctx(tmp_path, "/approval"))

    assert "Pending approvals (1):" in out.content
    assert record["id"] in out.content
    assert "daily-helper" in out.content


@pytest.mark.asyncio
async def test_approval_command_approve_applies_and_removes_record(tmp_path: Path) -> None:
    record = _create_pending(tmp_path, "daily-helper")

    out = await cmd_approval(_ctx(tmp_path, f"/approval approve {record['id']}"))

    assert f"Approved `{record['id']}`" in out.content
    assert (tmp_path / "skills" / "daily-helper" / "SKILL.md").exists()
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_approval_command_applies_config_manage_record(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    set_config_path(config_path)
    save_config(Config(), config_path)
    record = _create_config_pending(tmp_path)

    out = await cmd_approval(_ctx(tmp_path, f"/approval approve {record['id']}"))

    assert f"Approved `{record['id']}`" in out.content
    assert load_config(config_path).tools.china_life.amap_key == "amap-secret-key"
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_approval_command_approves_life_action_record(tmp_path: Path) -> None:
    record = _create_life_action_pending(tmp_path)

    out = await cmd_approval(_ctx(tmp_path, f"/approval approve {record['id']}"))

    assert f"Approved `{record['id']}`" in out.content
    action = _pending_life_action(tmp_path)
    assert action["status"] == "approved"
    assert "approve" in action["approval_text"]
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_approval_command_rejects_life_action_record(tmp_path: Path) -> None:
    record = _create_life_action_pending(tmp_path)

    out = await cmd_approval(_ctx(tmp_path, f"/approval reject {record['id']}"))

    assert f"Rejected `{record['id']}`" in out.content
    action = _pending_life_action(tmp_path)
    assert action["status"] == "rejected"
    assert "reject" in action["rejection_text"]
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_approval_command_applies_skill_curator_record(tmp_path: Path) -> None:
    record = _create_skill_curator_pending(tmp_path)

    out = await cmd_approval(_ctx(tmp_path, f"/approval approve {record['id']}"))

    assert f"Approved `{record['id']}`" in out.content
    assert not (tmp_path / "skills" / "old-helper").exists()
    assert list((tmp_path / "skills" / ".archive").iterdir())
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_plain_approve_applies_single_pending_approval(tmp_path: Path) -> None:
    record = _create_pending(tmp_path, "daily-helper")

    out = await maybe_handle_approval_reply(_ctx(tmp_path, "批准"))

    assert out is not None
    assert f"Approved `{record['id']}`" in out.content
    assert (tmp_path / "skills" / "daily-helper" / "SKILL.md").exists()
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []


@pytest.mark.asyncio
async def test_plain_approve_lists_multiple_pending_instead_of_applying(tmp_path: Path) -> None:
    first = _create_pending(tmp_path, "daily-helper")
    second = _create_pending(tmp_path, "finance-helper")

    out = await maybe_handle_approval_reply(_ctx(tmp_path, "批准"))

    assert out is not None
    assert "Pending approvals (2):" in out.content
    assert first["id"] in out.content
    assert second["id"] in out.content
    assert not (tmp_path / "skills" / "daily-helper").exists()
    assert not (tmp_path / "skills" / "finance-helper").exists()


@pytest.mark.asyncio
async def test_plain_reject_removes_single_pending_approval(tmp_path: Path) -> None:
    record = _create_pending(tmp_path, "daily-helper")

    out = await maybe_handle_approval_reply(_ctx(tmp_path, "reject"))

    assert out is not None
    assert f"Rejected `{record['id']}`" in out.content
    assert ApprovalStore(tmp_path).list(session_key="cli:direct") == []
    assert not (tmp_path / "skills" / "daily-helper").exists()
