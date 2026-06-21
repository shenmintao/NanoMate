---
name: china-smart-home
description: Coordinate smart-home notes, Home Assistant or Mi Home scenes, device reminders, and approval-gated home automation with strict safety boundaries.
---

# China Smart Home

Use this skill for Home Assistant, Mi Home, Aqara, smart lights, air conditioners, curtains,
plugs, sensors, robot vacuums, scenes, and household automation.

## Integration Preference

Prefer Home Assistant when available because it has clear entity ids and auditability. Mi Home
or vendor ecosystems may require unofficial or limited integrations; be explicit about limits.

## File

Store smart-home context in `life/smart-home.json` as an object:

- `locations`: rooms and labels.
- `devices`: entity id, display name, room, safe actions, risky actions.
- `scenes`: scene name, purpose, devices touched.
- `preferences`: temperature, lighting, quiet hours, cleaning windows.
- `safety_notes`: locks, cameras, alarms, gas, heating, medical devices.

## Workflow

1. Identify device, room, desired state, and timing.
2. Check whether a real integration/tool exists.
3. Save preferences or scene ideas locally when no integration exists.
4. Use `life-actions` before changing device state unless the user has explicitly configured that device/action as low risk.
5. Always require second confirmation for locks, cameras, alarms, gas, heat, high-power plugs, or safety-sensitive scenes.
6. Verify device response before claiming completion.

## Low-Risk Examples

Drafting a scene, saving a preferred temperature, or reminding the user to start a device is low
risk. Turning on a real device is an external action and may be risky.

## Companion Fusion

Companion warmth is useful for home routines, but do not let roleplay language obscure physical
safety. State exactly which device would change before approval.
