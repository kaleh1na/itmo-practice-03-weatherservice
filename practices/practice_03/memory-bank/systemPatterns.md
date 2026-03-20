# System Patterns

## Архитектура

FastAPI-приложение с разделением на слои:

```
main.py              — точка входа, регистрация роутеров, lifespan (создание таблиц БД)
routers/             — HTTP-обработчики (только маршрутизация, без бизнес-логики)
  weather.py         — GET /weather/{city}
  subscription.py    — POST /subscribe, DELETE /subscribe/{id}, GET /subscriptions
models/              — Pydantic-схемы запросов/ответов
  weather.py         — WeatherResponse, ErrorResponse
  subscription.py    — SubscriptionRequest, SubscriptionResponse, SubscriptionItem, SubscriptionsListResponse
  db_models.py       — SQLAlchemy ORM-модели (User, Subscription)
db/
  repository.py      — все операции с БД (get_or_create_user, create_subscription, delete_subscription, get_all_subscriptions)
database.py          — engine, AsyncSessionLocal, Base, get_db dependency
```

## Ключевые паттерны

### Изоляция внешних HTTP-вызовов
Все запросы к OpenWeatherMap вынесены в `_fetch_weather(city)` в [`routers/weather.py`](../routers/weather.py). Роутер вызывает эту функцию, не делая HTTP-запросов напрямую.

### Repository pattern
Вся логика работы с БД сосредоточена в [`db/repository.py`](../db/repository.py). Роутеры импортируют функции репозитория и не пишут SQL/ORM-запросы напрямую.

### Dependency Injection (FastAPI Depends)
Сессия БД передаётся через `Depends(get_db)` — роутеры не создают сессии вручную.

### get_or_create
`get_or_create_user` — пользователь создаётся автоматически при первой подписке, без отдельного эндпоинта регистрации.

### Уникальность подписки
Уникальность `(user_id, city)` обеспечена на двух уровнях:
- БД: `UniqueConstraint("user_id", "city")` в [`models/db_models.py`](../models/db_models.py)
- Приложение: явная проверка через `get_subscription_by_user_city` перед созданием → 409 Conflict

### Логирование
Каждый роутер логирует входящий запрос и его исход через `logging.getLogger(__name__)`.

### Конфигурация через env
`OPENWEATHER_API_KEY` и `DATABASE_URL` читаются через `os.getenv()`, загружаются через `python-dotenv`.

## Схема БД

```
users
  id          INTEGER PK
  email       VARCHAR(255) UNIQUE NOT NULL
  created_at  DATETIME DEFAULT now()

subscriptions
  id                INTEGER PK
  user_id           INTEGER FK → users.id ON DELETE CASCADE
  city              VARCHAR(100) NOT NULL
  notification_time TIME DEFAULT '09:00:00'
  is_active         BOOLEAN DEFAULT true
  created_at        DATETIME DEFAULT now()
  UNIQUE(user_id, city)
```

## API эндпоинты

| Метод  | Путь                      | Описание                        | Коды ответа         |
|--------|---------------------------|---------------------------------|---------------------|
| GET    | `/weather/{city}`         | Текущая погода для города       | 200, 404, 503       |
| POST   | `/subscribe`              | Создать подписку                | 201, 400, 404, 409, 503 |
| DELETE | `/subscribe/{id}`         | Удалить подписку по ID          | 204, 404            |
| GET    | `/subscriptions`          | Список всех подписок            | 200                 |
