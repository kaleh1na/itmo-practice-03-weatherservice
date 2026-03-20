"""Тесты для роутера GET /weather/{city}."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

WEATHER_JSON = {
    "name": "London",
    "main": {"temp": 15.5, "humidity": 72},
    "weather": [{"description": "light rain"}],
}


def _make_mock_client(status_code: int, json_data: dict | None = None) -> AsyncMock:
    """Создаёт мок AsyncClient с заданным статусом и JSON-ответом."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    return mock_client


def test_get_weather_happy_path() -> None:
    """Успешный запрос погоды возвращает 200 с корректными полями."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = _make_mock_client(200, WEATHER_JSON)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = client.get("/weather/London")

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert data["temp"] == 15.5
    assert data["humidity"] == 72
    assert data["description"] == "light rain"


def test_get_weather_city_not_found() -> None:
    """OpenWeatherMap вернул 404 — роутер возвращает 404 с detail."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = _make_mock_client(404)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = client.get("/weather/UnknownCity")

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found"


def test_get_weather_timeout() -> None:
    """httpx.TimeoutException → роутер возвращает 503."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = client.get("/weather/London")

    assert response.status_code == 503
    assert response.json()["detail"] == "Weather service temporarily unavailable"


def test_get_weather_request_error() -> None:
    """httpx.RequestError (сетевая ошибка) → роутер возвращает 503."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("connection error")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = client.get("/weather/London")

    assert response.status_code == 503
    assert response.json()["detail"] == "Weather service temporarily unavailable"


def test_get_weather_unexpected_status() -> None:
    """OpenWeatherMap вернул 500 → роутер возвращает 503."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = _make_mock_client(500)
        mock_client_class.return_value.__aenter__.return_value = mock_client

        response = client.get("/weather/London")

    assert response.status_code == 503
    assert response.json()["detail"] == "Weather service temporarily unavailable"
