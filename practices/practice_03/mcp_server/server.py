from fastmcp import FastMCP

from mcp_server.client import WeatherServiceClient

mcp = FastMCP(name="WeatherService Client")
_client = WeatherServiceClient()


@mcp.tool
async def get_weather(city: str) -> dict:
    """Получить текущую погоду для указанного города через WeatherService API.

    Возвращает температуру (°C), влажность и описание погоды.
    Пример: get_weather('Moscow') -> {'city': 'Moscow', 'temp': 5.2, 'humidity': 80, 'description': 'overcast clouds'}
    """
    return await _client.get_weather(city)


@mcp.tool
async def create_subscription(email: str, city: str) -> dict:
    """Подписать email на уведомления о погоде для указанного города.

    Создаёт подписку в WeatherService. Возвращает subscription_id и текущую погоду.
    Пример: create_subscription('user@example.com', 'London')
    """
    return await _client.create_subscription(email, city)


@mcp.tool
async def list_subscriptions() -> dict:
    """Получить список всех активных подписок на уведомления о погоде.

    Возвращает массив подписок с полями: subscription_id, email, city.
    Также возвращает общее количество подписок в поле total.
    """
    return await _client.list_subscriptions()


@mcp.tool
async def delete_subscription(subscription_id: int) -> dict:
    """Удалить подписку на уведомления о погоде по её идентификатору.

    Пример: delete_subscription(42) — удалит подписку с ID 42.
    Возвращает подтверждение удаления или сообщение об ошибке.
    """
    return await _client.delete_subscription(subscription_id)


if __name__ == "__main__":
    mcp.run()
