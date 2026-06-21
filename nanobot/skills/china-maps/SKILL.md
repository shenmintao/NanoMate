---
name: china-maps
description: Handle China map, commute, route planning, geocoding, nearby places, navigation, and location-aware errands with AMap or Baidu Maps integrations.
---

# China Maps

Use this skill for China location tasks: route planning, commute checks, nearby POI search,
geocoding, address cleanup, meeting location choice, errands by area, and navigation handoff.

## Preferred Integrations

- AMap MCP server or AMap Web Service API when available.
- Baidu Maps Web API when AMap is unavailable or the user's data is already there.
- Generic web search only as a fallback for public place information.

Do not require an API key for simple planning if web search is enough. Do not fabricate live
traffic, opening hours, or route times.

## Files

Store reusable location context in `life/preferences.json`:

- home/work/school labels, never full address unless the user explicitly wants it stored
- preferred transport modes
- commute windows
- walking tolerance, accessibility needs, and parking preferences

Store location-based errands in `life/tasks.json` with `context: "errand"` and optional
`location`.

## Workflow

1. Clarify origin, destination, date/time, and transport mode only when missing data changes the answer.
2. Use an available map/search integration for route, POI, or distance data.
3. Summarize 1-3 practical options with tradeoffs.
4. Save decisions to `life/calendar.json`, `life/tasks.json`, or `life/preferences.json` when the user asks or when it is clearly durable.
5. Use `life-actions` before booking, paying, calling, messaging, or changing an external account.

## Companion Fusion

When Companion Mode is active, present route help in the companion's voice while keeping factual
times, prices, and risks plain. Do not turn a caring check-in into an unsolicited navigation task.
