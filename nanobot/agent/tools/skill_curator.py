"""Hermes-style curation for agent-created workspace skills."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.context import ContextAware, RequestContext
from nanobot.agent.tools.schema import (
    IntegerSchema,
    NumberSchema,
    StringSchema,
    tool_parameters_schema,
)
from nanobot.agent.tools.skill_manage import (
    AGENT_SKILL_META_FILE,
    _parse_skill_frontmatter,
    _similarity,
    _skill_match_text,
    _validate_skill_name,
    _validate_within,
)
from nanobot.config_base import Base


class SkillCuratorToolConfig(Base):
    """Configuration for workspace skill curation."""

    enable: bool = True
    require_approval: bool = True
    stale_days: int = 90
    similarity_threshold: float = 0.58


def _tool_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _skills_dir(workspace: str | Path) -> Path:
    return Path(workspace) / "skills"


def _archive_dir(workspace: str | Path) -> Path:
    return _skills_dir(workspace) / ".archive"


def _meta_path(skill_dir: Path) -> Path:
    return skill_dir / AGENT_SKILL_META_FILE


def _read_meta(skill_dir: Path) -> dict[str, Any]:
    meta_file = _meta_path(skill_dir)
    if not meta_file.exists():
        return {}
    try:
        data = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _write_meta(skill_dir: Path, meta: dict[str, Any]) -> None:
    _write_text(_meta_path(skill_dir), json.dumps(meta, ensure_ascii=False, indent=2))


def _is_agent_created(meta: dict[str, Any]) -> bool:
    return str(meta.get("created_by") or meta.get("createdBy") or "") == "agent"


def _read_skill_content(skill_file: Path) -> str | None:
    try:
        return skill_file.read_text(encoding="utf-8")
    except OSError:
        return None


def _workspace_skill_snapshots(workspace: str | Path) -> list[dict[str, Any]]:
    root = _skills_dir(workspace)
    if not root.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name == ".archive" or skill_dir.is_symlink():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        content = _read_skill_content(skill_file)
        if content is None:
            continue
        meta = _read_meta(skill_dir)
        frontmatter = _parse_skill_frontmatter(content)
        snapshots.append({
            "name": skill_dir.name,
            "path": str(skill_file),
            "description": str(frontmatter.get("description") or ""),
            "meta": meta,
            "agent_created": _is_agent_created(meta),
            "pinned": bool(meta.get("pinned", False)),
            "created_at": meta.get("created_at"),
            "updated_at": meta.get("updated_at"),
            "text": _skill_match_text(content),
        })
    return snapshots


def _builtin_skill_snapshots() -> list[dict[str, Any]]:
    from nanobot.agent.skills import BUILTIN_SKILLS_DIR

    if not BUILTIN_SKILLS_DIR.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for skill_dir in sorted(BUILTIN_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        content = _read_skill_content(skill_file)
        if content is None:
            continue
        frontmatter = _parse_skill_frontmatter(content)
        snapshots.append({
            "name": skill_dir.name,
            "source": "builtin",
            "path": str(skill_file),
            "description": str(frontmatter.get("description") or ""),
            "text": _skill_match_text(content),
        })
    return snapshots


def _reference_snapshots(workspace: str | Path) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for snapshot in _workspace_skill_snapshots(workspace):
        refs.append({
            "name": snapshot["name"],
            "source": "workspace",
            "path": snapshot["path"],
            "description": snapshot["description"],
            "text": snapshot["text"],
        })
    refs.extend(_builtin_skill_snapshots())
    return refs


def _duplicate_candidates(
    workspace: str | Path,
    managed: list[dict[str, Any]],
    *,
    threshold: float,
) -> list[dict[str, Any]]:
    refs = _reference_snapshots(workspace)
    candidates: list[dict[str, Any]] = []
    for skill in managed:
        matches: list[dict[str, Any]] = []
        for ref in refs:
            if ref["source"] == "workspace" and ref["name"] == skill["name"]:
                continue
            exact_name = ref["name"] == skill["name"]
            score = _similarity(skill["text"], ref["text"])
            if exact_name or score >= threshold:
                matches.append({
                    "name": ref["name"],
                    "source": ref["source"],
                    "path": ref["path"],
                    "score": round(score, 3),
                    "reason": "name" if exact_name else "similarity",
                    "description": ref["description"],
                })
        if matches:
            matches.sort(key=lambda item: (item["reason"] != "name", -float(item["score"])))
            candidates.append({
                "name": skill["name"],
                "pinned": skill["pinned"],
                "matches": matches[:5],
                "suggested_action": "keep pinned" if skill["pinned"] else "archive or merge into the closest match",
            })
    return candidates


def audit_skills(
    workspace: str | Path,
    *,
    stale_days: int = 90,
    similarity_threshold: float = 0.58,
) -> dict[str, Any]:
    snapshots = _workspace_skill_snapshots(workspace)
    managed = [item for item in snapshots if item["agent_created"]]
    now = time.time()
    stale_cutoff = now - max(1, int(stale_days)) * 86400
    stale = [
        {
            "name": item["name"],
            "path": item["path"],
            "updated_at": item.get("updated_at"),
            "suggested_action": "archive or refresh",
        }
        for item in managed
        if not item["pinned"]
        and isinstance(item.get("updated_at"), int | float)
        and float(item["updated_at"]) < stale_cutoff
    ]
    duplicates = _duplicate_candidates(
        workspace,
        managed,
        threshold=max(0.0, min(1.0, float(similarity_threshold))),
    )
    return {
        "success": True,
        "managed_count": len(managed),
        "unmanaged_count": len(snapshots) - len(managed),
        "managed_skills": [
            {
                "name": item["name"],
                "description": item["description"],
                "pinned": item["pinned"],
                "updated_at": item.get("updated_at"),
            }
            for item in managed
        ],
        "duplicate_candidates": duplicates,
        "stale_candidates": stale,
        "message": (
            "Only skills marked created_by=agent in "
            f"{AGENT_SKILL_META_FILE} are eligible for curator archive/pin actions."
        ),
    }


def _require_agent_created_skill(workspace: str | Path, name: str) -> tuple[Path | None, dict[str, Any], str | None]:
    if err := _validate_skill_name(name):
        return None, {}, err
    root = _skills_dir(workspace)
    skill_dir = root / name
    if not skill_dir.exists():
        return None, {}, f"Skill '{name}' not found."
    if skill_dir.is_symlink():
        return None, {}, "Refusing to curate a symlinked skill directory."
    if err := _validate_within(root, skill_dir):
        return None, {}, err
    if not (skill_dir / "SKILL.md").exists():
        return None, {}, f"Skill '{name}' has no SKILL.md."
    meta = _read_meta(skill_dir)
    if not _is_agent_created(meta):
        return None, {}, f"Skill '{name}' is not marked as agent-created; refusing to curate it."
    return skill_dir, meta, None


def _archive_skill(workspace: str | Path, name: str, reason: str | None = None) -> dict[str, Any]:
    skill_dir, meta, error = _require_agent_created_skill(workspace, name)
    if error:
        return {"success": False, "error": error}
    assert skill_dir is not None
    if bool(meta.get("pinned", False)):
        return {"success": False, "error": f"Skill '{name}' is pinned; unpin before archiving."}
    archive_root = _archive_dir(workspace)
    archive_root.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    target = archive_root / f"{name}-{timestamp}"
    suffix = 1
    while target.exists():
        suffix += 1
        target = archive_root / f"{name}-{timestamp}-{suffix}"
    if err := _validate_within(archive_root, target):
        return {"success": False, "error": err}
    shutil.move(str(skill_dir), str(target))
    meta.update({
        "archived_at": time.time(),
        "archive_reason": str(reason or "curated"),
        "original_name": name,
        "updated_at": time.time(),
    })
    _write_meta(target, meta)
    return {
        "success": True,
        "message": f"Archived agent-created skill '{name}'.",
        "path": str(target),
    }


def _set_pin(workspace: str | Path, name: str, pinned: bool) -> dict[str, Any]:
    skill_dir, meta, error = _require_agent_created_skill(workspace, name)
    if error:
        return {"success": False, "error": error}
    assert skill_dir is not None
    meta["pinned"] = pinned
    meta["updated_at"] = time.time()
    _write_meta(skill_dir, meta)
    state = "pinned" if pinned else "unpinned"
    return {"success": True, "message": f"Skill '{name}' {state}.", "path": str(skill_dir)}


def apply_skill_curator_payload(workspace: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    name = str(payload.get("name") or "").strip()
    if action == "audit":
        return audit_skills(
            workspace,
            stale_days=int(payload.get("stale_days", payload.get("staleDays", 90)) or 90),
            similarity_threshold=float(
                payload.get("similarity_threshold", payload.get("similarityThreshold", 0.58)) or 0.58
            ),
        )
    if action == "archive":
        return _archive_skill(workspace, name, str(payload.get("reason") or ""))
    if action == "pin":
        return _set_pin(workspace, name, True)
    if action == "unpin":
        return _set_pin(workspace, name, False)
    return {"success": False, "error": f"Unknown skill_curator action '{action}'."}


def _summary_for(payload: dict[str, Any]) -> str:
    action = payload.get("action")
    name = payload.get("name")
    if action == "archive":
        return f"Archive agent-created skill `{name}`."
    if action == "pin":
        return f"Pin agent-created skill `{name}`."
    if action == "unpin":
        return f"Unpin agent-created skill `{name}`."
    return f"Run skill_curator action `{action}` for `{name}`."


class SkillCuratorTool(Tool, ContextAware):
    """Audit and soft-archive agent-created workspace skills."""

    config_key = "skill_curator"

    @classmethod
    def config_cls(cls):
        return SkillCuratorToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        return bool(getattr(ctx.config.skill_curator, "enable", True))

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(
            workspace=Path(ctx.workspace),
            require_approval=ctx.config.skill_curator.require_approval,
            stale_days=ctx.config.skill_curator.stale_days,
            similarity_threshold=ctx.config.skill_curator.similarity_threshold,
        )

    def __init__(
        self,
        workspace: str | Path,
        *,
        require_approval: bool = True,
        stale_days: int = 90,
        similarity_threshold: float = 0.58,
    ) -> None:
        self.workspace = Path(workspace)
        self.require_approval = require_approval
        self.stale_days = stale_days
        self.similarity_threshold = similarity_threshold
        self._request_context: RequestContext | None = None

    def set_context(self, ctx: RequestContext) -> None:
        self._request_context = ctx

    @property
    def name(self) -> str:
        return "skill_curator"

    @property
    def description(self) -> str:
        return (
            "Audit and curate workspace skills created by the agent. Use this to prevent many "
            "similar skills from accumulating: audit for duplicate/stale agent-created skills, "
            "pin important ones, or soft-archive obsolete ones. It refuses to archive built-in, "
            "companion-template, or manually created workspace skills."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return tool_parameters_schema(
            action=StringSchema("Action", enum=["audit", "archive", "pin", "unpin"]),
            name=StringSchema("Workspace skill directory name for archive/pin/unpin", nullable=True),
            reason=StringSchema("Reason for archive", nullable=True),
            staleDays=IntegerSchema(description="Override stale-day threshold for audit", minimum=1, nullable=True),
            similarityThreshold=NumberSchema(
                description="Override duplicate similarity threshold for audit",
                minimum=0,
                maximum=1,
                nullable=True,
            ),
            required=["action"],
        )

    async def execute(
        self,
        action: str,
        name: str | None = None,
        reason: str | None = None,
        stale_days: int | None = None,
        similarity_threshold: float | None = None,
        **kwargs: Any,
    ) -> str:
        normalized = str(action or "").strip()
        if normalized == "audit":
            return _tool_result(
                audit_skills(
                    self.workspace,
                    stale_days=stale_days
                    or kwargs.get("staleDays")
                    or self.stale_days,
                    similarity_threshold=similarity_threshold
                    or kwargs.get("similarityThreshold")
                    or self.similarity_threshold,
                )
            )

        payload = {
            "action": normalized,
            "name": str(name or kwargs.get("name") or "").strip(),
            "reason": reason or kwargs.get("reason") or "",
        }
        if normalized not in {"archive", "pin", "unpin"}:
            return _tool_result({"success": False, "error": f"Unsupported action: {action}"})
        if not payload["name"]:
            return _tool_result({"success": False, "error": "name is required."})
        if not self.require_approval:
            return _tool_result(apply_skill_curator_payload(self.workspace, payload))

        ctx = self._request_context
        record = ApprovalStore(self.workspace).create(
            kind="skill_curator",
            summary=_summary_for(payload),
            payload=payload,
            session_key=ctx.session_key if ctx else None,
            channel=ctx.channel if ctx else None,
            chat_id=ctx.chat_id if ctx else None,
        )
        return _tool_result({
            "success": True,
            "pending_approval": True,
            "id": record["id"],
            "summary": record["summary"],
            "message": (
                f"Staged skill curation as `{record['id']}`. "
                "The user can reply `approve` / `reject`, or run `/approval` to review pending items."
            ),
        })
