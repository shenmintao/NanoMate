from __future__ import annotations

import importlib
import sys
from pathlib import Path

from nanobot.agent.skills import BUILTIN_SKILLS_DIR, SkillsLoader


SCRIPT_DIR = Path("nanobot/skills/skill-creator/scripts").resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

quick_validate = importlib.import_module("quick_validate")

LIFE_ASSISTANT_SKILLS = {
    "life-actions",
    "life-calendar",
    "life-companion-bridge",
    "life-documents",
    "life-goals",
    "life-journal",
    "life-ledger",
    "life-manager",
    "life-people",
    "life-preferences",
    "life-reminders",
    "life-review",
    "life-subscriptions",
    "life-tasks",
    "china-express",
    "china-health",
    "china-local-services",
    "china-maps",
    "china-office",
    "china-shopping",
    "china-smart-home",
    "china-travel",
    "china-weather",
}


def test_life_assistant_skill_suite_is_complete_and_valid() -> None:
    loader = SkillsLoader(Path(".unused-test-workspace"), builtin_skills_dir=BUILTIN_SKILLS_DIR)
    available = {entry["name"] for entry in loader.list_skills(filter_unavailable=False)}
    readme = (BUILTIN_SKILLS_DIR / "README.md").read_text(encoding="utf-8")

    assert LIFE_ASSISTANT_SKILLS <= available

    for name in sorted(LIFE_ASSISTANT_SKILLS):
        valid, message = quick_validate.validate_skill(BUILTIN_SKILLS_DIR / name)
        assert valid, f"{name}: {message}"
        assert f"`{name}`" in readme


def test_only_life_coordinators_are_always_on() -> None:
    loader = SkillsLoader(Path(".unused-test-workspace"), builtin_skills_dir=BUILTIN_SKILLS_DIR)
    always = set(loader.get_always_skills())
    expected = {"life-manager", "life-companion-bridge"}

    assert expected <= always
    assert not ((LIFE_ASSISTANT_SKILLS - expected) & always)


def test_life_companion_bridge_preserves_companion_templates() -> None:
    bridge = (BUILTIN_SKILLS_DIR / "life-companion-bridge" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    manager = (BUILTIN_SKILLS_DIR / "life-manager" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    for content in (bridge, manager):
        assert "nanobot/templates/skills/living-together" in content
        assert "nanobot/templates/skills/emotional-companion" in content
        assert "Do not edit" in content or "Do not modify" in content

    assert "Feel" in bridge
    assert "Remember" in bridge
    assert "Plan" in bridge
    assert "Ask" in bridge
    assert "Reflect" in bridge
