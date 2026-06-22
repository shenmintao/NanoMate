"""Structured life data storage tool for the life-assistant branch."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.schema import (
    BooleanSchema,
    IntegerSchema,
    StringSchema,
    tool_parameters_schema,
)
from nanobot.config_base import Base


class LifeDataToolConfig(Base):
    """Configuration for structured life data writes."""

    enable: bool = True


@dataclass(frozen=True)
class _CollectionSpec:
    file_name: str
    kind: str
    id_prefix: str
    description: str


_ARRAY = "array"
_OBJECT = "object"
_TEXT = "text"

_COLLECTIONS: dict[str, _CollectionSpec] = {
    "tasks": _CollectionSpec("tasks.json", _ARRAY, "task", "Tasks, errands, and follow-ups"),
    "calendar": _CollectionSpec("calendar.json", _ARRAY, "event", "Appointments, plans, deadlines, and reservations"),
    "reminders": _CollectionSpec("reminders.json", _ARRAY, "rem", "Reminder definitions and cron metadata"),
    "ledger": _CollectionSpec("ledger.json", _ARRAY, "txn", "Expenses, income, budgets, and reimbursements"),
    "subscriptions": _CollectionSpec("subscriptions.json", _ARRAY, "sub", "Recurring bills, renewals, memberships, and trials"),
    "people": _CollectionSpec("people.json", _ARRAY, "person", "Contacts and relationship context"),
    "preferences": _CollectionSpec("preferences.json", _OBJECT, "pref", "Stable user preferences grouped by domain"),
    "goals": _CollectionSpec("goals.json", _ARRAY, "goal", "Goals, habits, and progress checkpoints"),
    "documents": _CollectionSpec("documents.json", _ARRAY, "doc", "Documents, warranties, IDs, contracts, and renewals"),
    "trips": _CollectionSpec("trips.json", _ARRAY, "trip", "Travel plans, ticket candidates, hotels, and itinerary state"),
    "express": _CollectionSpec("express.json", _ARRAY, "pkg", "Package tracking records"),
    "shopping": _CollectionSpec("shopping.json", _ARRAY, "shop", "Shopping lists, price watches, orders, and wish lists"),
    "local_services": _CollectionSpec("local-services.json", _ARRAY, "svc", "Restaurants, services, reservations, and errands"),
    "smart_home": _CollectionSpec("smart-home.json", _OBJECT, "home", "Home devices, scenes, and safety notes"),
    "health": _CollectionSpec("health.json", _ARRAY, "health", "Medication reminders, appointments, and health admin notes"),
    "pending_actions": _CollectionSpec("pending-actions.json", _ARRAY, "act", "Proposed high-risk external actions awaiting approval"),
    "mood": _CollectionSpec("mood.json", _ARRAY, "mood", "Structured mood trend records"),
    "journal": _CollectionSpec("journal.md", _TEXT, "journal", "Daily reflections, mood notes, and companion-relevant memories"),
    "notes": _CollectionSpec("notes.md", _TEXT, "note", "Freeform personal notes"),
    "audit": _CollectionSpec("audit.md", _TEXT, "audit", "Human-readable life data audit log"),
}

_WRITING_ACTIONS = {"add", "update", "archive", "merge", "replace", "append"}
_MAX_TEXT_CHARS = 200_000


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class LifeDataTool(Tool):
    """Read and update structured personal life data under workspace/life."""

    config_key = "life_data"
    _scopes = {"core", "subagent"}

    @classmethod
    def config_cls(cls):
        return LifeDataToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        return bool(getattr(ctx.config.life_data, "enable", True))

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(workspace=Path(ctx.workspace), timezone=getattr(ctx, "timezone", "UTC"))

    def __init__(self, workspace: Path | str, *, timezone: str = "UTC") -> None:
        self.workspace = Path(workspace)
        self.life_dir = self.workspace / "life"
        self.timezone = timezone or "UTC"

    @property
    def name(self) -> str:
        return "life_data"

    @property
    def description(self) -> str:
        return (
            "Safely read and update structured life-assistant records under workspace/life. "
            "Supports tasks, calendar, reminders, ledger, subscriptions, people, preferences, "
            "goals, documents, trips, express, shopping, local_services, smart_home, health, "
            "pending_actions, mood, journal, notes, and audit. Writes are local, append audit "
            "entries automatically, and archive instead of hard-delete."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return tool_parameters_schema(
            action=StringSchema(
                "Action to perform",
                enum=["schema", "list", "get", "add", "update", "archive", "merge", "replace", "append"],
            ),
            collection=StringSchema(
                "Life data collection",
                enum=list(_COLLECTIONS),
                nullable=True,
            ),
            id=StringSchema("Record id for get/update/archive", nullable=True),
            record={
                "type": ["object", "null"],
                "description": "Record object for add/update/merge/replace",
                "additionalProperties": True,
            },
            text=StringSchema("Text to append to journal/notes/audit", nullable=True),
            auditNote=StringSchema("Short reason for the audit log", nullable=True),
            includeArchived=BooleanSchema(description="Include archived records in list results", default=False),
            limit=IntegerSchema(50, description="Maximum records to return", minimum=1, maximum=500),
            required=["action"],
        )

    async def execute(
        self,
        action: str,
        collection: str | None = None,
        id: str | None = None,
        record: dict[str, Any] | None = None,
        text: str | None = None,
        audit_note: str | None = None,
        include_archived: bool = False,
        limit: int = 50,
        **kwargs: Any,
    ) -> str:
        action = str(action or "").strip()
        collection = collection or kwargs.get("name")
        audit_note = kwargs.get("auditNote", audit_note)
        include_archived = bool(kwargs.get("includeArchived", include_archived))
        if action == "schema":
            return _json({"success": True, "collections": self._schema()})
        if not collection:
            return _json({"success": False, "error": "collection is required unless action='schema'."})
        if collection not in _COLLECTIONS:
            return _json({
                "success": False,
                "error": f"Unsupported life data collection: {collection}",
                "allowed": list(_COLLECTIONS),
            })
        spec = _COLLECTIONS[collection]
        try:
            if action == "list":
                return _json(self._list(collection, spec, include_archived=include_archived, limit=limit))
            if action == "get":
                return _json(self._get(collection, spec, id))
            if action == "add":
                return _json(self._add(collection, spec, record, audit_note=audit_note))
            if action == "update":
                return _json(self._update(collection, spec, id, record, audit_note=audit_note))
            if action == "archive":
                return _json(self._archive(collection, spec, id, audit_note=audit_note))
            if action == "merge":
                return _json(self._merge_object(collection, spec, record, audit_note=audit_note))
            if action == "replace":
                return _json(self._replace_object(collection, spec, record, audit_note=audit_note))
            if action == "append":
                return _json(self._append_text(collection, spec, text, audit_note=audit_note))
            return _json({"success": False, "error": f"Unsupported action: {action}"})
        except ValueError as exc:
            return _json({"success": False, "error": str(exc), "collection": collection})
        except OSError as exc:
            return _json({"success": False, "error": f"File error: {exc}", "collection": collection})

    def _schema(self) -> dict[str, Any]:
        return {
            name: {
                "file": f"life/{spec.file_name}",
                "kind": spec.kind,
                "idPrefix": spec.id_prefix,
                "description": spec.description,
            }
            for name, spec in _COLLECTIONS.items()
        }

    def _path(self, spec: _CollectionSpec) -> Path:
        return self.life_dir / spec.file_name

    def _now(self) -> datetime:
        try:
            tz = ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            tz = UTC
        return datetime.now(tz)

    def _now_iso(self) -> str:
        return self._now().isoformat(timespec="seconds")

    def _new_id(self, spec: _CollectionSpec) -> str:
        stamp = self._now().strftime("%Y%m%d-%H%M%S")
        return f"{spec.id_prefix}-{stamp}-{uuid.uuid4().hex[:6]}"

    def _read_json(self, spec: _CollectionSpec) -> Any:
        path = self._path(spec)
        if not path.exists():
            return [] if spec.kind == _ARRAY else {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name} contains invalid JSON: {exc}") from exc
        if spec.kind == _ARRAY and not isinstance(data, list):
            raise ValueError(f"{path.name} must contain a JSON array.")
        if spec.kind == _OBJECT and not isinstance(data, dict):
            raise ValueError(f"{path.name} must contain a JSON object.")
        return data

    def _write_json(self, spec: _CollectionSpec, data: Any) -> None:
        _write_text(self._path(spec), json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    def _read_text(self, spec: _CollectionSpec) -> str:
        path = self._path(spec)
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8")
        if len(content) > _MAX_TEXT_CHARS:
            return content[-_MAX_TEXT_CHARS:]
        return content

    def _append_audit(self, collection: str, spec: _CollectionSpec, note: str | None) -> None:
        if collection == "audit":
            return
        audit_spec = _COLLECTIONS["audit"]
        reason = (note or f"{collection} {spec.kind} updated").strip()
        timestamp = self._now().strftime("%Y-%m-%d %H:%M")
        line = f"{timestamp} - changed life/{spec.file_name}: {reason}\n"
        path = self._path(audit_spec)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        _write_text(path, existing + line)

    def _require_array(self, spec: _CollectionSpec) -> None:
        if spec.kind != _ARRAY:
            raise ValueError("This action is only valid for array collections.")

    def _require_object(self, spec: _CollectionSpec) -> None:
        if spec.kind != _OBJECT:
            raise ValueError("This action is only valid for object collections.")

    def _require_text(self, spec: _CollectionSpec) -> None:
        if spec.kind != _TEXT:
            raise ValueError("This action is only valid for text collections.")

    def _list(
        self,
        collection: str,
        spec: _CollectionSpec,
        *,
        include_archived: bool,
        limit: int,
    ) -> dict[str, Any]:
        if spec.kind == _TEXT:
            content = self._read_text(spec)
            return {
                "success": True,
                "collection": collection,
                "file": f"life/{spec.file_name}",
                "kind": spec.kind,
                "text": content[-_MAX_TEXT_CHARS:],
            }
        data = self._read_json(spec)
        if spec.kind == _ARRAY:
            records = [
                item for item in data
                if isinstance(item, dict) and (include_archived or not item.get("archived_at"))
            ]
            return {
                "success": True,
                "collection": collection,
                "file": f"life/{spec.file_name}",
                "kind": spec.kind,
                "records": records[:limit],
                "total": len(records),
            }
        return {
            "success": True,
            "collection": collection,
            "file": f"life/{spec.file_name}",
            "kind": spec.kind,
            "record": data,
        }

    def _get(self, collection: str, spec: _CollectionSpec, record_id: str | None) -> dict[str, Any]:
        if spec.kind in {_OBJECT, _TEXT}:
            return self._list(collection, spec, include_archived=True, limit=1)
        self._require_array(spec)
        if not record_id:
            raise ValueError("id is required for get on array collections.")
        records = self._read_json(spec)
        match = next((item for item in records if isinstance(item, dict) and item.get("id") == record_id), None)
        if match is None:
            return {"success": False, "error": f"Record not found: {record_id}", "collection": collection}
        return {"success": True, "collection": collection, "record": match}

    def _add(
        self,
        collection: str,
        spec: _CollectionSpec,
        record: dict[str, Any] | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_array(spec)
        if not isinstance(record, dict) or not record:
            raise ValueError("record object is required for add.")
        records = self._read_json(spec)
        now = self._now_iso()
        new_record = dict(record)
        new_record.setdefault("id", self._new_id(spec))
        new_record.setdefault("created_at", now)
        new_record["updated_at"] = now
        if any(isinstance(item, dict) and item.get("id") == new_record["id"] for item in records):
            raise ValueError(f"Record id already exists: {new_record['id']}")
        records.append(new_record)
        self._write_json(spec, records)
        self._append_audit(collection, spec, audit_note or f"added {new_record['id']}")
        return {
            "success": True,
            "collection": collection,
            "file": f"life/{spec.file_name}",
            "record": new_record,
        }

    def _update(
        self,
        collection: str,
        spec: _CollectionSpec,
        record_id: str | None,
        record: dict[str, Any] | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_array(spec)
        if not record_id:
            raise ValueError("id is required for update.")
        if not isinstance(record, dict) or not record:
            raise ValueError("record object is required for update.")
        records = self._read_json(spec)
        for index, item in enumerate(records):
            if isinstance(item, dict) and item.get("id") == record_id:
                updated = _deep_merge(item, record)
                updated["id"] = record_id
                updated["updated_at"] = self._now_iso()
                records[index] = updated
                self._write_json(spec, records)
                self._append_audit(collection, spec, audit_note or f"updated {record_id}")
                return {
                    "success": True,
                    "collection": collection,
                    "file": f"life/{spec.file_name}",
                    "record": updated,
                }
        return {"success": False, "error": f"Record not found: {record_id}", "collection": collection}

    def _archive(
        self,
        collection: str,
        spec: _CollectionSpec,
        record_id: str | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_array(spec)
        if not record_id:
            raise ValueError("id is required for archive.")
        return self._update(
            collection,
            spec,
            record_id,
            {"archived_at": self._now_iso(), "status": "archived"},
            audit_note=audit_note or f"archived {record_id}",
        )

    def _merge_object(
        self,
        collection: str,
        spec: _CollectionSpec,
        record: dict[str, Any] | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_object(spec)
        if not isinstance(record, dict):
            raise ValueError("record object is required for merge.")
        existing = self._read_json(spec)
        merged = _deep_merge(existing, record)
        merged["updated_at"] = self._now_iso()
        self._write_json(spec, merged)
        self._append_audit(collection, spec, audit_note or f"merged {collection}")
        return {
            "success": True,
            "collection": collection,
            "file": f"life/{spec.file_name}",
            "record": merged,
        }

    def _replace_object(
        self,
        collection: str,
        spec: _CollectionSpec,
        record: dict[str, Any] | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_object(spec)
        if not isinstance(record, dict):
            raise ValueError("record object is required for replace.")
        replaced = dict(record)
        replaced["updated_at"] = self._now_iso()
        self._write_json(spec, replaced)
        self._append_audit(collection, spec, audit_note or f"replaced {collection}")
        return {
            "success": True,
            "collection": collection,
            "file": f"life/{spec.file_name}",
            "record": replaced,
        }

    def _append_text(
        self,
        collection: str,
        spec: _CollectionSpec,
        text: str | None,
        *,
        audit_note: str | None,
    ) -> dict[str, Any]:
        self._require_text(spec)
        if not text or not text.strip():
            raise ValueError("text is required for append.")
        path = self._path(spec)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        separator = "" if not existing or existing.endswith("\n") else "\n"
        entry = text.strip()
        _write_text(path, f"{existing}{separator}{entry}\n")
        self._append_audit(collection, spec, audit_note or f"appended to {collection}")
        return {
            "success": True,
            "collection": collection,
            "file": f"life/{spec.file_name}",
            "chars": len(entry),
        }
