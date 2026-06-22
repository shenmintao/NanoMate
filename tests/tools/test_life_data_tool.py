from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.agent.tools.life_data import LifeDataTool


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_life_data_adds_task_and_audit_entry(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path, timezone="Asia/Shanghai")

    result = json.loads(
        await tool.execute(
            action="add",
            collection="tasks",
            record={"title": "Buy milk", "status": "open", "priority": "normal"},
            auditNote="captured grocery task",
        )
    )

    assert result["success"] is True
    task = result["record"]
    assert task["id"].startswith("task-")
    assert task["created_at"]
    assert task["updated_at"]

    stored = _load(tmp_path / "life" / "tasks.json")
    assert stored == [task]
    audit = (tmp_path / "life" / "audit.md").read_text(encoding="utf-8")
    assert "changed life/tasks.json: captured grocery task" in audit


@pytest.mark.asyncio
async def test_life_data_updates_record_with_deep_merge(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path)
    created = json.loads(
        await tool.execute(
            action="add",
            collection="tasks",
            record={"id": "task-1", "title": "Call bank", "metadata": {"source": "chat"}},
        )
    )

    result = json.loads(
        await tool.execute(
            action="update",
            collection="tasks",
            id="task-1",
            record={"status": "done", "metadata": {"channel": "cli"}},
        )
    )

    assert result["success"] is True
    assert result["record"]["id"] == "task-1"
    assert result["record"]["status"] == "done"
    assert result["record"]["metadata"] == {"source": "chat", "channel": "cli"}
    assert result["record"]["created_at"] == created["record"]["created_at"]


@pytest.mark.asyncio
async def test_life_data_archive_is_soft_and_hidden_by_default(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path)
    await tool.execute(action="add", collection="tasks", record={"id": "task-1", "title": "Old"})

    archived = json.loads(await tool.execute(action="archive", collection="tasks", id="task-1"))
    listed = json.loads(await tool.execute(action="list", collection="tasks"))
    listed_with_archived = json.loads(
        await tool.execute(action="list", collection="tasks", includeArchived=True)
    )

    assert archived["success"] is True
    assert archived["record"]["archived_at"]
    assert listed["records"] == []
    assert listed_with_archived["records"][0]["id"] == "task-1"


@pytest.mark.asyncio
async def test_life_data_merges_preferences_object(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path)

    first = json.loads(
        await tool.execute(
            action="merge",
            collection="preferences",
            record={"food": {"coffee": {"value": "latte", "confidence": "confirmed"}}},
        )
    )
    second = json.loads(
        await tool.execute(
            action="merge",
            collection="preferences",
            record={"food": {"spice": {"value": "mild", "confidence": "confirmed"}}},
        )
    )

    assert first["success"] is True
    assert second["record"]["food"]["coffee"]["value"] == "latte"
    assert second["record"]["food"]["spice"]["value"] == "mild"


@pytest.mark.asyncio
async def test_life_data_appends_journal_and_audit(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path)

    result = json.loads(
        await tool.execute(
            action="append",
            collection="journal",
            text="## 2026-06-22\n\n- 21:00 - felt focused after planning.",
            auditNote="recorded evening reflection",
        )
    )

    assert result["success"] is True
    assert "felt focused" in (tmp_path / "life" / "journal.md").read_text(encoding="utf-8")
    audit = (tmp_path / "life" / "audit.md").read_text(encoding="utf-8")
    assert "changed life/journal.md: recorded evening reflection" in audit


@pytest.mark.asyncio
async def test_life_data_rejects_unknown_collection(tmp_path: Path) -> None:
    tool = LifeDataTool(tmp_path)

    result = json.loads(await tool.execute(action="list", collection="escape"))

    assert result["success"] is False
    assert "Unsupported life data collection" in result["error"]
    assert not (tmp_path / "life" / "escape.json").exists()
