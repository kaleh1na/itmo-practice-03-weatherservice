# Tech Context

## Стек технологий

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Web framework | FastAPI | 0.135.1 |
| ASGI сервер | Uvicorn | 0.42.0 |
| ORM | SQLAlchemy (async) | 2.0.41 |
| БД драйвер | asyncpg | 0.30.0 |
| База данных | PostgreSQL | 16 (Docker) |
| HTTP клиент | httpx | 0.28.1 |
| Валидация | Pydantic v2 | 2.12.5 |
| Email валидация | email-validator | 2.3.0 |
| Env переменные | python-dotenv | 1.1.0 |

## Переменные окружения

| Переменная | Описание | Пример |
|-----------|---------|--------|
| `OPENWEATHER_API_KEY` | API ключ OpenWeatherMap | `abc123...` |
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://weather:weather@localhost:5432/weatherservice` |

## Запуск окружения

```bash
# 1. Запустить PostgreSQL
docker-compose up -d

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Скопировать и заполнить .env
cp .env.example .env

# 4. Запустить сервер
uvicorn main:app --reload
```

## Запуск тестов

```bash
python -m pytest
```

## Docker

[`docker-compose.yml`](../docker-compose.yml) поднимает PostgreSQL 16:
- Контейнер: `weatherservice-postgres`
- Порт: `5432:5432`
- БД: `weatherservice`, пользователь: `weather`, пароль: `weather`
- Данные персистируются в volume `postgres_data`
- Healthcheck: `pg_isready -U weather -d weatherservice`

## Структура проекта

```
practice_03/
├── main.py                  — точка входа FastAPI
├── database.py              — engine, Base, get_db
├── requirements.txt
├── docker-compose.yml
├── .env
├── models/
│   ├── __init__.py
│   ├── weather.py           — WeatherResponse, ErrorResponse
│   ├── subscription.py      — Pydantic-схемы подписок
│   └── db_models.py         — SQLAlchemy ORM (User, Subscription)
├── routers/
│   ├── __init__.py
│   ├── weather.py           — GET /weather/{city}
│   └── subscription.py      — POST/DELETE /subscribe, GET /subscriptions
├── db/
│   ├── __init__.py
│   └── repository.py        — CRUD-функции
├── plans/                   — планы реализации (архитектурные решения)
├── memory-bank/             — контекст проекта для AI-агентов
└── .roo/                    — конфигурация Roo Code (rules, skills, modes)
```

## Внешние зависимости

### OpenWeatherMap API
- URL: `https://api.openweathermap.org/data/2.5/weather`
- Параметры: `q={city}`, `appid={key}`, `units=metric`
- Таймаут: 5 секунд
- Ошибки: 404 → город не найден, timeout/5xx → 503

## Ограничения текущей реализации

- Нет Redis-кэширования (запланировано в архитектуре v2.0, но не реализовано)
- Нет Alembic-миграций (таблицы создаются через `create_all` при старте)
- Нет retry-логики для OpenWeatherMap API
- Нет аутентификации
