"""Agent core module."""

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "AgentHook": ".hook",
    "AgentHookContext": ".hook",
    "AgentRunHookContext": ".hook",
    "AgentLoop": ".loop",
    "CompositeHook": ".hook",
    "ContextBuilder": ".context",
    "MemoryStore": ".memory",
    "SkillsLoader": ".skills",
    "SubagentManager": ".subagent",
}


def __getattr__(name: str) -> Any:
    module_path = _LAZY_EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod = import_module(module_path, __name__)
    value = getattr(mod, name)
    globals()[name] = value
    return value


__all__ = [
    "AgentHook",
    "AgentHookContext",
    "AgentRunHookContext",
    "AgentLoop",
    "CompositeHook",
    "ContextBuilder",
    "MemoryStore",
    "SkillsLoader",
    "SubagentManager",
]
