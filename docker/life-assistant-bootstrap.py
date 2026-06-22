"""Bootstrap a container-friendly NanoMate life-assistant config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from nanobot.config.loader import load_config, save_config
from nanobot.config.schema import Config

DEFAULT_CONFIG = "/home/nanobot/.nanobot/config.json"
DEFAULT_WORKSPACE = "/home/nanobot/.nanobot/workspace"

PROVIDER_ENV: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "anthropic": (("ANTHROPIC_API_KEY",), ("ANTHROPIC_API_BASE", "ANTHROPIC_BASE_URL")),
    "openai": (("OPENAI_API_KEY",), ("OPENAI_API_BASE", "OPENAI_BASE_URL")),
    "openrouter": (("OPENROUTER_API_KEY",), ("OPENROUTER_API_BASE", "OPENROUTER_BASE_URL")),
    "deepseek": (("DEEPSEEK_API_KEY",), ("DEEPSEEK_API_BASE", "DEEPSEEK_BASE_URL")),
    "dashscope": (("DASHSCOPE_API_KEY",), ("DASHSCOPE_API_BASE", "DASHSCOPE_BASE_URL")),
    "gemini": (("GEMINI_API_KEY",), ("GEMINI_API_BASE", "GEMINI_BASE_URL")),
    "moonshot": (("MOONSHOT_API_KEY",), ("MOONSHOT_API_BASE", "MOONSHOT_BASE_URL")),
    "zhipu": (("ZHIPUAI_API_KEY", "ZAI_API_KEY"), ("ZHIPU_API_BASE", "ZAI_API_BASE")),
    "siliconflow": (("SILICONFLOW_API_KEY",), ("SILICONFLOW_API_BASE",)),
    "aihubmix": (("AIHUBMIX_API_KEY",), ("AIHUBMIX_API_BASE",)),
    "volcengine": (("VOLCENGINE_API_KEY",), ("VOLCENGINE_API_BASE",)),
    "qianfan": (("QIANFAN_API_KEY",), ("QIANFAN_API_BASE",)),
}

DEFAULT_MODELS = {
    "anthropic": "anthropic/claude-opus-4-5",
    "openai": "gpt-4o-mini",
    "openrouter": "anthropic/claude-opus-4-5",
    "deepseek": "deepseek-chat",
    "dashscope": "qwen-plus",
    "gemini": "gemini-2.0-flash",
    "moonshot": "kimi-k2.5",
    "zhipu": "glm-4.5",
}


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _first_env(names: Iterable[str]) -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    return ""


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name).lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on", "enable", "enabled"}


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _choose_provider() -> str:
    explicit = _env("NANOMATE_PROVIDER")
    if explicit:
        return explicit
    for provider, (key_names, _base_names) in PROVIDER_ENV.items():
        if _first_env(key_names):
            return provider
    return "deepseek"


def _apply_provider_env(config: Config, provider: str) -> None:
    generic_key = _env("NANOMATE_PROVIDER_API_KEY")
    generic_base = _env("NANOMATE_PROVIDER_API_BASE") or _env("NANOMATE_PROVIDER_BASE_URL")
    for name, (key_names, base_names) in PROVIDER_ENV.items():
        provider_config = getattr(config.providers, name, None)
        if provider_config is None:
            continue
        api_key = generic_key if name == provider and generic_key else _first_env(key_names)
        api_base = generic_base if name == provider and generic_base else _first_env(base_names)
        if api_key:
            provider_config.api_key = api_key
        if api_base:
            provider_config.api_base = api_base


def _apply_life_service_env(config: Config) -> None:
    china = config.tools.china_life
    china.public_providers_enabled = _env_bool("NANOMATE_PUBLIC_PROVIDERS_ENABLED", True)
    if value := _first_env(("AMAP_KEY", "AMAP_API_KEY", "GAODE_API_KEY")):
        china.amap_key = value
    if value := _first_env(("QWEATHER_KEY", "QWEATHER_API_KEY")):
        china.qweather_key = value
    if value := _env("KUAIDI100_KEY"):
        china.kuaidi100_key = value
    if value := _env("KUAIDI100_CUSTOMER"):
        china.kuaidi100_customer = value

    search = config.tools.web.search
    if value := _env("NANOMATE_WEB_SEARCH_PROVIDER"):
        search.provider = value
    if value := _env("NANOMATE_WEB_SEARCH_API_KEY"):
        search.api_key = value
    if value := _env("NANOMATE_WEB_SEARCH_BASE_URL"):
        search.base_url = value


def _enable_life_tools(config: Config) -> None:
    config.tools.config_manage.enable = True
    config.tools.config_manage.require_approval = True
    config.tools.life_data.enable = True
    config.tools.life_action.enable = True
    config.tools.life_action.require_approval = True
    config.tools.skill_manage.enable = True
    config.tools.skill_manage.require_approval = True
    config.tools.skill_curator.enable = True
    config.tools.skill_curator.require_approval = True
    config.tools.china_life.enable = True
    config.tools.web.enable = True


def bootstrap() -> Path:
    config_path = Path(_env("NANOMATE_CONFIG") or DEFAULT_CONFIG).expanduser()
    workspace = _env("NANOMATE_WORKSPACE") or DEFAULT_WORKSPACE
    config_path.parent.mkdir(parents=True, exist_ok=True)
    Path(workspace).expanduser().mkdir(parents=True, exist_ok=True)

    config = load_config(config_path) if config_path.exists() else Config()
    provider = _choose_provider()

    config.agents.defaults.workspace = workspace
    config.agents.defaults.provider = provider
    config.agents.defaults.model = _env("NANOMATE_MODEL") or DEFAULT_MODELS.get(
        provider,
        config.agents.defaults.model,
    )
    config.agents.defaults.timezone = _env("NANOMATE_TIMEZONE") or _env("TZ") or "Asia/Shanghai"
    config.agents.defaults.bot_name = _env("NANOMATE_BOT_NAME") or "NanoMate"
    config.agents.defaults.unified_session = _env_bool("NANOMATE_UNIFIED_SESSION", True)

    config.gateway.host = _env("NANOMATE_GATEWAY_HOST") or "0.0.0.0"
    config.gateway.port = _env_int("NANOMATE_GATEWAY_PORT", 18790)
    config.api.host = _env("NANOMATE_API_HOST") or "0.0.0.0"
    config.api.port = _env_int("NANOMATE_API_PORT", 8900)
    config.tools.restrict_to_workspace = _env_bool("NANOMATE_RESTRICT_TO_WORKSPACE", True)
    config.sillytavern.enabled = _env_bool("NANOMATE_SILLYTAVERN_ENABLED", config.sillytavern.enabled)

    _enable_life_tools(config)
    _apply_provider_env(config, provider)
    _apply_life_service_env(config)

    save_config(config, config_path)
    print(f"[life-assistant] config ready: {config_path}")
    print(f"[life-assistant] workspace ready: {workspace}")
    print(f"[life-assistant] provider/model: {config.agents.defaults.provider}/{config.agents.defaults.model}")
    return config_path


if __name__ == "__main__":
    bootstrap()
