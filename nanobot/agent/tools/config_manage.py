"""Approval-gated configuration updates from chat."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nanobot.agent.approvals import ApprovalStore
from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.context import ContextAware, RequestContext
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema
from nanobot.config_base import Base


class ConfigManageToolConfig(Base):
    """Configuration for agent-managed config writes."""

    enable: bool = True
    require_approval: bool = True


@dataclass(frozen=True)
class _AllowedConfigPath:
    attr_path: tuple[str, ...]
    value_type: str = "secret"
    description: str = ""


_PROVIDER_KEYS = {
    "anthropic",
    "openai",
    "openrouter",
    "custom",
    "azure_openai",
    "huggingface",
    "skywork",
    "deepseek",
    "groq",
    "zhipu",
    "dashscope",
    "vllm",
    "gemini",
    "moonshot",
    "minimax",
    "mistral",
    "stepfun",
    "xiaomi_mimo",
    "longcat",
    "ant_ling",
    "aihubmix",
    "siliconflow",
    "novita",
    "volcengine",
    "qianfan",
    "nvidia",
}


_ALLOWED_PATHS: dict[str, _AllowedConfigPath] = {
    "tools.chinaLife.amapKey": _AllowedConfigPath(
        ("tools", "china_life", "amap_key"),
        "secret",
        "AMap Web Service key",
    ),
    "tools.chinaLife.qweatherKey": _AllowedConfigPath(
        ("tools", "china_life", "qweather_key"),
        "secret",
        "QWeather API key",
    ),
    "tools.chinaLife.kuaidi100Key": _AllowedConfigPath(
        ("tools", "china_life", "kuaidi100_key"),
        "secret",
        "Kuaidi100 key",
    ),
    "tools.chinaLife.kuaidi100Customer": _AllowedConfigPath(
        ("tools", "china_life", "kuaidi100_customer"),
        "secret",
        "Kuaidi100 customer id",
    ),
    "tools.chinaLife.publicProvidersEnabled": _AllowedConfigPath(
        ("tools", "china_life", "public_providers_enabled"),
        "bool",
        "Allow free no-registration public providers",
    ),
    "tools.web.search.provider": _AllowedConfigPath(
        ("tools", "web", "search", "provider"),
        "string",
        "Web search provider",
    ),
    "tools.web.search.apiKey": _AllowedConfigPath(
        ("tools", "web", "search", "api_key"),
        "secret",
        "Web search provider API key",
    ),
    "tools.web.search.baseUrl": _AllowedConfigPath(
        ("tools", "web", "search", "base_url"),
        "string",
        "Web search provider base URL",
    ),
}

for _provider in _PROVIDER_KEYS:
    _ALLOWED_PATHS[f"providers.{_provider}.apiKey"] = _AllowedConfigPath(
        ("providers", _provider, "api_key"),
        "secret",
        f"{_provider} provider API key",
    )
    _ALLOWED_PATHS[f"providers.{_provider}.apiBase"] = _AllowedConfigPath(
        ("providers", _provider, "api_base"),
        "string",
        f"{_provider} provider API base URL",
    )


def _tool_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _mask_value(value: str) -> str:
    if not value:
        return "<empty>"
    if value.startswith("${") and value.endswith("}"):
        return value
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:2]}{'*' * max(4, len(value) - 6)}{value[-4:]}"


def _cast_value(raw: str, value_type: str) -> Any:
    if value_type in {"secret", "string"}:
        return str(raw)
    if value_type == "bool":
        lowered = str(raw).strip().lower()
        if lowered in {"1", "true", "yes", "y", "on", "enable", "enabled"}:
            return True
        if lowered in {"0", "false", "no", "n", "off", "disable", "disabled"}:
            return False
        raise ValueError("value must be a boolean-like string")
    raise ValueError(f"Unsupported config value type: {value_type}")


def _get_target(config: Any, attr_path: tuple[str, ...]) -> tuple[Any, str]:
    target = config
    for attr in attr_path[:-1]:
        target = getattr(target, attr)
    return target, attr_path[-1]


def _summary_for(payload: dict[str, Any]) -> str:
    path = str(payload.get("path") or "")
    allowed = _ALLOWED_PATHS.get(path)
    raw_value = str(payload.get("value") or "")
    shown = _mask_value(raw_value) if allowed and allowed.value_type == "secret" else raw_value
    return f"Set config `{path}` to `{shown}`."


def allowed_config_paths() -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "type": spec.value_type,
            "description": spec.description,
        }
        for path, spec in sorted(_ALLOWED_PATHS.items())
    ]


def apply_config_manage_payload(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "set").strip().lower()
    if action == "list_allowed":
        return {"success": True, "allowed": allowed_config_paths()}
    if action != "set":
        return {"success": False, "error": f"Unknown config_manage action '{action}'."}

    path = str(payload.get("path") or "").strip()
    if path not in _ALLOWED_PATHS:
        return {
            "success": False,
            "error": f"Config path '{path}' is not allowed for chat-based updates.",
            "allowed": allowed_config_paths(),
        }
    value = str(payload.get("value") or "")
    spec = _ALLOWED_PATHS[path]
    try:
        casted = _cast_value(value, spec.value_type)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    from nanobot.config.loader import load_config, save_config

    config = load_config()
    target, attr = _get_target(config, spec.attr_path)
    setattr(target, attr, casted)
    save_config(config)

    shown = _mask_value(value) if spec.value_type == "secret" else str(casted)
    return {
        "success": True,
        "message": f"Updated `{path}` to `{shown}`.",
        "path": path,
    }


class ConfigManageTool(Tool, ContextAware):
    """Update a strict allowlist of config settings, normally via approval."""

    config_key = "config_manage"

    @classmethod
    def config_cls(cls):
        return ConfigManageToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        return ctx.config.config_manage.enable

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(
            workspace=Path(ctx.workspace),
            require_approval=ctx.config.config_manage.require_approval,
        )

    def __init__(self, workspace: Path | str, *, require_approval: bool = True) -> None:
        self.workspace = Path(workspace)
        self.require_approval = require_approval
        self._request_context: RequestContext | None = None

    def set_context(self, ctx: RequestContext) -> None:
        self._request_context = ctx

    @property
    def name(self) -> str:
        return "config_manage"

    @property
    def description(self) -> str:
        return (
            "List or update a strict allowlist of NanoMate config keys from chat. "
            "Use this when the user asks to configure API keys or service settings. "
            "By default, changes are staged for user approval and secret values are masked in replies."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return tool_parameters_schema(
            action=StringSchema("Action", enum=["list_allowed", "set"]),
            path=StringSchema("Allowed config path such as tools.chinaLife.amapKey", nullable=True),
            value=StringSchema("New value. Secrets will be masked in tool output.", nullable=True),
            required=["action"],
        )

    async def execute(
        self,
        action: str,
        path: str | None = None,
        value: str | None = None,
        **_kwargs: Any,
    ) -> str:
        action = action.strip().lower()
        if action == "list_allowed":
            return _tool_result({"success": True, "allowed": allowed_config_paths()})
        if action != "set":
            return _tool_result({"success": False, "error": f"Unknown action '{action}'."})
        if not path:
            return _tool_result({"success": False, "error": "path is required for set."})
        if path not in _ALLOWED_PATHS:
            return _tool_result({
                "success": False,
                "error": f"Config path '{path}' is not allowed for chat-based updates.",
                "allowed": allowed_config_paths(),
            })
        if value is None:
            return _tool_result({"success": False, "error": "value is required for set."})

        payload = {"action": "set", "path": path, "value": value}
        if not self.require_approval:
            return _tool_result(apply_config_manage_payload(payload))

        ctx = self._request_context
        record = ApprovalStore(self.workspace).create(
            kind="config_manage",
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
                f"Staged config update as `{record['id']}`. "
                "The user can reply `批准` / `approve`, `拒绝` / `reject`, "
                "or run `/approval` to review pending items."
            ),
        })
