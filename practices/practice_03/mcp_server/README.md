# WeatherService Client MCP-сервер

MCP-сервер на `fastmcp`, который предоставляет LLM-агентам (Roo Code) инструменты для работы с WeatherService API.

## Инструменты

| Инструмент | Описание | Параметры |
|------------|----------|-----------|
| `get_weather` | Получить текущую погоду для города | `city: str` |
| `create_subscription` | Подписаться на уведомления о погоде | `email: str, city: str` |
| `list_subscriptions` | Список всех активных подписок | — |
| `delete_subscription` | Удалить подписку по ID | `subscription_id: int` |

## Требования

- Python 3.10+
- Запущенный WeatherService (`uvicorn main:app --reload`)
- Установленные зависимости: `pip install -r requirements.txt`

## Запуск сервера вручную

```bash
python -m mcp_server.server
```

Переменная окружения `WEATHER_SERVICE_URL` (по умолчанию `http://localhost:8000`):

```bash
WEATHER_SERVICE_URL=http://localhost:8000 python -m mcp_server.server
```

## Подключение к Roo Code

### Шаг 1: Открыть настройки MCP в Roo Code

В VS Code нажать `Cmd+Shift+P` → `Roo Code: Open MCP Settings` (или через иконку MCP в боковой панели).

### Шаг 2: Добавить конфигурацию сервера

```json
{
  "mcpServers": {
    "weather-service": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/practice_03",
      "env": {
        "WEATHER_SERVICE_URL": "http://localhost:8000"
      }
    }
  }
}
```

> **Важно:** замените `/absolute/path/to/practice_03` на реальный путь к проекту.

### Шаг 3: Перезапустить Roo Code

После сохранения конфигурации Roo Code автоматически запустит MCP-сервер.

### Шаг 4: Проверить подключение

В чате Roo Code спросить:
```
Какая погода в Москве?
```

Агент должен использовать инструмент `get_weather` и вернуть результат.

## Структура

```
mcp_server/
├── __init__.py
├── client.py    # Async HTTP-клиент к WeatherService API
├── server.py    # FastMCP сервер с 4 инструментами
└── README.md    # Эта документация
```
