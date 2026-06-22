from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.config_manage import ConfigManageTool, apply_config_manage_payload
from nanobot.agent.tools.context import RequestContext
from nanobot.config.loader import load_config, save_config, set_config_path
from nanobot.config.schema import Config


def test_apply_config_manage_payload_writes_allowed_key(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    set_config_path(config_path)
    save_config(Config(), config_path)

    result = apply_config_manage_payload(
        {
            "action": "set",
            "path": "tools.chinaLife.amapKey",
            "value": "amap-secret-key",
        }
    )

    assert result["success"] is True
    assert "amap-secret-key" not in result["message"]
    assert load_config(config_path).tools.china_life.amap_key == "amap-secret-key"


def test_apply_config_manage_payload_rejects_unknown_path(tmp_path: Path) -> None:
    set_config_path(tmp_path / "config.json")

    result = apply_config_manage_payload(
        {
            "action": "set",
            "path": "tools.exec.allowPatterns",
            "value": "anything",
        }
    )

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_config_manage_stages_update_by_default(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    set_config_path(config_path)
    save_config(Config(), config_path)

    tool = ConfigManageTool(tmp_path)
    tool.set_context(RequestContext(channel="cli", chat_id="direct", session_key="cli:direct"))
    result = json.loads(
        await tool.execute(
            action="set",
            path="tools.chinaLife.qweatherKey",
            value="qweather-secret-key",
        )
    )

    assert result["success"] is True
    assert result["pending_approval"] is True
    assert "qweather-secret-key" not in result["summary"]
    assert load_config(config_path).tools.china_life.qweather_key == ""

    records = ApprovalStore(tmp_path).list(session_key="cli:direct")
    assert len(records) == 1
    assert records[0]["kind"] == "config_manage"
    assert records[0]["payload"]["value"] == "qweather-secret-key"
