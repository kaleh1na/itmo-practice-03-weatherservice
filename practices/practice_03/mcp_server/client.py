import os

import httpx


class WeatherServiceClient:
    """HTTP-клиент для взаимодействия с WeatherService API."""

    def __init__(self) -> None:
        self._base_url = os.getenv("WEATHER_SERVICE_URL", "http://localhost:8000")

    async def get_weather(self, city: str) -> dict:
        """Получить текущую погоду для указанного города."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self._base_url}/weather/{city}")
                if response.status_code == 404:
                    return {"error": f"Город '{city}' не найден"}
                if response.status_code == 503:
                    return {"error": "WeatherService временно недоступен"}
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as exc:
                return {"error": f"Ошибка подключения к WeatherService: {exc}"}

    async def create_subscription(self, email: str, city: str) -> dict:
        """Создать подписку на уведомления о погоде для email и города."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._base_url}/subscribe",
                    json={"email": email, "city": city},
                )
                if response.status_code == 409:
                    return {"error": f"Подписка для {email} на город '{city}' уже существует"}
                if response.status_code == 404:
                    return {"error": f"Город '{city}' не найден"}
                if response.status_code == 400:
                    return {"error": f"Невалидные данные: {response.json().get('detail', '')}"}
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as exc:
                return {"error": f"Ошибка подключения к WeatherService: {exc}"}

    async def list_subscriptions(self) -> dict:
        """Получить список всех активных подписок."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self._base_url}/subscriptions")
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as exc:
                return {"error": f"Ошибка подключения к WeatherService: {exc}"}

    async def delete_subscription(self, subscription_id: int) -> dict:
        """Удалить подписку по её идентификатору."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{self._base_url}/subscribe/{subscription_id}"
                )
                if response.status_code == 404:
                    return {"error": f"Подписка с ID {subscription_id} не найдена"}
                if response.status_code == 204:
                    return {"success": True, "message": f"Подписка {subscription_id} удалена"}
                response.raise_for_status()
                return {"success": True, "message": f"Подписка {subscription_id} удалена"}
            except httpx.RequestError as exc:
                return {"error": f"Ошибка подключения к WeatherService: {exc}"}
