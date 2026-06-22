from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.context import RequestContext
from nanobot.agent.tools.life_action import LifeActionTool, apply_life_action_approval


def _load_pending_actions(tmp_path: Path) -> list[dict]:
    return json.loads((tmp_path / "life" / "pending-actions.json").read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_life_action_propose_records_action_and_stages_approval(tmp_path: Path) -> None:
    tool = LifeActionTool(tmp_path)
    tool.set_context(RequestContext(channel="cli", chat_id="direct", session_key="cli:direct"))

    result = json.loads(
        await tool.execute(
            action="propose",
            title="Book train to Shanghai",
            summary="Book G123 from Beijing to Shanghai tomorrow morning.",
            risk="high",
            actionType="booking",
            externalSystem="12306",
            payloadSummary="train=G123, route=Beijing-Shanghai, passenger=user",
        )
    )

    assert result["success"] is True
    assert result["pending_approval"] is True
    assert result["requires_second_confirmation"] is True
    pending_actions = _load_pending_actions(tmp_path)
    assert pending_actions[0]["id"] == result["pending_action_id"]
    assert pending_actions[0]["status"] == "proposed"
    assert pending_actions[0]["requires_second_confirmation"] is True

    approvals = ApprovalStore(tmp_path).list(session_key="cli:direct")
    assert len(approvals) == 1
    assert approvals[0]["kind"] == "life_action"
    assert approvals[0]["payload"]["pending_action_id"] == result["pending_action_id"]


def test_apply_life_action_approval_marks_pending_action_approved(tmp_path: Path) -> None:
    from nanobot.agent.tools.life_action import create_life_action_proposal

    result = create_life_action_proposal(
        tmp_path,
        {
            "title": "Pay utility bill",
            "summary": "Pay 100 CNY utility bill.",
            "risk": "critical",
            "actionType": "payment",
            "externalSystem": "Alipay",
            "payloadSummary": "amount=100 CNY, account=utility bill",
        },
        session_key="cli:direct",
        channel="cli",
        chat_id="direct",
    )

    applied = apply_life_action_approval(
        tmp_path,
        {"pending_action_id": result["pending_action_id"]},
        decision="approve",
        approval_text="approve",
    )

    assert applied["success"] is True
    action = _load_pending_actions(tmp_path)[0]
    assert action["status"] == "approved"
    assert action["approval_text"] == "approve"
    assert "second confirmation" in action["result"]


def test_apply_life_action_approval_marks_pending_action_rejected(tmp_path: Path) -> None:
    from nanobot.agent.tools.life_action import create_life_action_proposal

    created = create_life_action_proposal(
        tmp_path,
        {
            "title": "Send message",
            "summary": "Send the drafted message to Alice.",
            "risk": "high",
            "actionType": "message",
            "externalSystem": "WeChat",
            "payloadSummary": "recipient=Alice",
        },
        session_key="cli:direct",
        channel="cli",
        chat_id="direct",
    )

    applied = apply_life_action_approval(
        tmp_path,
        {"pending_action_id": created["pending_action_id"]},
        decision="reject",
        approval_text="reject",
    )

    assert applied["success"] is True
    action = _load_pending_actions(tmp_path)[0]
    assert action["status"] == "rejected"
    assert action["rejection_text"] == "reject"
