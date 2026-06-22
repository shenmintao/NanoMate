"""Agent-managed workspace skill writes with approval gating."""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.skills import BUILTIN_SKILLS_DIR
from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.context import ContextAware, RequestContext
from nanobot.agent.tools.schema import BooleanSchema, StringSchema, tool_parameters_schema
from nanobot.config_base import Base


class SkillManageToolConfig(Base):
    """Configuration for agent-managed skill writes."""

    enable: bool = True
    require_approval: bool = True


_VALID_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_ALLOWED_SUPPORT_DIRS = {"references", "templates", "scripts", "assets"}
_MAX_SKILL_CONTENT_CHARS = 100_000
_MAX_SUPPORT_FILE_CHARS = 1_000_000
_MAX_IMPORT_URL_CHARS = _MAX_SKILL_CONTENT_CHARS
_SIMILARITY_THRESHOLD = 0.58
AGENT_SKILL_META_FILE = ".nanomate-skill.json"


def _tool_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _validate_skill_name(name: str) -> str | None:
    if not name or not isinstance(name, str):
        return "Skill name is required."
    if not _VALID_NAME_RE.fullmatch(name):
        return (
            "Invalid skill name. Use lowercase letters, numbers, dots, "
            "underscores, or hyphens; start with a letter or digit."
        )
    return None


def _skill_dir(workspace: Path, name: str) -> Path:
    return workspace / "skills" / name


def _validate_within(base: Path, target: Path) -> str | None:
    try:
        target.resolve(strict=False).relative_to(base.resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
        return f"Path escapes skill directory: {target}"
    return None


def _validate_skill_content(content: str) -> str | None:
    if not isinstance(content, str) or not content.strip():
        return "content cannot be empty."
    if len(content) > _MAX_SKILL_CONTENT_CHARS:
        return f"content exceeds {_MAX_SKILL_CONTENT_CHARS} characters."
    if not content.startswith("---"):
        return "SKILL.md must start with YAML frontmatter."
    end = re.search(r"\n---\s*\n", content[3:])
    if not end:
        return "SKILL.md frontmatter is not closed."
    raw_yaml = content[3:end.start() + 3]
    try:
        meta = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        return f"YAML frontmatter parse error: {exc}"
    if not isinstance(meta, dict):
        return "frontmatter must be a YAML mapping."
    if not meta.get("name"):
        return "frontmatter must include name."
    if not meta.get("description"):
        return "frontmatter must include description."
    if not content[end.end() + 3:].strip():
        return "SKILL.md must include instructions after frontmatter."
    return None


def _parse_skill_frontmatter(content: str) -> dict[str, Any]:
    if not content.startswith("---"):
        return {}
    end = re.search(r"\n---\s*\n", content[3:])
    if not end:
        return {}
    raw_yaml = content[3:end.start() + 3]
    try:
        meta = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return {}
    return meta if isinstance(meta, dict) else {}


def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    end = re.search(r"\n---\s*\n", content[3:])
    if not end:
        return content
    return content[end.end() + 3:]


def _skill_match_text(content: str) -> str:
    meta = _parse_skill_frontmatter(content)
    pieces = [
        str(meta.get("name") or ""),
        str(meta.get("description") or ""),
        _strip_frontmatter(content)[:5000],
    ]
    return "\n".join(pieces)


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    words = set(re.findall(r"[a-z0-9][a-z0-9_-]{1,}", lowered))
    cjk = re.findall(r"[\u4e00-\u9fff]", lowered)
    words.update("".join(cjk[i:i + 2]) for i in range(max(0, len(cjk) - 1)))
    return {word for word in words if len(word) >= 2}


def _similarity(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _skill_snapshots(workspace: Path) -> list[dict[str, Any]]:
    roots = [
        ("workspace", workspace / "skills"),
        ("builtin", BUILTIN_SKILLS_DIR),
    ]
    snapshots: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for source, root in roots:
        if not root.exists():
            continue
        for skill_dir in sorted(root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            name = skill_dir.name
            if name in seen_names:
                continue
            try:
                content = skill_file.read_text(encoding="utf-8")
            except OSError:
                continue
            meta = _parse_skill_frontmatter(content)
            snapshots.append({
                "name": name,
                "frontmatter_name": str(meta.get("name") or ""),
                "description": str(meta.get("description") or ""),
                "source": source,
                "path": str(skill_file),
                "text": _skill_match_text(content),
            })
            seen_names.add(name)
    return snapshots


def _find_similar_skills(
    workspace: Path,
    name: str,
    content: str,
    *,
    ignore_name: str | None = None,
) -> list[dict[str, Any]]:
    meta = _parse_skill_frontmatter(content)
    frontmatter_name = str(meta.get("name") or "")
    target_text = _skill_match_text(content)
    matches: list[dict[str, Any]] = []
    for snapshot in _skill_snapshots(workspace):
        if ignore_name and snapshot["name"] == ignore_name:
            continue
        exact_name = name in {snapshot["name"], snapshot["frontmatter_name"]}
        exact_frontmatter_name = (
            bool(frontmatter_name)
            and frontmatter_name in {snapshot["name"], snapshot["frontmatter_name"]}
        )
        score = _similarity(target_text, snapshot["text"])
        if exact_name or exact_frontmatter_name or score >= _SIMILARITY_THRESHOLD:
            reason = "name" if exact_name or exact_frontmatter_name else "similarity"
            matches.append({
                "name": snapshot["name"],
                "source": snapshot["source"],
                "path": snapshot["path"],
                "score": round(score, 3),
                "reason": reason,
                "description": snapshot["description"],
            })
    matches.sort(key=lambda item: (item["reason"] != "name", -float(item["score"])))
    return matches[:5]


def _duplicate_skill_error(matches: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "success": False,
        "error": (
            "A similar skill already exists. Reuse or patch the existing skill instead "
            "of creating another overlapping skill."
        ),
        "similar_skills": matches,
        "suggestion": "Use action='patch' or action='edit' on the closest existing skill if new instructions are needed.",
    }


def _validate_support_path(file_path: str) -> str | None:
    if not file_path or not isinstance(file_path, str):
        return "file_path is required."
    normalized = Path(file_path)
    if normalized.is_absolute() or ".." in normalized.parts:
        return "file_path must be relative and cannot contain '..'."
    if normalized.name == "SKILL.md" and len(normalized.parts) == 1:
        return None
    if len(normalized.parts) < 2 or normalized.parts[0] not in _ALLOWED_SUPPORT_DIRS:
        allowed = ", ".join(sorted(_ALLOWED_SUPPORT_DIRS))
        return f"file_path must be SKILL.md or live under one of: {allowed}."
    return None


def _safe_raw_github_path_parts(parts: list[str]) -> bool:
    if len(parts) < 4:
        return False
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return parts[-1] == "SKILL.md"


def _normalize_skill_source_url(source_url: str) -> tuple[str | None, str | None]:
    url = (source_url or "").strip(" \t\r\n`\"'")
    if not url:
        return None, "source_url is required."
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None, "source_url must use https."

    if parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 5 and parts[2] == "blob":
            owner, repo, _blob, ref = parts[:4]
            path_parts = parts[4:]
            raw_parts = [owner, repo, ref, *path_parts]
            if _safe_raw_github_path_parts(raw_parts):
                return (
                    f"https://raw.githubusercontent.com/{'/'.join(raw_parts)}",
                    None,
                )

    if parsed.netloc.lower() != "raw.githubusercontent.com":
        return None, "Only raw GitHub SKILL.md URLs are supported for direct skill import."

    parts = [part for part in parsed.path.split("/") if part]
    if not _safe_raw_github_path_parts(parts):
        return None, "source_url must point to a raw GitHub SKILL.md file."
    return url, None


async def _fetch_text_from_url(url: str) -> str:
    import httpx

    from nanobot.security.network import validate_url_target

    ok, error = validate_url_target(url)
    if not ok:
        raise ValueError(f"URL validation failed: {error}")
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
        response = await client.get(url, headers={"Accept": "text/plain"})
        response.raise_for_status()
    if len(response.text) > _MAX_IMPORT_URL_CHARS:
        raise ValueError(f"downloaded skill exceeds {_MAX_IMPORT_URL_CHARS} characters.")
    return response.text


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _managed_meta_path(skill_dir: Path) -> Path:
    return skill_dir / AGENT_SKILL_META_FILE


def _read_agent_skill_meta(skill_dir: Path) -> dict[str, Any]:
    meta_file = _managed_meta_path(skill_dir)
    if not meta_file.exists():
        return {}
    try:
        data = json.loads(meta_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_agent_skill_meta(skill_dir: Path, meta: dict[str, Any]) -> None:
    _write_text(_managed_meta_path(skill_dir), json.dumps(meta, ensure_ascii=False, indent=2))


def _mark_agent_created_skill(
    workspace: Path,
    name: str,
    *,
    source_url: str | None = None,
) -> None:
    skill_dir = _skill_dir(workspace, name)
    existing = _read_agent_skill_meta(skill_dir)
    now = time.time()
    meta: dict[str, Any] = {
        "schema_version": 1,
        "created_by": "agent",
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "pinned": bool(existing.get("pinned", False)),
    }
    if source_url:
        meta["source_url"] = source_url
    elif existing.get("source_url"):
        meta["source_url"] = existing["source_url"]
    _write_agent_skill_meta(skill_dir, meta)


def _touch_agent_managed_skill(workspace: Path, name: str) -> None:
    skill_dir = _skill_dir(workspace, name)
    meta = _read_agent_skill_meta(skill_dir)
    if str(meta.get("created_by") or "") != "agent":
        return
    meta["updated_at"] = time.time()
    _write_agent_skill_meta(skill_dir, meta)


def _create_skill(workspace: Path, name: str, content: str) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    if err := _validate_skill_content(content):
        return {"success": False, "error": err}
    skill_dir = _skill_dir(workspace, name)
    if skill_dir.exists():
        return {"success": False, "error": f"Skill '{name}' already exists."}
    if matches := _find_similar_skills(workspace, name, content):
        return _duplicate_skill_error(matches)
    skill_dir.mkdir(parents=True, exist_ok=False)
    _write_text(skill_dir / "SKILL.md", content)
    _mark_agent_created_skill(workspace, name)
    return {"success": True, "message": f"Skill '{name}' created.", "path": str(skill_dir)}


def _edit_skill(workspace: Path, name: str, content: str) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    if err := _validate_skill_content(content):
        return {"success": False, "error": err}
    skill_dir = _skill_dir(workspace, name)
    if not (skill_dir / "SKILL.md").exists():
        return {"success": False, "error": f"Skill '{name}' not found."}
    _write_text(skill_dir / "SKILL.md", content)
    _touch_agent_managed_skill(workspace, name)
    return {"success": True, "message": f"Skill '{name}' updated.", "path": str(skill_dir)}


def _patch_skill(
    workspace: Path,
    name: str,
    old_string: str,
    new_string: str,
    file_path: str | None,
    replace_all: bool,
) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    target_rel = file_path or "SKILL.md"
    if err := _validate_support_path(target_rel):
        return {"success": False, "error": err}
    skill_dir = _skill_dir(workspace, name)
    target = skill_dir / target_rel
    if err := _validate_within(skill_dir, target):
        return {"success": False, "error": err}
    if not target.exists():
        return {"success": False, "error": f"File not found: {target_rel}"}
    if not old_string:
        return {"success": False, "error": "old_string is required."}
    content = target.read_text(encoding="utf-8")
    count = content.count(old_string)
    if count == 0:
        return {"success": False, "error": "old_string was not found."}
    if count > 1 and not replace_all:
        return {
            "success": False,
            "error": f"old_string matched {count} times. Set replace_all=true or use a more exact string.",
        }
    updated = content.replace(old_string, new_string, -1 if replace_all else 1)
    if target.name == "SKILL.md":
        if err := _validate_skill_content(updated):
            return {"success": False, "error": f"patched SKILL.md would be invalid: {err}"}
    _write_text(target, updated)
    _touch_agent_managed_skill(workspace, name)
    return {
        "success": True,
        "message": f"Skill '{name}' patched.",
        "path": str(target),
        "replacements": count if replace_all else 1,
    }


def _write_support_file(
    workspace: Path,
    name: str,
    file_path: str,
    file_content: str,
) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    if err := _validate_support_path(file_path):
        return {"success": False, "error": err}
    if not isinstance(file_content, str):
        return {"success": False, "error": "file_content must be a string."}
    if len(file_content) > _MAX_SUPPORT_FILE_CHARS:
        return {"success": False, "error": f"file_content exceeds {_MAX_SUPPORT_FILE_CHARS} characters."}
    skill_dir = _skill_dir(workspace, name)
    if not skill_dir.exists():
        return {"success": False, "error": f"Skill '{name}' not found."}
    target = skill_dir / file_path
    if err := _validate_within(skill_dir, target):
        return {"success": False, "error": err}
    if target.name == "SKILL.md" and (err := _validate_skill_content(file_content)):
        return {"success": False, "error": err}
    _write_text(target, file_content)
    _touch_agent_managed_skill(workspace, name)
    return {"success": True, "message": f"Wrote {file_path} for skill '{name}'.", "path": str(target)}


def _delete_skill(workspace: Path, name: str) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    skills_dir = workspace / "skills"
    skill_dir = _skill_dir(workspace, name)
    if not skill_dir.exists():
        return {"success": False, "error": f"Skill '{name}' not found."}
    if skill_dir.is_symlink():
        return {"success": False, "error": "Refusing to delete a symlinked skill directory."}
    if err := _validate_within(skills_dir, skill_dir):
        return {"success": False, "error": err}
    shutil.rmtree(skill_dir)
    return {"success": True, "message": f"Skill '{name}' deleted.", "path": str(skill_dir)}


def _import_url_skill(
    workspace: Path,
    name: str,
    content: str,
    source_url: str,
    overwrite: bool,
) -> dict[str, Any]:
    if err := _validate_skill_name(name):
        return {"success": False, "error": err}
    if err := _validate_skill_content(content):
        return {"success": False, "error": err}
    skill_file = _skill_dir(workspace, name) / "SKILL.md"
    if skill_file.exists():
        if not overwrite:
            return {
                "success": False,
                "error": f"Skill '{name}' already exists. Set overwrite=true to replace it.",
            }
        result = _edit_skill(workspace, name, content)
    else:
        if matches := _find_similar_skills(workspace, name, content):
            return _duplicate_skill_error(matches)
        result = _create_skill(workspace, name, content)
    if result.get("success"):
        _mark_agent_created_skill(workspace, name, source_url=source_url)
        result["message"] = f"Skill '{name}' imported from {source_url}."
    return result


def apply_skill_manage_payload(workspace: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    workspace_path = Path(workspace)
    action = str(payload.get("action") or "").strip()
    name = str(payload.get("name") or "").strip()
    if action == "create":
        return _create_skill(workspace_path, name, str(payload.get("content") or ""))
    if action == "edit":
        return _edit_skill(workspace_path, name, str(payload.get("content") or ""))
    if action == "patch":
        return _patch_skill(
            workspace_path,
            name,
            str(payload.get("old_string") or ""),
            str(payload.get("new_string") or ""),
            payload.get("file_path"),
            bool(payload.get("replace_all", False)),
        )
    if action == "write_file":
        return _write_support_file(
            workspace_path,
            name,
            str(payload.get("file_path") or ""),
            str(payload.get("file_content") or ""),
        )
    if action == "delete":
        return _delete_skill(workspace_path, name)
    if action == "import_url":
        return _import_url_skill(
            workspace_path,
            name,
            str(payload.get("content") or ""),
            str(payload.get("source_url") or ""),
            bool(payload.get("overwrite", False)),
        )
    return {"success": False, "error": f"Unknown action '{action}'."}


def _summary_for(payload: dict[str, Any]) -> str:
    action = payload.get("action")
    name = payload.get("name")
    if action == "create":
        return f"Create workspace skill `{name}`."
    if action == "edit":
        return f"Replace `SKILL.md` for workspace skill `{name}`."
    if action == "patch":
        target = payload.get("file_path") or "SKILL.md"
        return f"Patch `{target}` in workspace skill `{name}`."
    if action == "write_file":
        return f"Write `{payload.get('file_path')}` in workspace skill `{name}`."
    if action == "delete":
        return f"Delete workspace skill `{name}`."
    if action == "import_url":
        return f"Import workspace skill `{name}` from `{payload.get('source_url')}`."
    return f"Run skill_manage action `{action}` for `{name}`."


async def _build_import_url_payload(
    name: str,
    source_url: str | None,
    overwrite: bool,
) -> dict[str, Any]:
    normalized_url, error = _normalize_skill_source_url(source_url or "")
    if error:
        return {"success": False, "error": error}
    assert normalized_url is not None
    try:
        content = await _fetch_text_from_url(normalized_url)
    except Exception as exc:
        return {"success": False, "error": f"Could not fetch skill: {exc}"}
    if err := _validate_skill_content(content):
        return {"success": False, "error": f"Downloaded SKILL.md is invalid: {err}"}
    return {
        "success": True,
        "payload": {
            "action": "import_url",
            "name": name,
            "source_url": normalized_url,
            "content": content,
            "overwrite": overwrite,
        },
    }


class SkillManageTool(Tool, ContextAware):
    """Create and update workspace skills, normally via pending approval."""

    config_key = "skill_manage"

    @classmethod
    def config_cls(cls):
        return SkillManageToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        return ctx.config.skill_manage.enable

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(
            workspace=Path(ctx.workspace),
            require_approval=ctx.config.skill_manage.require_approval,
        )

    def __init__(self, workspace: Path, *, require_approval: bool = True) -> None:
        self.workspace = workspace
        self.require_approval = require_approval
        self._request_context: RequestContext | None = None

    def set_context(self, ctx: RequestContext) -> None:
        self._request_context = ctx

    @property
    def name(self) -> str:
        return "skill_manage"

    @property
    def description(self) -> str:
        return (
            "Create, edit, patch, delete, import from a raw GitHub SKILL.md URL, "
            "or add support files to workspace skills. "
            "Skills are procedural memory for recurring task types and load from "
            "`workspace/skills/<name>/SKILL.md`. By default, writes are staged for "
            "user approval; tell the user they can reply `批准` / `approve` or use `/approval`."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return tool_parameters_schema(
            action=StringSchema(
                "Action to perform",
                enum=["create", "edit", "patch", "delete", "write_file", "import_url"],
            ),
            name=StringSchema("Workspace skill directory name"),
            content=StringSchema("Full SKILL.md content for create/edit", nullable=True),
            source_url=StringSchema(
                "For import_url: GitHub blob URL or raw.githubusercontent.com URL ending in SKILL.md",
                nullable=True,
            ),
            file_path=StringSchema(
                "For patch/write_file: SKILL.md or a path under references/, templates/, scripts/, or assets/",
                nullable=True,
            ),
            file_content=StringSchema("Content for write_file", nullable=True),
            old_string=StringSchema("Exact text to replace for patch", nullable=True),
            new_string=StringSchema("Replacement text for patch", nullable=True),
            replace_all=BooleanSchema(description="Replace all patch matches", default=False),
            overwrite=BooleanSchema(description="For import_url: replace an existing skill", default=False),
            required=["action", "name"],
        )

    async def execute(
        self,
        action: str,
        name: str,
        content: str | None = None,
        file_path: str | None = None,
        file_content: str | None = None,
        source_url: str | None = None,
        old_string: str | None = None,
        new_string: str | None = None,
        replace_all: bool = False,
        overwrite: bool = False,
        **_kwargs: Any,
    ) -> str:
        payload = {
            "action": action,
            "name": name,
            "content": content,
            "source_url": source_url,
            "file_path": file_path,
            "file_content": file_content,
            "old_string": old_string,
            "new_string": new_string,
            "replace_all": replace_all,
            "overwrite": overwrite,
        }
        payload = {key: value for key, value in payload.items() if value is not None}

        if action == "import_url":
            prepared = await _build_import_url_payload(name, source_url, overwrite)
            if not prepared.get("success"):
                return _tool_result(prepared)
            payload = prepared["payload"]

        if not self.require_approval:
            return _tool_result(apply_skill_manage_payload(self.workspace, payload))

        ctx = self._request_context
        record = ApprovalStore(self.workspace).create(
            kind="skill_manage",
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
                f"Staged for approval as `{record['id']}`. "
                "The user can reply `批准` / `approve`, `拒绝` / `reject`, "
                "or run `/approval` to review pending items."
            ),
        })
