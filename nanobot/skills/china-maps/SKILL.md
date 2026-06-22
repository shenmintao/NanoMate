---
name: china-maps
description: Handle China map, commute, route planning, geocoding, nearby places, navigation, and location-aware errands with AMap or Baidu Maps integrations.
---

# China Maps

Use this skill for China location tasks: route planning, commute checks, nearby POI search,
geocoding, address cleanup, meeting location choice, errands by area, and navigation handoff.

## Preferred Integrations

- `china_life` tool first:
  - default `provider: "auto"` or `"public"` uses Nominatim + OSRM public APIs, which do not require a key.
  - `provider: "amap"` uses AMap Web Service API when `tools.chinaLife.amapKey` or `AMAP_KEY` is configured.
- AMap MCP server when available.
- Baidu Maps Web API when AMap is unavailable or the user's data is already there.
- Generic web search only as a fallback for public place information.

Prefer free/no-registration sources for low-risk planning. Do not require an API key for simple
planning if public providers or web search are enough. Do not fabricate live traffic, opening
hours, or route times.

If the user gives an AMap key in conversation, use `config_manage` to set
`tools.chinaLife.amapKey`; wait for approval before writing it.

## Files

Store reusable location context in `life/preferences.json`:
Use `life_data` with `collection: "preferences"` for reusable location preferences.

- home/work/school labels, never full address unless the user explicitly wants it stored
- preferred transport modes
- commute windows
- walking tolerance, accessibility needs, and parking preferences

Store location-based errands in `life/tasks.json` with `context: "errand"` and optional
`location`.
Use `life_data` with `collection: "tasks"` for errands.

## Workflow

1. Clarify origin, destination, date/time, and transport mode only when missing data changes the answer.
2. Use `china_life` for route, POI, geocoding, or distance data when available.
3. Summarize 1-3 practical options with tradeoffs.
4. Save durable decisions with `life_data` to `calendar`, `tasks`, or `preferences` when the user asks or when clearly durable.
5. Use `life-actions` before booking, paying, calling, messaging, or changing an external account.

## Companion Fusion

When Companion Mode is active, present route help in the companion's voice while keeping factual
times, prices, and risks plain. Do not turn a caring check-in into an unsolicited navigation task.
