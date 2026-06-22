"""Approval-gated high-risk life action proposals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.context import ContextAware, RequestContext
from nanobot.agent.tools.life_data import apply_life_data_payload
from nanobot.agent.tools.schema import BooleanSchema, StringSchema, tool_parameters_schema
from nanobot.config_base import Base


class LifeActionToolConfig(Base):
    """Configuration for life action approval staging."""

    enable: bool = True
    require_approval: bool = True


_SECOND_CONFIRMATION_ACTION_TYPES = {
    "payment",
    "purchase",
    "message",
    "booking",
    "account-change",
    "smart-home",
    "health",
    "delete-data",
}


def _tool_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _requires_second_confirmation(risk: str, action_type: str, explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    return risk == "critical" or action_type in _SECOND_CONFIRMATION_ACTION_TYPES


def _summary_for(action: dict[str, Any]) -> str:
    action_id = str(action.get("id") or "")
    title = str(action.get("title") or action.get("summary") or "life action").strip()
    risk = str(action.get("risk") or "high").strip()
    external_system = str(action.get("external_system") or "external system").strip()
    return f"Approve life action `{action_id}`: {title} ({risk}, {external_system})."


def _load_pending_action(workspace: str | Path, action_id: str) -> dict[str, Any] | None:
    result = apply_life_data_payload(
        workspace,
        {
            "action": "get",
            "collection": "pending_actions",
            "id": action_id,
        },
    )
    if result.get("success") and isinstance(result.get("record"), dict):
        return result["record"]
    return None


def _stage_approval(
    workspace: str | Path,
    action: dict[str, Any],
    *,
    session_key: str | None,
    channel: str | None,
    chat_id: str | None,
) -> dict[str, Any]:
    record = ApprovalStore(workspace).create(
        kind="life_action",
        summary=_summary_for(action),
        payload={
            "action": "approve",
            "pending_action_id": action.get("id"),
        },
        session_key=session_key,
        channel=channel,
        chat_id=chat_id,
    )
    return {
        "success": True,
        "pending_approval": True,
        "approval_id": record["id"],
        "pending_action_id": action.get("id"),
        "summary": record["summary"],
        "requires_second_confirmation": bool(action.get("requires_second_confirmation")),
        "message": (
            f"Staged life action approval as `{record['id']}`. "
            "The user can reply `批准` / `approve`, `拒绝` / `reject`, "
            "or run `/approval` to review pending items."
        ),
    }


def create_life_action_proposal(
    workspace: str | Path,
    payload: dict[str, Any],
    *,
    session_key: str | None,
    channel: str | None,
    chat_id: str | None,
) -> dict[str, Any]:
    title = str(payload.get("title") or "").strip()
    summary = str(payload.get("summary") or "").strip()
    if not title:
        return {"success": False, "error": "title is required."}
    if not summary:
        return {"success": False, "error": "summary is required."}
    risk = str(payload.get("risk") or "high").strip()
    if risk not in {"medium", "high", "critical"}:
        return {"success": False, "error": "risk must be medium, high, or critical."}
    action_type = str(payload.get("action_type") or payload.get("actionType") or "other").strip()
    external_system = str(payload.get("external_system") or payload.get("externalSystem") or "unknown").strip()
    requires_second = _requires_second_confirmation(
        risk,
        action_type,
        payload.get("requires_second_confirmation", payload.get("requiresSecondConfirmation")),
    )
    action_record = {
        "title": title,
        "status": "proposed",
        "risk": risk,
        "action_type": action_type,
        "external_system": external_system,
        "summary": summary,
        "payload_summary": payload.get("payload_summary", payload.get("payloadSummary", "")),
        "money": payload.get("money"),
        "recipient": payload.get("recipient"),
        "scheduled_for": payload.get("scheduled_for", payload.get("scheduledFor")),
        "requires_second_confirmation": requires_second,
        "source": "life_action",
    }
    action_record = {key: value for key, value in action_record.items() if value not in (None, "")}
    created = apply_life_data_payload(
        workspace,
        {
            "action": "add",
            "collection": "pending_actions",
            "record": action_record,
            "audit_note": f"proposed life action: {title}",
        },
    )
    if not created.get("success"):
        return created
    staged = _stage_approval(
        workspace,
        created["record"],
        session_key=session_key,
        channel=channel,
        chat_id=chat_id,
    )
    staged["record"] = created["record"]
    return staged


def stage_existing_life_action(
    workspace: str | Path,
    pending_action_id: str,
    *,
    session_key: str | None,
    channel: str | None,
    chat_id: str | None,
) -> dict[str, Any]:
    if not pending_action_id:
        return {"success": False, "error": "pending_action_id is required."}
    action = _load_pending_action(workspace, pending_action_id)
    if action is None:
        return {"success": False, "error": f"Pending life action not found: {pending_action_id}"}
    if str(action.get("status") or "") not in {"proposed", "pending"}:
        return {
            "success": False,
            "error": f"Pending life action {pending_action_id} is not proposed/pending.",
            "status": action.get("status"),
        }
    return _stage_approval(
        workspace,
        action,
        session_key=session_key,
        channel=channel,
        chat_id=chat_id,
    )


def apply_life_action_approval(
    workspace: str | Path,
    payload: dict[str, Any],
    *,
    decision: str,
    approval_text: str,
) -> dict[str, Any]:
    pending_action_id = str(payload.get("pending_action_id") or payload.get("pendingActionId") or "").strip()
    if not pending_action_id:
        return {"success": False, "error": "pending_action_id is required."}
    action = _load_pending_action(workspace, pending_action_id)
    if action is None:
        return {"success": False, "error": f"Pending life action not found: {pending_action_id}"}
    if decision == "approve":
        update = {
            "status": "approved",
            "approval_text": approval_text,
        }
        if action.get("requires_second_confirmation"):
            update["result"] = "Approved; second confirmation is required before execution."
        result = apply_life_data_payload(
            workspace,
            {
                "action": "update",
                "collection": "pending_actions",
                "id": pending_action_id,
                "record": update,
                "audit_note": f"approved life action {pending_action_id}",
            },
        )
        if result.get("success"):
            message = f"Life action `{pending_action_id}` approved."
            if action.get("requires_second_confirmation"):
                message += " Second confirmation is still required before execution."
            result["message"] = message
        return result
    if decision == "reject":
        result = apply_life_data_payload(
            workspace,
            {
                "action": "update",
                "collection": "pending_actions",
                "id": pending_action_id,
                "record": {
                    "status": "rejected",
                    "rejection_text": approval_text,
                },
                "audit_note": f"rejected life action {pending_action_id}",
            },
        )
        if result.get("success"):
            result["message"] = f"Life action `{pending_action_id}` rejected."
        return result
    return {"success": False, "error": f"Unsupported life action decision: {decision}"}


class LifeActionTool(Tool, ContextAware):
    """Stage high-risk life actions for conversation approval."""

    config_key = "life_action"

    @classmethod
    def config_cls(cls):
        return LifeActionToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        return bool(getattr(ctx.config.life_action, "enable", True))

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(
            workspace=Path(ctx.workspace),
            require_approval=ctx.config.life_action.require_approval,
        )

    def __init__(self, workspace: Path | str, *, require_approval: bool = True) -> None:
        self.workspace = Path(workspace)
        self.require_approval = require_approval
        self._request_context: RequestContext | None = None

    def set_context(self, ctx: RequestContext) -> None:
        self._request_context = ctx

    @property
    def name(self) -> str:
        return "life_action"

    @property
    def description(self) -> str:
        return (
            "Create or stage high-risk life action proposals for user approval. "
            "Use this before bookings, payments, purchases, third-party messages, account changes, "
            "health bookings, smart-home changes, or destructive data actions. "
            "This tool records the proposal in life/pending-actions.json and stages /approval; "
            "it does not execute the external action."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return tool_parameters_schema(
            action=StringSchema("Action", enum=["propose", "stage_existing"]),
            pendingActionId=StringSchema("Existing life/pending-actions id for stage_existing", nullable=True),
            title=StringSchema("Short action title", nullable=True),
            summary=StringSchema("Exact human-readable action summary", nullable=True),
            risk=StringSchema("Risk level", enum=["medium", "high", "critical"], nullable=True),
            actionType=StringSchema(
                "Action type",
                enum=[
                    "booking",
                    "payment",
                    "message",
                    "purchase",
                    "account-change",
                    "calendar-write",
                    "smart-home",
                    "health",
                    "delete-data",
                    "other",
                ],
                nullable=True,
            ),
            externalSystem=StringSchema("Target external system", nullable=True),
            payloadSummary=StringSchema("Concise non-secret fields that would be submitted", nullable=True),
            money=StringSchema("Optional amount/currency", nullable=True),
            recipient=StringSchema("Optional recipient or merchant", nullable=True),
            scheduledFor=StringSchema("Optional date/time", nullable=True),
            requiresSecondConfirmation=BooleanSchema(
                description="Require second confirmation before execution",
                nullable=True,
            ),
            required=["action"],
        )

    async def execute(
        self,
        action: str,
        pending_action_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        ctx = self._request_context
        session_key = ctx.session_key if ctx else None
        channel = ctx.channel if ctx else None
        chat_id = ctx.chat_id if ctx else None
        normalized = str(action or "").strip()
        if normalized == "stage_existing":
            pending_action_id = pending_action_id or kwargs.get("pendingActionId")
            return _tool_result(
                stage_existing_life_action(
                    self.workspace,
                    str(pending_action_id or ""),
                    session_key=session_key,
                    channel=channel,
                    chat_id=chat_id,
                )
            )
        if normalized == "propose":
            if not self.require_approval:
                return _tool_result({"success": False, "error": "life_action requires approval staging."})
            return _tool_result(
                create_life_action_proposal(
                    self.workspace,
                    kwargs,
                    session_key=session_key,
                    channel=channel,
                    chat_id=chat_id,
                )
            )
        return _tool_result({"success": False, "error": f"Unsupported action: {action}"})
