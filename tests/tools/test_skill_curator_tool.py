from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.context import RequestContext
from nanobot.agent.tools.skill_curator import (
    SkillCuratorTool,
    apply_skill_curator_payload,
    audit_skills,
)


def _skill_content(name: str, description: str) -> str:
    return f"""---
name: {name}
description: {description}
---

Use this workflow when the matching recurring task appears.
"""


def _write_skill(
    workspace: Path,
    name: str,
    description: str,
    *,
    agent_created: bool,
    updated_at: float | None = None,
    pinned: bool = False,
) -> None:
    skill_dir = workspace / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        _skill_content(name, description),
        encoding="utf-8",
    )
    if agent_created:
        ts = updated_at if updated_at is not None else time.time()
        (skill_dir / ".nanomate-skill.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "created_by": "agent",
                    "created_at": ts,
                    "updated_at": ts,
                    "pinned": pinned,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def test_audit_reports_agent_created_duplicates_and_stale_skills(tmp_path: Path) -> None:
    old_ts = time.time() - 120 * 86400
    _write_skill(
        tmp_path,
        "meal-plan",
        "Plan weekly meals and grocery lists.",
        agent_created=True,
        updated_at=old_ts,
    )
    _write_skill(
        tmp_path,
        "meal-planner",
        "Plan weekly meals and grocery lists.",
        agent_created=True,
    )
    _write_skill(
        tmp_path,
        "manual-meals",
        "Plan weekly meals and grocery lists.",
        agent_created=False,
    )

    result = audit_skills(tmp_path, stale_days=30, similarity_threshold=0.2)

    assert result["success"] is True
    assert result["managed_count"] == 2
    assert result["unmanaged_count"] == 1
    assert {item["name"] for item in result["stale_candidates"]} == {"meal-plan"}
    duplicate_names = {item["name"] for item in result["duplicate_candidates"]}
    assert {"meal-plan", "meal-planner"} <= duplicate_names


def test_archive_refuses_unmanaged_skill(tmp_path: Path) -> None:
    _write_skill(tmp_path, "manual-meals", "Manual workflow.", agent_created=False)

    result = apply_skill_curator_payload(
        tmp_path,
        {"action": "archive", "name": "manual-meals", "reason": "duplicate"},
    )

    assert result["success"] is False
    assert "not marked as agent-created" in result["error"]
    assert (tmp_path / "skills" / "manual-meals" / "SKILL.md").exists()


def test_archive_moves_agent_created_skill_to_archive(tmp_path: Path) -> None:
    _write_skill(tmp_path, "old-helper", "Old generated workflow.", agent_created=True)

    result = apply_skill_curator_payload(
        tmp_path,
        {"action": "archive", "name": "old-helper", "reason": "stale"},
    )

    assert result["success"] is True
    assert not (tmp_path / "skills" / "old-helper").exists()
    archived = Path(result["path"])
    assert archived.parent == tmp_path / "skills" / ".archive"
    assert (archived / "SKILL.md").exists()
    meta = json.loads((archived / ".nanomate-skill.json").read_text(encoding="utf-8"))
    assert meta["archive_reason"] == "stale"
    assert meta["original_name"] == "old-helper"


def test_pin_prevents_archive_until_unpinned(tmp_path: Path) -> None:
    _write_skill(tmp_path, "keeper", "Important generated workflow.", agent_created=True)

    pinned = apply_skill_curator_payload(tmp_path, {"action": "pin", "name": "keeper"})
    assert pinned["success"] is True

    blocked = apply_skill_curator_payload(tmp_path, {"action": "archive", "name": "keeper"})
    assert blocked["success"] is False
    assert "pinned" in blocked["error"]

    unpinned = apply_skill_curator_payload(tmp_path, {"action": "unpin", "name": "keeper"})
    assert unpinned["success"] is True

    archived = apply_skill_curator_payload(tmp_path, {"action": "archive", "name": "keeper"})
    assert archived["success"] is True


@pytest.mark.asyncio
async def test_skill_curator_stages_archive_by_default(tmp_path: Path) -> None:
    _write_skill(tmp_path, "old-helper", "Old generated workflow.", agent_created=True)
    tool = SkillCuratorTool(tmp_path)
    tool.set_context(RequestContext(channel="cli", chat_id="direct", session_key="cli:direct"))

    result = json.loads(
        await tool.execute(action="archive", name="old-helper", reason="duplicate")
    )

    assert result["success"] is True
    assert result["pending_approval"] is True
    assert (tmp_path / "skills" / "old-helper" / "SKILL.md").exists()
    records = ApprovalStore(tmp_path).list(session_key="cli:direct")
    assert len(records) == 1
    assert records[0]["kind"] == "skill_curator"
    assert records[0]["payload"]["action"] == "archive"
