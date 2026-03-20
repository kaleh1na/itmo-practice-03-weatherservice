# Progress

## Что реализовано

### Этап 1 — GET /weather/{city} ✅
- [`routers/weather.py`](../routers/weather.py) — эндпоинт и `_fetch_weather(city)`
- [`models/weather.py`](../models/weather.py) — `WeatherResponse`, `ErrorResponse`
- Интеграция с OpenWeatherMap API через `httpx`
- Обработка 404 (город не найден) и 503 (таймаут/сетевая ошибка)

### Этап 2 — POST /subscribe ✅
- [`routers/subscription.py`](../routers/subscription.py) — эндпоинт `POST /subscribe`
- [`models/subscription.py`](../models/subscription.py) — `SubscriptionRequest`, `SubscriptionResponse`
- Валидация email через `EmailStr`, города через `Field(min_length=2)`
- Проверка дубликата → 409 Conflict
- Проверка города через `_fetch_weather` → 404/503

### Этап 3 — DELETE /subscribe/{id} и GET /subscriptions ✅
- `DELETE /subscribe/{subscription_id}` → 204 / 404
- `GET /subscriptions` → список всех подписок с `total`
- Модели `SubscriptionItem`, `SubscriptionsListResponse` добавлены в [`models/subscription.py`](../models/subscription.py)

### Этап 4 — Интеграция PostgreSQL ✅
- [`database.py`](../database.py) — async engine, `AsyncSessionLocal`, `Base`, `get_db`
- [`models/db_models.py`](../models/db_models.py) — ORM-модели `User`, `Subscription`
- [`db/repository.py`](../db/repository.py) — `get_or_create_user`, `get_subscription_by_user_city`, `create_subscription`, `delete_subscription`, `get_all_subscriptions`
- [`main.py`](../main.py) — lifespan с `Base.metadata.create_all`
- In-memory хранилище полностью заменено на PostgreSQL
- [`docker-compose.yml`](../docker-compose.yml) — PostgreSQL-контейнер

## Текущее состояние

Все запланированные фичи реализованы. Приложение полностью функционально.

### Этап 5 — Тесты ✅

- [`tests/routers/test_weather.py`](../tests/routers/test_weather.py) — 5 тест-кейсов для `GET /weather/{city}`: happy path, 404, 503 (таймаут), 503 (сетевая ошибка), 503 (неожиданный статус)
- [`tests/routers/test_subscription.py`](../tests/routers/test_subscription.py) — 6 тест-кейсов: POST happy path, 409 дубликат, 404 город, DELETE 204, DELETE 404, GET список
- [`pytest.ini`](../pytest.ini) — `asyncio_mode = auto`, `testpaths = tests`
- Все внешние HTTP-вызовы замокированы, реальные сетевые запросы не выполняются
- `pytest`, `pytest-asyncio`, `pytest-mock` добавлены в [`requirements.txt`](../requirements.txt)

## Текущее состояние

Все запланированные фичи реализованы. Тесты написаны и проходят (11/11). Приложение полностью функционально.

## Что не реализовано / возможные следующие шаги

- [ ] Миграции через Alembic (сейчас таблицы создаются через `create_all` при старте)
- [ ] Аутентификация / авторизация
- [ ] Фактическая отправка уведомлений о погоде (поле `notification_time` есть в БД, но логика не реализована)
- [ ] Фильтрация подписок по email в `GET /subscriptions`
- [ ] Пагинация в `GET /subscriptions`
- [ ] Redis-кэширование данных о погоде (TTL 10 мин)
