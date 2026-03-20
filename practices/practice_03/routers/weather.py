import logging
import os

import httpx
from fastapi import APIRouter, HTTPException

from models.weather import ErrorResponse, WeatherResponse

logger = logging.getLogger(__name__)

router = APIRouter()

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 5.0


async def _fetch_weather(city: str) -> WeatherResponse:
    """Запрашивает данные о погоде для города через OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                OPENWEATHER_URL,
                params={"q": city, "appid": api_key, "units": "metric"},
            )
    except httpx.TimeoutException:
        logger.error("_fetch_weather/%s — таймаут запроса к OpenWeatherMap", city)
        raise HTTPException(
            status_code=503,
            detail="Weather service temporarily unavailable",
        )
    except httpx.RequestError as exc:
        logger.error("_fetch_weather/%s — ошибка запроса: %s", city, exc)
        raise HTTPException(
            status_code=503,
            detail="Weather service temporarily unavailable",
        )

    if response.status_code == 404:
        logger.warning("_fetch_weather/%s — город не найден", city)
        raise HTTPException(status_code=404, detail="City not found")

    if response.status_code != 200:
        logger.error(
            "_fetch_weather/%s — неожиданный статус от OpenWeatherMap: %s",
            city,
            response.status_code,
        )
        raise HTTPException(
            status_code=503,
            detail="Weather service temporarily unavailable",
        )

    data = response.json()
    return WeatherResponse(
        city=data["name"],
        temp=data["main"]["temp"],
        humidity=data["main"]["humidity"],
        description=data["weather"][0]["description"],
    )


@router.get(
    "/weather/{city}",
    response_model=WeatherResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Город не найден"},
        503: {"model": ErrorResponse, "description": "Weather API недоступен"},
    },
    summary="Получить погоду для города",
)
async def get_weather(city: str) -> WeatherResponse:
    """Возвращает текущую погоду для указанного города через OpenWeatherMap API."""
    logger.info("GET /weather/%s — запрос погоды", city)
    weather = await _fetch_weather(city)
    logger.info("GET /weather/%s — успешно: %s°C", city, weather.temp)
    return weather
