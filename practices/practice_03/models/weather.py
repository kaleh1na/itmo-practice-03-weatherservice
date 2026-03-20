from pydantic import BaseModel


class WeatherResponse(BaseModel):
    """Ответ с данными о погоде для города."""

    city: str
    temp: float
    humidity: int
    description: str


class ErrorResponse(BaseModel):
    """Ответ с описанием ошибки."""

    detail: str
