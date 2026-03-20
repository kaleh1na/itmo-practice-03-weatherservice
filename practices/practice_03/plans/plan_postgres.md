# План интеграции PostgreSQL в WeatherService

## Источники

- Схема БД взята из [`docs/report_p2.md`](../docs/report_p2.md) (Chain of Thought, Шаг 1–3)
- Текущий API: [`routers/subscription.py`](../routers/subscription.py), [`models/subscription.py`](../models/subscription.py)

---

## Текущее состояние

Подписки хранятся в памяти в [`routers/subscription.py`](../routers/subscription.py:18):
```python
_subscriptions: list[dict] = []
_counter: int = 0
```
Данные теряются при перезапуске. Нужно заменить на PostgreSQL через SQLAlchemy (async).

---

## Схема БД (из docs/report_p2.md)

Две таблицы: `users` и `subscriptions`.

### Таблица `users`
| Поле | Тип | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### Таблица `subscriptions`
| Поле | Тип | Constraints |
|---|---|---|
| id | SERIAL | PRIMARY KEY |
| user_id | INTEGER | FK → users.id, NOT NULL, ON DELETE CASCADE |
| city | VARCHAR(100) | NOT NULL |
| notification_time | TIME | DEFAULT '09:00:00' |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

**Уникальность:** `UNIQUE(user_id, city)` — один пользователь не может подписаться на один город дважды.

---

## Логика работы POST /subscribe с двумя таблицами

Текущий API принимает `{email, city}`. При создании подписки:

```
POST /subscribe {email, city}
  │
  ├─ Найти пользователя по email в таблице users
  │    └─ Если не найден → создать нового пользователя (INSERT INTO users)
  │
  ├─ Проверить дубликат: EXISTS(user_id, city) в subscriptions
  │    └─ Если найден → 409 Conflict
  │
  ├─ Получить погоду через _fetch_weather(city)
  │    └─ Если ошибка → 404 / 503
  │
  └─ Создать подписку (INSERT INTO subscriptions)
       └─ Вернуть 201 Created
```

---

## Архитектура после интеграции

```mermaid
graph TD
    A[FastAPI App] --> B[routers/subscription.py]
    B --> C[db/repository.py]
    C --> D[database.py - AsyncSession]
    D --> E[(PostgreSQL)]
    F[models/db_models.py - ORM User + Subscription] --> D
    G[models/subscription.py - Pydantic] --> B
```

---

## Структура файлов после изменений

```
practice_03/
├── database.py              ← НОВЫЙ: движок, фабрика сессий, Base
├── db/
│   ├── __init__.py          ← НОВЫЙ
│   └── repository.py        ← НОВЫЙ: CRUD через SQLAlchemy
├── models/
│   ├── __init__.py          ← без изменений
│   ├── db_models.py         ← НОВЫЙ: ORM-модели User и Subscription
│   ├── subscription.py      ← без изменений (Pydantic)
│   └── weather.py           ← без изменений
├── routers/
│   ├── subscription.py      ← ИЗМЕНИТЬ: убрать in-memory, добавить Depends(get_db)
│   └── weather.py           ← без изменений
├── main.py                  ← ИЗМЕНИТЬ: lifespan для create_all
├── requirements.txt         ← ИЗМЕНИТЬ: добавить sqlalchemy, asyncpg
└── .env                     ← ИЗМЕНИТЬ: добавить DATABASE_URL
```

---

## Шаги реализации

### 1. Обновить `requirements.txt`

Добавить:
```
asyncpg==0.30.0
greenlet==3.2.1
sqlalchemy==2.0.41
```

### 2. Добавить `DATABASE_URL` в `.env`

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/weatherservice
```

### 3. Создать [`database.py`](../database.py)

```python
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 4. Создать [`models/db_models.py`](../models/db_models.py)

ORM-модели обеих таблиц:

```python
from datetime import datetime, time
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "city", name="unique_user_city"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    notification_time: Mapped[time] = mapped_column(Time, server_default="09:00:00")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="subscriptions")
```

### 5. Создать [`db/repository.py`](../db/repository.py)

CRUD-функции:

| Функция | Описание |
|---|---|
| `get_or_create_user(db, email)` | Найти пользователя по email или создать нового |
| `get_subscription_by_user_city(db, user_id, city)` | Проверка дубликата |
| `create_subscription(db, user_id, city)` | Создание подписки |
| `delete_subscription(db, subscription_id)` | Удаление по ID |
| `get_all_subscriptions(db)` | Список всех подписок (JOIN с users для email) |

### 6. Обновить [`routers/subscription.py`](../routers/subscription.py)

- Убрать `_subscriptions: list[dict]` и `_counter: int`
- Добавить `db: AsyncSession = Depends(get_db)` в каждый роутер
- Логика `POST /subscribe`:
  1. `user = await get_or_create_user(db, request.email)`
  2. Проверить дубликат через `get_subscription_by_user_city(db, user.id, request.city)`
  3. Получить погоду через `_fetch_weather(request.city)`
  4. `sub = await create_subscription(db, user.id, request.city)`
  5. Вернуть `SubscriptionResponse(subscription_id=sub.id, ...)`

### 7. Обновить [`main.py`](../main.py)

```python
from contextlib import asynccontextmanager
from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="WeatherService", version="1.0.0", lifespan=lifespan)
```

---

## Что НЕ меняется

- [`models/subscription.py`](../models/subscription.py) — Pydantic-схемы без изменений
- [`routers/weather.py`](../routers/weather.py) — погода не затрагивается
- Все HTTP-статусы и контракты API — без изменений
- `subscription_id` в ответе — это `subscriptions.id` (не `users.id`)

---

## Зависимости между компонентами

```mermaid
graph LR
    A[main.py] -->|lifespan create_all| B[database.py]
    C[routers/subscription.py] -->|Depends get_db| B
    C -->|вызывает| D[db/repository.py]
    D -->|AsyncSession| B
    D -->|ORM User + Subscription| E[models/db_models.py]
    E -->|Base| B
```
