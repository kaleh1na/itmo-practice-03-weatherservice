# WeatherService Constitution

<!-- 
Sync Impact Report:
Version change: [CONSTITUTION_VERSION] → 1.0.0
Initial constitution creation for WeatherService project
Ratification date: 2026-04-26
Templates status: ✅ All templates aligned with constitution principles
-->

## Core Principles

### I. API-First Design

REST API является основным интерфейсом системы. Каждый эндпоинт ДОЛЖЕН:
- Использовать Pydantic модели для request/response схем
- Возвращать структурированные JSON ответы
- Обрабатывать ошибки через HTTPException с явными status codes
- Быть задокументирован через OpenAPI (FastAPI автодокументация)

**Rationale**: Четкий контракт API обеспечивает предсказуемость интеграций и упрощает тестирование.

### II. Async-First Architecture

Все I/O операции ДОЛЖНЫ быть асинхронными:
- Работа с базой данных через async SQLAlchemy
- HTTP запросы через httpx (async)
- FastAPI эндпоинты как async def
- Избегать блокирующих операций в event loop

**Rationale**: Асинхронность критична для производительности при работе с внешними API и базой данных.

### III. Data Validation & Type Safety

Строгая типизация и валидация данных ОБЯЗАТЕЛЬНЫ:
- Type annotations для всех функций и параметров
- Pydantic v2 для валидации входных/выходных данных
- email-validator для проверки email адресов
- Никаких raw dict на границах API

**Rationale**: Ранняя валидация предотвращает ошибки и улучшает developer experience.

### IV. Separation of Concerns

Один файл — одна ответственность:
- Models (models/) — только Pydantic схемы и SQLAlchemy модели
- Routers (routers/) — только обработка HTTP запросов
- Repository (db/) — только CRUD операции с БД
- Бизнес-логика НЕ должна быть в роутерах

**Rationale**: Четкое разделение упрощает тестирование, поддержку и масштабирование.

### V. Observability & Logging

Каждый запрос ДОЛЖЕН быть залогирован:
- Входящие запросы (метод, путь, параметры)
- Исход операции (успех/ошибка)
- Внешние вызовы (OpenWeatherMap API)
- Использовать стандартный модуль logging
- Структурированные логи с контекстом

**Rationale**: Логи критичны для отладки и мониторинга в production.

### VI. Configuration Management

Конфигурация через переменные окружения:
- Секреты (API ключи, пароли БД) ТОЛЬКО через os.getenv()
- Никогда не хардкодить credentials в коде
- .env файл для локальной разработки
- .env.example как шаблон без реальных секретов

**Rationale**: Безопасность и гибкость деплоя в разные окружения.

### VII. Test Coverage (NON-NEGOTIABLE)

Тестирование ОБЯЗАТЕЛЬНО перед коммитом:
- pytest + pytest-asyncio для async тестов
- Mock всех внешних HTTP вызовов (httpx.AsyncClient)
- Покрытие: happy path + 4xx ошибки + edge cases
- Тесты НЕ должны делать реальные сетевые запросы
- `python -m pytest` должен проходить перед каждым PR

**Rationale**: Тесты — единственная гарантия корректности при рефакторинге.

## Code Style Standards

### Naming Conventions
- snake_case для переменных, функций, модулей
- PascalCase для классов (Pydantic модели, SQLAlchemy модели)
- UPPER_CASE для констант
- Префикс `_` для приватных методов

### Documentation
- Docstrings разрешены для сложной логики
- Inline комментарии ЗАПРЕЩЕНЫ (код должен быть самодокументируемым)
- Type hints ОБЯЗАТЕЛЬНЫ для всех функций

### Formatting
- PEP 8 compliance
- f-strings для форматирования (не .format() или %)
- Группировка импортов: stdlib → third-party → local (разделены пустой строкой)
- Никогда не использовать bare `except:` — только конкретные типы исключений

## Architecture Constraints

### Database Layer
- SQLAlchemy 2.0+ с async engine
- asyncpg драйвер для PostgreSQL
- Модели в models/db_models.py
- CRUD операции изолированы в db/repository.py
- Транзакции управляются через async with session

### External Dependencies
- OpenWeatherMap API — единственный внешний источник данных о погоде
- Timeout 5 секунд для внешних запросов
- Обработка ошибок: 404 → город не найден, timeout/5xx → 503 Service Unavailable

### Error Handling
- Все HTTP ошибки через HTTPException
- Явные status codes и detail messages
- Логирование ошибок перед возвратом клиенту
- Не раскрывать внутренние детали в error messages

## Testing Requirements

### Test Structure
- Тесты в tests/ директории, зеркалируют структуру src
- Именование: test_*.py для файлов, test_* для функций
- Один тестовый файл на один модуль

### Test Coverage Areas
- **Happy path**: Основные сценарии использования
- **4xx errors**: Невалидные входные данные, несуществующие ресурсы
- **Edge cases**: Пустые списки, граничные значения, concurrent access
- **External failures**: Mock ошибок внешних API

### Mocking Strategy
- httpx.AsyncClient для внешних HTTP вызовов
- AsyncMock для async функций
- Не мокать Pydantic валидацию (тестируем реальное поведение)

## Development Workflow

### Local Development
1. `docker-compose up -d` — запуск PostgreSQL
2. `pip install -r requirements.txt` — установка зависимостей
3. Создать `.env` из `.env.example`
4. `uvicorn main:app --reload` — запуск с hot-reload

### Before Commit
1. `python -m pytest` — все тесты должны пройти
2. Проверить, что нет hardcoded secrets
3. Убедиться, что новый код следует PEP 8

### PR Requirements
- Title format: `[scope] Short description` (e.g., `[routers] Add DELETE /subscribe/{id}`)
- Все тесты проходят
- Один PR — одна задача (избегать смешивания несвязанных изменений)
- Code review обязателен

## Governance

### Constitution Authority
Эта конституция является высшим приоритетом для всех решений в проекте. При конфликте между конституцией и другими документами, конституция имеет приоритет.

### Amendment Process
Изменения в конституцию требуют:
1. Документирование причины изменения
2. Обновление версии согласно semver:
   - MAJOR: Несовместимые изменения принципов
   - MINOR: Добавление новых принципов/секций
   - PATCH: Уточнения формулировок, исправления опечаток
3. Обновление зависимых шаблонов и документации

### Compliance Review
- Все PR должны проверяться на соответствие конституции
- Нарушения принципов должны быть явно обоснованы
- Сложность должна быть оправдана бизнес-требованиями

### Runtime Guidance
Для детальных инструкций по разработке см. `agents.md` и `.roo/rules/rules.md`.

**Version**: 1.0.0 | **Ratified**: 2026-04-26 | **Last Amended**: 2026-04-26
