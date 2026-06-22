"""China-friendly life service lookups.

The default providers intentionally prefer public, no-registration APIs. Keyed
China-local providers remain available as opt-in upgrades for better coverage.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx
from pydantic import Field

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import (
    BooleanSchema,
    IntegerSchema,
    NumberSchema,
    StringSchema,
    tool_parameters_schema,
)
from nanobot.config_base import Base

_OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
_NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
_OSRM_BASE_URL = "https://router.project-osrm.org"
_AMAP_BASE_URL = "https://restapi.amap.com"
_QWEATHER_GEO_BASE_URL = "https://geoapi.qweather.com"
_QWEATHER_API_BASE_URL = "https://devapi.qweather.com"
_KUAIDI100_QUERY_URL = "https://poll.kuaidi100.com/poll/query.do"
_DEFAULT_USER_AGENT = "nanobot-life-assistant/0.1 (https://github.com/HKUDS/nanobot)"


class ChinaLifeToolConfig(Base):
    """Configuration for China life service lookup tool."""

    enable: bool = True
    public_providers_enabled: bool = True
    proxy: str | None = None
    user_agent: str = _DEFAULT_USER_AGENT
    timeout: float = 15.0

    amap_key: str = Field(default="", repr=False)
    qweather_key: str = Field(default="", repr=False)
    qweather_geo_base_url: str = _QWEATHER_GEO_BASE_URL
    qweather_api_base_url: str = _QWEATHER_API_BASE_URL
    kuaidi100_key: str = Field(default="", repr=False)
    kuaidi100_customer: str = Field(default="", repr=False)
    kuaidi100_query_url: str = _KUAIDI100_QUERY_URL


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _compact(v) for k, v in value.items() if v not in (None, "", [], {})}
    if isinstance(value, list):
        return [_compact(v) for v in value]
    return value


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _split_lat_lon(value: str) -> tuple[float, float] | None:
    parts = [part.strip() for part in value.replace("，", ",").split(",")]
    if len(parts) != 2:
        return None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None


def _split_lng_lat(value: str) -> tuple[float, float] | None:
    parsed = _split_lat_lon(value)
    if parsed is None:
        return None
    first, second = parsed
    return second, first


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


@tool_parameters(
    tool_parameters_schema(
        operation=StringSchema(
            "Lookup type",
            enum=[
                "geocode",
                "reverse_geocode",
                "poi_search",
                "route",
                "weather",
                "express_track",
            ],
        ),
        provider=StringSchema(
            "Provider: auto prefers free/no-registration public APIs; amap/qweather/kuaidi100 require configured keys",
            enum=["auto", "public", "amap", "qweather", "kuaidi100"],
        ),
        query=StringSchema("City, address, place, or POI query"),
        city=StringSchema("Optional city name or adcode to narrow results"),
        latitude=NumberSchema(description="Latitude for reverse geocode/weather/route"),
        longitude=NumberSchema(description="Longitude for reverse geocode/weather/route"),
        origin=StringSchema("Route origin as address or 'lat,lon'"),
        destination=StringSchema("Route destination as address or 'lat,lon'"),
        profile=StringSchema(
            "Route profile",
            enum=["driving", "walking", "cycling"],
        ),
        days=IntegerSchema(3, description="Forecast days", minimum=1, maximum=16),
        limit=IntegerSchema(5, description="Maximum search results", minimum=1, maximum=10),
        airQuality=BooleanSchema(description="Include public air-quality lookup when available"),
        trackingNumber=StringSchema("Express tracking number"),
        carrier=StringSchema("Courier code for configured express providers, such as shunfeng, jd, zto, yto, ems"),
        phone=StringSchema("Optional phone suffix required by some carriers"),
        required=["operation"],
    )
)
class ChinaLifeTool(Tool):
    """Look up life-service data with China-friendly defaults."""

    name = "china_life"
    description = (
        "China life-service lookup tool. Supports geocode, reverse_geocode, poi_search, "
        "route, weather, and express_track. Defaults to free/no-registration public "
        "providers where possible; AMap, QWeather, and Kuaidi100 are opt-in when keys "
        "are configured. Read-only: never books, pays, orders, messages, or changes accounts."
    )
    config_key = "china_life"
    _scopes = {"core", "subagent"}

    @classmethod
    def config_cls(cls):
        return ChinaLifeToolConfig

    @classmethod
    def enabled(cls, ctx: Any) -> bool:
        config = getattr(ctx.config, "china_life", None)
        if config is None:
            return True
        return bool(getattr(config, "enable", True))

    @classmethod
    def create(cls, ctx: Any) -> Tool:
        return cls(getattr(ctx.config, "china_life", None))

    def __init__(self, config: ChinaLifeToolConfig | None = None):
        self.config = config if isinstance(config, ChinaLifeToolConfig) else ChinaLifeToolConfig()

    @property
    def read_only(self) -> bool:
        return True

    async def execute(
        self,
        operation: str,
        provider: str = "auto",
        query: str | None = None,
        city: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        origin: str | None = None,
        destination: str | None = None,
        profile: str = "driving",
        days: int = 3,
        limit: int = 5,
        tracking_number: str | None = None,
        carrier: str | None = None,
        phone: str | None = None,
        air_quality: bool = False,
        **kwargs: Any,
    ) -> str:
        provider = (provider or "auto").strip().lower()
        operation = operation.strip().lower()
        query = query or kwargs.get("keywords")
        tracking_number = tracking_number or kwargs.get("trackingNumber")
        air_quality = _truthy(kwargs.get("airQuality", air_quality))

        try:
            if operation == "geocode":
                return await self._geocode(query=query, city=city, provider=provider, limit=limit)
            if operation == "reverse_geocode":
                return await self._reverse_geocode(latitude=latitude, longitude=longitude, provider=provider)
            if operation == "poi_search":
                return await self._poi_search(query=query, city=city, provider=provider, limit=limit)
            if operation == "route":
                return await self._route(
                    origin=origin,
                    destination=destination,
                    profile=profile,
                    provider=provider,
                    city=city,
                )
            if operation == "weather":
                return await self._weather(
                    query=query,
                    city=city,
                    latitude=latitude,
                    longitude=longitude,
                    provider=provider,
                    days=days,
                    air_quality=air_quality,
                )
            if operation == "express_track":
                return await self._express_track(
                    tracking_number=tracking_number,
                    carrier=carrier,
                    phone=phone,
                    provider=provider,
                )
            return _json({"success": False, "error": f"Unsupported operation: {operation}"})
        except httpx.HTTPStatusError as exc:
            return _json({
                "success": False,
                "error": f"HTTP {exc.response.status_code}: {exc.response.text[:300]}",
                "provider": provider,
                "operation": operation,
            })
        except Exception as exc:
            return _json({
                "success": False,
                "error": f"{type(exc).__name__}: {exc}",
                "provider": provider,
                "operation": operation,
            })

    async def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        request_headers = {"User-Agent": self.config.user_agent or _DEFAULT_USER_AGENT}
        if headers:
            request_headers.update(headers)
        async with httpx.AsyncClient(proxy=self.config.proxy, timeout=self.config.timeout) as client:
            response = await client.get(url, params=_compact(params or {}), headers=request_headers)
            response.raise_for_status()
            return response.json()

    async def _post_form_json(
        self,
        url: str,
        *,
        data: dict[str, Any],
    ) -> dict[str, Any] | list[Any]:
        async with httpx.AsyncClient(proxy=self.config.proxy, timeout=self.config.timeout) as client:
            response = await client.post(
                url,
                data=data,
                headers={"User-Agent": self.config.user_agent or _DEFAULT_USER_AGENT},
            )
            response.raise_for_status()
            return response.json()

    def _public_allowed(self) -> str | None:
        if self.config.public_providers_enabled:
            return None
        return _json({
            "success": False,
            "error": "Public no-registration providers are disabled by tools.chinaLife.publicProvidersEnabled=false.",
            "required": ["configure amapKey/qweatherKey or enable publicProvidersEnabled"],
        })

    def _amap_key(self) -> str:
        return self.config.amap_key or _env("AMAP_KEY")

    def _qweather_key(self) -> str:
        return self.config.qweather_key or _env("QWEATHER_KEY")

    def _kuaidi100_key(self) -> str:
        return self.config.kuaidi100_key or _env("KUAIDI100_KEY")

    def _kuaidi100_customer(self) -> str:
        return self.config.kuaidi100_customer or _env("KUAIDI100_CUSTOMER")

    async def _geocode(
        self,
        *,
        query: str | None,
        city: str | None,
        provider: str,
        limit: int,
    ) -> str:
        if not query:
            return _json({"success": False, "error": "query is required for geocode"})
        if provider == "amap":
            return await self._amap_geocode(query, city=city)
        if error := self._public_allowed():
            return error
        data = await self._nominatim_search(query, city=city, limit=limit)
        return _json({
            "success": True,
            "provider": "nominatim",
            "sourceType": "public-no-registration",
            "privacyNote": "Query was sent to the public OpenStreetMap Nominatim service.",
            "results": [
                {
                    "name": item.get("display_name"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "type": item.get("type"),
                    "class": item.get("class"),
                    "address": item.get("address"),
                }
                for item in data
                if isinstance(item, dict)
            ],
        })

    async def _reverse_geocode(
        self,
        *,
        latitude: float | None,
        longitude: float | None,
        provider: str,
    ) -> str:
        if latitude is None or longitude is None:
            return _json({"success": False, "error": "latitude and longitude are required"})
        if provider == "amap":
            return await self._amap_regeocode(latitude, longitude)
        if error := self._public_allowed():
            return error
        data = await self._get_json(
            f"{_NOMINATIM_BASE_URL}/reverse",
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
                "accept-language": "zh-CN,zh,en",
            },
        )
        return _json({
            "success": True,
            "provider": "nominatim",
            "sourceType": "public-no-registration",
            "privacyNote": "Coordinates were sent to the public OpenStreetMap Nominatim service.",
            "result": data,
        })

    async def _poi_search(
        self,
        *,
        query: str | None,
        city: str | None,
        provider: str,
        limit: int,
    ) -> str:
        if not query:
            return _json({"success": False, "error": "query is required for poi_search"})
        if provider == "amap":
            return await self._amap_poi_search(query, city=city, limit=limit)
        return await self._geocode(query=query, city=city, provider="public", limit=limit)

    async def _route(
        self,
        *,
        origin: str | None,
        destination: str | None,
        profile: str,
        provider: str,
        city: str | None,
    ) -> str:
        if not origin or not destination:
            return _json({"success": False, "error": "origin and destination are required for route"})
        if provider == "amap":
            return await self._amap_route(origin=origin, destination=destination, profile=profile, city=city)
        if error := self._public_allowed():
            return error
        origin_point = await self._resolve_point_public(origin, city=city)
        destination_point = await self._resolve_point_public(destination, city=city)
        if origin_point is None or destination_point is None:
            return _json({
                "success": False,
                "error": "Could not geocode origin or destination with public provider",
                "provider": "nominatim+osrm",
            })
        lat1, lon1 = origin_point
        lat2, lon2 = destination_point
        profile = profile if profile in {"driving", "walking", "cycling"} else "driving"
        data = await self._get_json(
            f"{_OSRM_BASE_URL}/route/v1/{profile}/{lon1},{lat1};{lon2},{lat2}",
            params={"overview": "false", "alternatives": "false", "steps": "true"},
        )
        routes = data.get("routes", []) if isinstance(data, dict) else []
        best = routes[0] if routes else {}
        return _json({
            "success": True,
            "provider": "nominatim+osrm",
            "sourceType": "public-no-registration",
            "privacyNote": "Origin and destination were sent to public OpenStreetMap/OSRM services.",
            "origin": {"lat": lat1, "lon": lon1},
            "destination": {"lat": lat2, "lon": lon2},
            "profile": profile,
            "distanceMeters": best.get("distance"),
            "durationSeconds": best.get("duration"),
            "raw": data,
        })

    async def _weather(
        self,
        *,
        query: str | None,
        city: str | None,
        latitude: float | None,
        longitude: float | None,
        provider: str,
        days: int,
        air_quality: bool,
    ) -> str:
        if provider == "amap":
            return await self._amap_weather(query=query or city)
        if provider == "qweather":
            return await self._qweather_weather(query=query or city, days=days)
        if error := self._public_allowed():
            return error
        point: tuple[float, float] | None
        place: dict[str, Any] | None = None
        if latitude is not None and longitude is not None:
            point = (latitude, longitude)
        else:
            point, place = await self._open_meteo_geocode(query or city)
        if point is None:
            return _json({"success": False, "error": "query/city or latitude+longitude is required"})
        lat, lon = point
        forecast = await self._get_json(
            _OPEN_METEO_FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,rain,weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,precipitation_sum"
                ),
                "forecast_days": min(max(days, 1), 16),
                "timezone": "auto",
            },
        )
        air: dict[str, Any] | list[Any] | None = None
        if air_quality:
            air = await self._get_json(
                _OPEN_METEO_AIR_QUALITY_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "pm10,pm2_5,us_aqi",
                    "timezone": "auto",
                },
            )
        return _json({
            "success": True,
            "provider": "open-meteo",
            "sourceType": "public-no-registration",
            "privacyNote": "Location was sent to the public Open-Meteo service.",
            "location": {"lat": lat, "lon": lon, "place": place},
            "forecast": forecast,
            "airQuality": air,
        })

    async def _express_track(
        self,
        *,
        tracking_number: str | None,
        carrier: str | None,
        phone: str | None,
        provider: str,
    ) -> str:
        if provider not in {"auto", "kuaidi100"}:
            return _json({
                "success": False,
                "error": "express_track currently supports Kuaidi100 when configured",
                "provider": provider,
            })
        if not tracking_number:
            return _json({"success": False, "error": "trackingNumber is required"})
        key = self._kuaidi100_key()
        customer = self._kuaidi100_customer()
        if not key or not customer:
            return _json({
                "success": False,
                "error": "No reliable free/no-registration express tracking API is configured.",
                "provider": "kuaidi100",
                "required": ["KUAIDI100_KEY", "KUAIDI100_CUSTOMER"],
                "fallback": "Save the parcel in life/express.json and ask the user to provide status manually or configure a provider.",
            })
        param = {"com": carrier or "auto", "num": tracking_number}
        if phone:
            param["phone"] = phone
        param_text = json.dumps(param, ensure_ascii=False, separators=(",", ":"))
        sign = hashlib.md5(f"{param_text}{key}{customer}".encode("utf-8")).hexdigest().upper()
        data = await self._post_form_json(
            self.config.kuaidi100_query_url,
            data={"customer": customer, "sign": sign, "param": param_text},
        )
        return _json({
            "success": True,
            "provider": "kuaidi100",
            "sourceType": "configured-key",
            "result": data,
        })

    async def _nominatim_search(
        self,
        query: str,
        *,
        city: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        q = f"{query} {city}" if city and city not in query else query
        data = await self._get_json(
            f"{_NOMINATIM_BASE_URL}/search",
            params={
                "q": q,
                "format": "jsonv2",
                "limit": min(max(limit, 1), 10),
                "addressdetails": 1,
                "accept-language": "zh-CN,zh,en",
            },
        )
        return data if isinstance(data, list) else []

    async def _resolve_point_public(self, value: str, *, city: str | None) -> tuple[float, float] | None:
        direct = _split_lat_lon(value)
        if direct is not None:
            return direct
        results = await self._nominatim_search(value, city=city, limit=1)
        if not results:
            return None
        try:
            return float(results[0]["lat"]), float(results[0]["lon"])
        except (KeyError, TypeError, ValueError):
            return None

    async def _open_meteo_geocode(
        self,
        query: str | None,
    ) -> tuple[tuple[float, float] | None, dict[str, Any] | None]:
        if not query:
            return None, None
        data = await self._get_json(
            _OPEN_METEO_GEOCODING_URL,
            params={"name": query, "count": 1, "language": "zh", "format": "json"},
        )
        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            return None, None
        place = results[0]
        try:
            return (float(place["latitude"]), float(place["longitude"])), place
        except (KeyError, TypeError, ValueError):
            return None, place

    async def _amap_geocode(self, query: str, *, city: str | None) -> str:
        key = self._amap_key()
        if not key:
            return _json({"success": False, "error": "AMap key is not configured", "required": ["AMAP_KEY"]})
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/geocode/geo",
            params={"key": key, "address": query, "city": city, "output": "JSON"},
        )
        return _json({"success": True, "provider": "amap", "sourceType": "configured-key", "result": data})

    async def _amap_regeocode(self, latitude: float, longitude: float) -> str:
        key = self._amap_key()
        if not key:
            return _json({"success": False, "error": "AMap key is not configured", "required": ["AMAP_KEY"]})
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/geocode/regeo",
            params={"key": key, "location": f"{longitude},{latitude}", "output": "JSON", "extensions": "base"},
        )
        return _json({"success": True, "provider": "amap", "sourceType": "configured-key", "result": data})

    async def _amap_weather(self, query: str | None) -> str:
        key = self._amap_key()
        if not key:
            return _json({"success": False, "error": "AMap key is not configured", "required": ["AMAP_KEY"]})
        if not query:
            return _json({"success": False, "error": "city/adcode query is required for AMap weather"})
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/weather/weatherInfo",
            params={"key": key, "city": query, "extensions": "all", "output": "JSON"},
        )
        return _json({"success": True, "provider": "amap", "sourceType": "configured-key", "result": data})

    async def _amap_poi_search(self, query: str, *, city: str | None, limit: int) -> str:
        key = self._amap_key()
        if not key:
            return _json({"success": False, "error": "AMap key is not configured", "required": ["AMAP_KEY"]})
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/place/text",
            params={
                "key": key,
                "keywords": query,
                "city": city,
                "offset": min(max(limit, 1), 10),
                "page": 1,
                "extensions": "base",
                "output": "JSON",
            },
        )
        return _json({"success": True, "provider": "amap", "sourceType": "configured-key", "result": data})

    async def _amap_route(
        self,
        *,
        origin: str,
        destination: str,
        profile: str,
        city: str | None,
    ) -> str:
        key = self._amap_key()
        if not key:
            return _json({"success": False, "error": "AMap key is not configured", "required": ["AMAP_KEY"]})
        origin_lng_lat = _split_lng_lat(origin)
        destination_lng_lat = _split_lng_lat(destination)
        if origin_lng_lat is None:
            geocode = await self._amap_geocode_point(origin, city=city)
            origin_lng_lat = geocode
        if destination_lng_lat is None:
            geocode = await self._amap_geocode_point(destination, city=city)
            destination_lng_lat = geocode
        if origin_lng_lat is None or destination_lng_lat is None:
            return _json({"success": False, "error": "Could not resolve origin or destination with AMap"})
        endpoint = "walking" if profile == "walking" else "driving"
        origin_text = f"{origin_lng_lat[0]},{origin_lng_lat[1]}"
        destination_text = f"{destination_lng_lat[0]},{destination_lng_lat[1]}"
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/direction/{endpoint}",
            params={"key": key, "origin": origin_text, "destination": destination_text, "output": "JSON"},
        )
        return _json({
            "success": True,
            "provider": "amap",
            "sourceType": "configured-key",
            "profile": endpoint,
            "result": data,
        })

    async def _amap_geocode_point(self, query: str, *, city: str | None) -> tuple[float, float] | None:
        key = self._amap_key()
        data = await self._get_json(
            f"{_AMAP_BASE_URL}/v3/geocode/geo",
            params={"key": key, "address": query, "city": city, "output": "JSON"},
        )
        geocodes = data.get("geocodes", []) if isinstance(data, dict) else []
        if not geocodes:
            return None
        location = geocodes[0].get("location")
        if not isinstance(location, str):
            return None
        parts = [part.strip() for part in location.split(",")]
        if len(parts) != 2:
            return None
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None

    async def _qweather_weather(self, query: str | None, *, days: int) -> str:
        key = self._qweather_key()
        if not key:
            return _json({"success": False, "error": "QWeather key is not configured", "required": ["QWEATHER_KEY"]})
        if not query:
            return _json({"success": False, "error": "query/city is required for QWeather"})
        geo = await self._get_json(
            f"{self.config.qweather_geo_base_url.rstrip('/')}/v2/city/lookup",
            params={"location": query, "key": key, "number": 1, "lang": "zh"},
        )
        locations = geo.get("location", []) if isinstance(geo, dict) else []
        if not locations:
            return _json({"success": False, "provider": "qweather", "error": "No QWeather location found", "geo": geo})
        location_id = locations[0].get("id")
        endpoint_days = 3 if days <= 3 else 7
        forecast = await self._get_json(
            f"{self.config.qweather_api_base_url.rstrip('/')}/v7/weather/{endpoint_days}d",
            params={"location": location_id, "key": key, "lang": "zh"},
        )
        now = await self._get_json(
            f"{self.config.qweather_api_base_url.rstrip('/')}/v7/weather/now",
            params={"location": location_id, "key": key, "lang": "zh"},
        )
        return _json({
            "success": True,
            "provider": "qweather",
            "sourceType": "configured-key",
            "location": locations[0],
            "now": now,
            "forecast": forecast,
        })
