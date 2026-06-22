---
name: china-weather
description: Provide China weather, air quality, rain alerts, typhoon or severe weather checks, and weather-aware reminders using China-friendly weather sources.
---

# China Weather

Use this skill for weather in mainland China, Hong Kong, Macau, or Taiwan when the user asks
about conditions, forecasts, air quality, rain, typhoons, heat, cold, or whether to bring gear.

## Preferred Sources

- `china_life` tool first:
  - default `provider: "auto"` or `"public"` uses Open-Meteo, which does not require a key.
  - `provider: "qweather"` uses QWeather when `tools.chinaLife.qweatherKey` or `QWEATHER_KEY` is configured.
  - `provider: "amap"` uses AMap weather when `tools.chinaLife.amapKey` or `AMAP_KEY` is configured.
- Public web search as fallback.
- Built-in `weather` skill for quick non-China-specific checks.

Prefer free/no-registration sources first. Do not invent live weather or warnings. If no live
source is available, state that the answer is planning guidance rather than verified current
weather.

If the user gives a QWeather or AMap key in conversation, use `config_manage` to set the relevant
`tools.chinaLife.*Key`; wait for approval before writing it.

## Files

Store weather-sensitive preferences in `life/preferences.json`, such as:
Use `life_data` with `collection: "preferences"` for these preferences.

- umbrella threshold
- air-quality sensitivity
- preferred clothing guidance level
- commute weather reminders

Store scheduled weather checks in `life/reminders.json`.
Use `life_data` with `collection: "reminders"` for local reminder metadata.

## Workflow

1. Identify city/district and time window.
2. Fetch current conditions and forecast with `china_life` if available.
3. Give practical advice: umbrella, coat, mask, sunscreen, commute buffer, or plan change.
4. If the weather affects an event or trip, update `calendar` or `trips` through `life_data`.
5. If the user wants ongoing alerts, use `life-reminders`.

## Risk

Weather advice is informational. For emergencies, official local alerts and authorities take
priority. Do not claim certainty about dangerous conditions without a current official source.
