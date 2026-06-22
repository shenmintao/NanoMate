from __future__ import annotations

import importlib.util
from pathlib import Path

from nanobot.config.loader import load_config


def _load_bootstrap_module(repo_root: Path):
    module_path = repo_root / "docker" / "life-assistant-bootstrap.py"
    spec = importlib.util.spec_from_file_location("life_assistant_bootstrap", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_life_assistant_bootstrap_writes_container_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    module = _load_bootstrap_module(repo_root)
    config_path = tmp_path / "config.json"
    workspace = tmp_path / "workspace"

    monkeypatch.setenv("NANOMATE_CONFIG", str(config_path))
    monkeypatch.setenv("NANOMATE_WORKSPACE", str(workspace))
    monkeypatch.setenv("NANOMATE_PROVIDER", "deepseek")
    monkeypatch.setenv("NANOMATE_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("AMAP_KEY", "amap-test-key")
    monkeypatch.setenv("NANOMATE_WEB_SEARCH_PROVIDER", "duckduckgo")
    monkeypatch.setenv("TZ", "Asia/Shanghai")

    written = module.bootstrap()

    assert written == config_path
    config = load_config(config_path)
    assert config.agents.defaults.workspace == str(workspace)
    assert config.agents.defaults.provider == "deepseek"
    assert config.agents.defaults.model == "deepseek-chat"
    assert config.agents.defaults.timezone == "Asia/Shanghai"
    assert config.agents.defaults.unified_session is True
    assert config.gateway.host == "0.0.0.0"
    assert config.gateway.port == 18790
    assert config.api.host == "0.0.0.0"
    assert config.providers.deepseek.api_key == "deepseek-test-key"
    assert config.tools.china_life.enable is True
    assert config.tools.china_life.public_providers_enabled is True
    assert config.tools.china_life.amap_key == "amap-test-key"
    assert config.tools.life_data.enable is True
    assert config.tools.life_action.require_approval is True
    assert config.tools.config_manage.require_approval is True
    assert config.tools.skill_manage.require_approval is True
    assert config.tools.skill_curator.require_approval is True
    assert config.tools.restrict_to_workspace is True
