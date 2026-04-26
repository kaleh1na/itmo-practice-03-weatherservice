# WeatherService API

FastAPI приложение для получения погоды и управления подписками на уведомления о погоде.

## Требования

- Python 3.10+
- Docker (для PostgreSQL)
- API ключ OpenWeatherMap

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте `.env.example` в `.env` (или создайте `.env` файл):

```bash
OPENWEATHER_API_KEY=ваш_ключ_здесь
DATABASE_URL=postgresql+asyncpg://weather:weather@localhost:5432/weatherservice
```

### 3. Запуск PostgreSQL

Запустите Docker (если используете Colima на macOS):

```bash
colima start
```

Затем запустите PostgreSQL через docker-compose:

```bash
docker-compose up -d
```

Проверьте, что контейнер запущен:

```bash
docker ps
```

### 4. Запуск приложения

```bash
uvicorn main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

API документация (Swagger): http://localhost:8000/docs

## Доступные эндпоинты

### Погода

- `GET /weather/{city}` — получить текущую погоду для города

### Подписки

- `POST /subscribe` — создать подписку на уведомления о погоде
- `GET /subscriptions` — получить список всех подписок
- `DELETE /subscribe/{id}` — удалить подписку по ID

## Тестирование

Запуск всех тестов:

```bash
python -m pytest
```

Запуск с подробным выводом:

```bash
python -m pytest -v
```

Запуск конкретного теста:

```bash
python -m pytest tests/routers/test_weather.py
```

## Структура проекта

```
.
├── main.py                 # Точка входа FastAPI приложения
├── database.py             # Настройка SQLAlchemy и подключения к БД
├── models/                 # Pydantic и SQLAlchemy модели
│   ├── weather.py
│   ├── subscription.py
│   └── db_models.py
├── routers/                # API роутеры
│   ├── weather.py
│   └── subscription.py
├── db/                     # Репозитории для работы с БД
│   └── repository.py
├── tests/                  # Тесты
│   └── routers/
├── mcp_server/             # MCP сервер для интеграции
└── docker-compose.yml      # PostgreSQL контейнер
```

## Troubleshooting

### Docker не запускается

Если используете Colima на macOS:

```bash
colima start
```

Если используете Docker Desktop:

```bash
# Запустите Docker Desktop приложение
```

### База данных недоступна

Проверьте, что PostgreSQL контейнер запущен:

```bash
docker ps
```

Проверьте логи контейнера:

```bash
docker logs weatherservice-postgres
```

### Ошибка подключения к OpenWeatherMap API

Убедитесь, что:
1. API ключ указан в `.env` файле
2. API ключ активирован (может занять до 2 часов после регистрации)
3. Есть доступ к интернету

## Разработка

### Запуск с hot-reload

```bash
uvicorn main:app --reload
```

### Форматирование кода

Проект следует PEP 8 стандартам:
- snake_case для переменных и функций
- PascalCase для классов
- Type annotations для всех функций
- Docstrings разрешены, inline комментарии — нет

### Правила архитектуры

- Один файл — одна ответственность
- Модели в `models/`, роутеры в `routers/`
- Pydantic модели для всех request/response схем
- Внешние HTTP вызовы изолированы в отдельных async функциях
- Все HTTP ошибки через `HTTPException`
- Логирование каждого запроса через `logging` модуль
- Переменные окружения через `os.getenv()`

## Лицензия

Учебный проект для ITMO Practice 03
