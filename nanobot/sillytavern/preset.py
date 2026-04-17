"""Preset parser — prompt entry management and macro substitution."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from nanobot.sillytavern.types import PresetPromptEntry, SillyTavernPreset, MacrosConfig


def parse_preset(json_string: str) -> tuple[SillyTavernPreset | None, str | None]:
    """Parse a preset JSON string.

    Returns:
        Tuple of (preset, error).
    """
    try:
        obj = json.loads(json_string)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

    return parse_preset_object(obj)


def parse_preset_object(obj: Any) -> tuple[SillyTavernPreset | None, str | None]:
    """Parse a preset from a dict."""
    if not isinstance(obj, dict):
        return None, "Input is not an object"

    prompts_raw = obj.get("prompts", obj.get("prompt_order", []))

    prompts: list[PresetPromptEntry] = []
    if isinstance(prompts_raw, list):
        for entry in prompts_raw:
            if not isinstance(entry, dict):
                continue
            prompts.append(_parse_prompt_entry(entry))

    # Apply prompt_order overrides (enabled state and ordering).
    # SillyTavern stores per-entry enabled state and ordering in prompt_order
    # separately from the prompts array. The prompt_order takes precedence.
    prompts = _apply_prompt_order_overrides(prompts, obj.get("prompt_order", []))

    preset = SillyTavernPreset(
        temperature=float(obj.get("temperature", 1.0)),
        frequency_penalty=float(obj.get("frequency_penalty", 0.0)),
        presence_penalty=float(obj.get("presence_penalty", 0.0)),
        top_p=float(obj.get("top_p", 1.0)),
        top_k=int(obj.get("top_k", 0)),
        prompts=prompts,
    )

    return preset, None


def _apply_prompt_order_overrides(
    prompts: list[PresetPromptEntry],
    prompt_order_raw: list[Any],
) -> list[PresetPromptEntry]:
    """Apply enabled and ordering overrides from prompt_order to parsed prompts.

    SillyTavern presets have a prompt_order array where each entry contains
    a character_id and an order list with per-identifier enabled states and
    ordering. These override the enabled field and order in the prompts array.
    """
    if not isinstance(prompt_order_raw, list):
        return prompts

    # Build a lookup from identifier to prompt entry
    by_id: dict[str, PresetPromptEntry] = {}
    for p in prompts:
        if p.identifier:
            by_id[p.identifier] = p

    # Find the last prompt_order entry (last one wins)
    last_order: list[dict] | None = None
    for po in prompt_order_raw:
        if not isinstance(po, dict):
            continue
        order = po.get("order")
        if isinstance(order, list):
            last_order = order

    if last_order is None:
        return prompts

    # Apply enabled overrides and reorder
    ordered: list[PresetPromptEntry] = []
    seen: set[str] = set()
    for item in last_order:
        if not isinstance(item, dict):
            continue
        ident = item.get("identifier", "")
        if not ident or ident not in by_id:
            continue
        entry = by_id[ident]
        if "enabled" in item:
            entry.enabled = bool(item["enabled"])
        if ident not in seen:
            ordered.append(entry)
            seen.add(ident)

    # Append any prompts not referenced in prompt_order
    for p in prompts:
        if p.identifier and p.identifier not in seen:
            ordered.append(p)
            seen.add(p.identifier)
        elif not p.identifier:
            ordered.append(p)

    return ordered


def _parse_prompt_entry(d: dict) -> PresetPromptEntry:
    """Parse a single prompt entry from a dict."""
    return PresetPromptEntry(
        identifier=str(d.get("identifier", "")),
        name=str(d.get("name", d.get("identifier", ""))),
        enabled=d.get("enabled", True),
        role=str(d.get("role", "system")),
        content=str(d.get("content", "")),
        injection_position=d.get("injection_position", d.get("injectionPosition", 0)),
        injection_depth=d.get("injection_depth", d.get("injectionDepth", 4)),
        injection_order=d.get("injection_order", d.get("order", 100)),
        system_prompt=d.get("system_prompt", d.get("systemPrompt", False)),
        marker=d.get("marker", False),
    )


def get_enabled_prompts(preset: SillyTavernPreset) -> list[PresetPromptEntry]:
    """Get all enabled, non-marker prompts with content."""
    return [
        p for p in preset.prompts
        if p.enabled and not p.marker and p.content.strip()
    ]


def build_preset_prompt(
    prompts: list[PresetPromptEntry],
    *,
    position: int | None = None,
) -> str:
    """Build a system prompt from preset prompt entries.

    Args:
        prompts: Preset prompt entries.
        position: If provided, only include entries at this injection position.
    """
    filtered = prompts
    if position is not None:
        filtered = [p for p in prompts if p.injection_position == position]

    # Sort by injection order
    filtered.sort(key=lambda p: p.injection_order)

    parts = [p.content.strip() for p in filtered if p.content.strip()]
    return "\n\n".join(parts)


# ============================================================================
# Macro Substitution
# ============================================================================

DEFAULT_MACROS = {
    "user": "User",
    "char": "Assistant",
}


def apply_macros(
    content: str,
    macros: MacrosConfig | None = None,
    custom_variables: dict[str, str] | None = None,
) -> str:
    """Apply macro substitutions to content.

    Replaces patterns like {{user}}, {{char}}, {{date}}, {{time}}, etc.
    """
    if not content:
        return content

    cfg = macros or MacrosConfig()
    now = datetime.now()

    replacements: dict[str, str] = {
        "user": cfg.user,
        "char": cfg.char,
        "date": now.strftime(_format_to_strftime(cfg.date_format)),
        "time": now.strftime(_format_to_strftime(cfg.time_format)),
        "weekday": now.strftime("%A"),
        "month": now.strftime("%B"),
        "year": str(now.year),
        "isotime": now.isoformat(),
        "idle_duration": "",
        "random": str(hash(now) % 1000),
        "roll": str((hash(now) % 20) + 1),  # d20 roll
        "// ": "",  # comment macro (removed)
    }

    # Add custom variables
    if cfg.custom_variables:
        replacements.update(cfg.custom_variables)
    if custom_variables:
        replacements.update(custom_variables)

    result = content
    for key, value in replacements.items():
        result = result.replace("{{" + key + "}}", value)

    return result


def _format_to_strftime(fmt: str) -> str:
    """Convert SillyTavern date/time format to strftime format."""
    mapping = {
        "YYYY": "%Y",
        "YY": "%y",
        "MM": "%m",
        "DD": "%d",
        "HH": "%H",
        "hh": "%I",
        "mm": "%M",
        "ss": "%S",
        "A": "%p",
    }
    result = fmt
    for src, dst in mapping.items():
        result = result.replace(src, dst)
    return result


def summarize_preset(preset: SillyTavernPreset) -> str:
    """Build a human-readable summary of a preset."""
    total = len(preset.prompts)
    enabled = len(get_enabled_prompts(preset))
    return f"{total} prompts ({enabled} enabled), temp={preset.temperature}"
