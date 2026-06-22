from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.context import RequestContext
from nanobot.agent.tools.skill_manage import SkillManageTool, apply_skill_manage_payload


def _skill_content(name: str = "daily-helper") -> str:
    return f"""---
name: {name}
description: Help with recurring personal assistant tasks.
---

Use this workflow when the matching recurring task appears.
"""


@pytest.mark.asyncio
async def test_skill_manage_stages_create_by_default(tmp_path: Path) -> None:
    tool = SkillManageTool(tmp_path)
    tool.set_context(
        RequestContext(channel="cli", chat_id="direct", session_key="cli:direct")
    )

    result = json.loads(
        await tool.execute(
            action="create",
            name="daily-helper",
            content=_skill_content(),
        )
    )

    assert result["success"] is True
    assert result["pending_approval"] is True
    assert not (tmp_path / "skills" / "daily-helper" / "SKILL.md").exists()

    records = ApprovalStore(tmp_path).list(session_key="cli:direct")
    assert len(records) == 1
    assert records[0]["kind"] == "skill_manage"
    assert records[0]["payload"]["action"] == "create"
    assert records[0]["payload"]["name"] == "daily-helper"


def test_apply_skill_manage_payload_creates_valid_skill(tmp_path: Path) -> None:
    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-helper",
            "content": _skill_content(),
        },
    )

    assert result["success"] is True
    assert (tmp_path / "skills" / "daily-helper" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == _skill_content()
    meta = json.loads(
        (tmp_path / "skills" / "daily-helper" / ".nanomate-skill.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["created_by"] == "agent"
    assert meta["pinned"] is False


def test_apply_skill_manage_payload_rejects_similar_skill(tmp_path: Path) -> None:
    first = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-helper",
            "content": _skill_content(),
        },
    )
    assert first["success"] is True

    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-assistant",
            "content": _skill_content("daily-assistant"),
        },
    )

    assert result["success"] is False
    assert "similar skill" in result["error"]
    assert result["similar_skills"][0]["name"] == "daily-helper"
    assert not (tmp_path / "skills" / "daily-assistant").exists()


@pytest.mark.asyncio
async def test_skill_manage_import_url_stages_downloaded_skill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_urls: list[str] = []

    async def fake_fetch(url: str) -> str:
        seen_urls.append(url)
        return _skill_content("remote-helper")

    monkeypatch.setattr("nanobot.agent.tools.skill_manage._fetch_text_from_url", fake_fetch)
    tool = SkillManageTool(tmp_path)
    tool.set_context(
        RequestContext(channel="cli", chat_id="direct", session_key="cli:direct")
    )

    result = json.loads(
        await tool.execute(
            action="import_url",
            name="remote-helper",
            source_url="https://github.com/acme/skills/blob/main/skills/remote-helper/SKILL.md",
        )
    )

    assert result["success"] is True
    assert result["pending_approval"] is True
    assert seen_urls == [
        "https://raw.githubusercontent.com/acme/skills/main/skills/remote-helper/SKILL.md"
    ]
    assert not (tmp_path / "skills" / "remote-helper" / "SKILL.md").exists()

    records = ApprovalStore(tmp_path).list(session_key="cli:direct")
    assert len(records) == 1
    assert records[0]["payload"]["action"] == "import_url"
    assert records[0]["payload"]["content"] == _skill_content("remote-helper")
    assert records[0]["payload"]["source_url"] == seen_urls[0]


def test_apply_skill_manage_import_url_payload_uses_content_snapshot(tmp_path: Path) -> None:
    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "import_url",
            "name": "remote-helper",
            "source_url": "https://raw.githubusercontent.com/acme/skills/main/skills/remote-helper/SKILL.md",
            "content": _skill_content("remote-helper"),
        },
    )

    assert result["success"] is True
    assert (tmp_path / "skills" / "remote-helper" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == _skill_content("remote-helper")
    meta = json.loads(
        (tmp_path / "skills" / "remote-helper" / ".nanomate-skill.json").read_text(
            encoding="utf-8"
        )
    )
    assert meta["created_by"] == "agent"
    assert meta["source_url"] == (
        "https://raw.githubusercontent.com/acme/skills/main/skills/remote-helper/SKILL.md"
    )


@pytest.mark.asyncio
async def test_skill_manage_import_url_rejects_untrusted_url_without_fetch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_fetch(url: str) -> str:
        raise AssertionError(f"unexpected fetch: {url}")

    monkeypatch.setattr("nanobot.agent.tools.skill_manage._fetch_text_from_url", fail_fetch)
    tool = SkillManageTool(tmp_path)

    result = json.loads(
        await tool.execute(
            action="import_url",
            name="remote-helper",
            source_url="https://example.com/SKILL.md",
        )
    )

    assert result["success"] is False
    assert "raw GitHub" in result["error"]


def test_write_file_rejects_path_traversal(tmp_path: Path) -> None:
    apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-helper",
            "content": _skill_content(),
        },
    )

    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "write_file",
            "name": "daily-helper",
            "file_path": "../escape.txt",
            "file_content": "bad",
        },
    )

    assert result["success"] is False
    assert "cannot contain '..'" in result["error"]
    assert not (tmp_path / "skills" / "escape.txt").exists()


def test_patch_requires_exact_match(tmp_path: Path) -> None:
    apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-helper",
            "content": _skill_content(),
        },
    )

    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "patch",
            "name": "daily-helper",
            "old_string": "missing exact text",
            "new_string": "replacement",
        },
    )

    assert result["success"] is False
    assert result["error"] == "old_string was not found."


def test_patch_rejects_invalid_resulting_skill_file(tmp_path: Path) -> None:
    apply_skill_manage_payload(
        tmp_path,
        {
            "action": "create",
            "name": "daily-helper",
            "content": _skill_content(),
        },
    )
    target = tmp_path / "skills" / "daily-helper" / "SKILL.md"
    before = target.read_text(encoding="utf-8")

    result = apply_skill_manage_payload(
        tmp_path,
        {
            "action": "patch",
            "name": "daily-helper",
            "old_string": "Use this workflow when the matching recurring task appears.",
            "new_string": "",
        },
    )

    assert result["success"] is False
    assert "patched SKILL.md would be invalid" in result["error"]
    assert target.read_text(encoding="utf-8") == before
