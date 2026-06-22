from __future__ import annotations

import json

import httpx
import pytest

from nanobot.agent.tools.china_life import ChinaLifeTool, ChinaLifeToolConfig


def _response(status: int = 200, payload: dict | list | None = None) -> httpx.Response:
    response = httpx.Response(status, json=payload if payload is not None else {})
    response._request = httpx.Request("GET", "https://mock")
    return response


@pytest.mark.asyncio
async def test_public_weather_uses_open_meteo_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict]] = []

    async def mock_get(self, url, **kwargs):
        calls.append((str(url), kwargs.get("params") or {}))
        if "geocoding-api.open-meteo.com" in str(url):
            return _response(payload={"results": [{"latitude": 31.23, "longitude": 121.47, "name": "上海"}]})
        assert "api.open-meteo.com" in str(url)
        return _response(payload={"current": {"temperature_2m": 25}})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    tool = ChinaLifeTool()
    result = json.loads(await tool.execute(operation="weather", query="上海", days=1))

    assert result["success"] is True
    assert result["provider"] == "open-meteo"
    assert result["sourceType"] == "public-no-registration"
    assert calls[0][1]["name"] == "上海"
    assert calls[1][1]["latitude"] == 31.23
    assert calls[1][1]["forecast_days"] == 1


@pytest.mark.asyncio
async def test_public_route_uses_nominatim_and_osrm(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict]] = []

    async def mock_get(self, url, **kwargs):
        calls.append((str(url), kwargs.get("params") or {}))
        if str(url).endswith("/search"):
            index = len([call for call in calls if call[0].endswith("/search")])
            point = {"lat": "31.2", "lon": "121.4"} if index == 1 else {"lat": "31.3", "lon": "121.5"}
            return _response(payload=[point])
        assert "router.project-osrm.org" in str(url)
        return _response(payload={"routes": [{"distance": 1234.0, "duration": 567.0}]})

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    tool = ChinaLifeTool()
    result = json.loads(
        await tool.execute(
            operation="route",
            origin="人民广场",
            destination="上海站",
            city="上海",
            profile="driving",
        )
    )

    assert result["success"] is True
    assert result["provider"] == "nominatim+osrm"
    assert result["distanceMeters"] == 1234.0
    assert "121.4,31.2;121.5,31.3" in calls[-1][0]


@pytest.mark.asyncio
async def test_amap_missing_key_returns_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMAP_KEY", raising=False)

    tool = ChinaLifeTool()
    result = json.loads(await tool.execute(operation="geocode", provider="amap", query="上海"))

    assert result["success"] is False
    assert result["required"] == ["AMAP_KEY"]


@pytest.mark.asyncio
async def test_kuaidi100_missing_key_returns_manual_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KUAIDI100_KEY", raising=False)
    monkeypatch.delenv("KUAIDI100_CUSTOMER", raising=False)

    tool = ChinaLifeTool()
    result = json.loads(
        await tool.execute(operation="express_track", trackingNumber="SF123456789CN", carrier="shunfeng")
    )

    assert result["success"] is False
    assert result["provider"] == "kuaidi100"
    assert "fallback" in result


@pytest.mark.asyncio
async def test_kuaidi100_signs_configured_request(monkeypatch: pytest.MonkeyPatch) -> None:
    posted: dict[str, str] = {}

    async def mock_post(self, url, **kwargs):
        assert url == "https://poll.kuaidi100.com/poll/query.do"
        posted.update(kwargs["data"])
        return _response(payload={"message": "ok", "data": [{"context": "已签收"}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    tool = ChinaLifeTool(ChinaLifeToolConfig(kuaidi100_key="key", kuaidi100_customer="customer"))
    result = json.loads(
        await tool.execute(
            operation="express_track",
            trackingNumber="SF123456789CN",
            carrier="shunfeng",
            phone="1234",
        )
    )

    assert result["success"] is True
    assert result["provider"] == "kuaidi100"
    assert posted["customer"] == "customer"
    assert posted["sign"]
    assert json.loads(posted["param"]) == {
        "com": "shunfeng",
        "num": "SF123456789CN",
        "phone": "1234",
    }
