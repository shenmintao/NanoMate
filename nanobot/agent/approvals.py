"""File-backed pending approvals for agent-initiated writes."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


class ApprovalStore:
    """Persist approval records under the active workspace.

    Records are intentionally small JSON blobs.  The tool that created a record
    owns the payload shape; command handlers decide how to apply each kind.
    """

    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace)
        self.approvals_dir = self.workspace / "approvals"
        self.pending_file = self.approvals_dir / "pending.json"

    def _load(self) -> list[dict[str, Any]]:
        if not self.pending_file.exists():
            return []
        try:
            data = json.loads(self.pending_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(data, dict):
            records = data.get("pending", [])
        else:
            records = data
        return [record for record in records if isinstance(record, dict)]

    def _save(self, records: list[dict[str, Any]]) -> None:
        self.approvals_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.pending_file.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps({"pending": records}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, self.pending_file)

    @staticmethod
    def _matches(record: dict[str, Any], *, session_key: str | None) -> bool:
        if session_key is None:
            return True
        return str(record.get("session_key") or "") == session_key

    def create(
        self,
        *,
        kind: str,
        summary: str,
        payload: dict[str, Any],
        session_key: str | None,
        channel: str | None,
        chat_id: str | None,
        origin: str = "agent",
    ) -> dict[str, Any]:
        records = self._load()
        record = {
            "id": uuid.uuid4().hex[:8],
            "kind": kind,
            "summary": summary.strip(),
            "payload": payload,
            "session_key": session_key or "",
            "channel": channel or "",
            "chat_id": chat_id or "",
            "origin": origin,
            "created_at": time.time(),
        }
        records.append(record)
        self._save(records)
        return record

    def list(self, *, session_key: str | None = None) -> list[dict[str, Any]]:
        records = self._load()
        return [
            record for record in records
            if self._matches(record, session_key=session_key)
        ]

    def get(self, approval_id: str, *, session_key: str | None = None) -> dict[str, Any] | None:
        needle = approval_id.strip().lower()
        if not needle:
            return None
        matches = [
            record for record in self._load()
            if str(record.get("id") or "").lower().startswith(needle)
            and self._matches(record, session_key=session_key)
        ]
        return matches[0] if len(matches) == 1 else None

    def remove(self, approval_id: str) -> bool:
        records = self._load()
        remaining = [
            record for record in records
            if str(record.get("id") or "") != approval_id
        ]
        if len(remaining) == len(records):
            return False
        self._save(remaining)
        return True
