---
name: china-weather
description: Provide China weather, air quality, rain alerts, typhoon or severe weather checks, and weather-aware reminders using China-friendly weather sources.
---

# China Weather

Use this skill for weather in mainland China, Hong Kong, Macau, or Taiwan when the user asks
about conditions, forecasts, air quality, rain, typhoons, heat, cold, or whether to bring gear.

## Preferred Sources

- HeWeather/QWeather API when configured.
- AMap weather API when an AMap key or MCP server is available.
- Public web search as fallback.
- Built-in `weather` skill for quick non-China-specific checks.

Do not invent live weather or warnings. If no live source is available, state that the answer is
planning guidance rather than verified current weather.

## Files

Store weather-sensitive preferences in `life/preferences.json`, such as:

- umbrella threshold
- air-quality sensitivity
- preferred clothing guidance level
- commute weather reminders

Store scheduled weather checks in `life/reminders.json`.

## Workflow

1. Identify city/district and time window.
2. Fetch or search current conditions and forecast if a live source is available.
3. Give practical advice: umbrella, coat, mask, sunscreen, commute buffer, or plan change.
4. If the weather affects an event or trip, update `life/calendar.json` or `life/trips.json`.
5. If the user wants ongoing alerts, use `life-reminders`.

## Risk

Weather advice is informational. For emergencies, official local alerts and authorities take
priority. Do not claim certainty about dangerous conditions without a current official source.
