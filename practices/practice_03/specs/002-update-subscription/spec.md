# Feature Specification: Update Subscription (PATCH /subscribe/{id})

**Feature Branch**: `feature/patch-subscription`  
**Created**: 2026-04-26  
**Status**: In Development  
**Priority**: P2 (Completes CRUD operations)

## Overview

Эта фича позволяет пользователям обновлять существующие подписки на уведомления о погоде. Пользователь может изменить время уведомления или активировать/деактивировать подписку без необходимости удаления и повторного создания.

## What We ARE Building

- ✅ PATCH эндпоинт `/subscribe/{id}` для частичного обновления подписки
- ✅ Возможность изменить `notification_time` (время уведомления)
- ✅ Возможность изменить `is_active` (активность подписки)
- ✅ Валидация входных данных (время в формате HH:MM, boolean для is_active)
- ✅ Проверка существования подписки перед обновлением
- ✅ Возврат обновлённой подписки в ответе

## What We ARE NOT Building

- ❌ Изменение `city` (города) — требует повторной валидации через OpenWeatherMap API, лучше удалить и создать новую подписку
- ❌ Изменение `email` пользователя — это изменение владельца подписки, что нарушает бизнес-логику
- ❌ Массовое обновление нескольких подписок одним запросом
- ❌ История изменений подписки (audit log)
- ❌ Аутентификация/авторизация (кто может обновлять подписку)
- ❌ Валидация прав доступа (любой может обновить любую подписку по ID)

## User Scenarios & Testing

### User Story 5 - Обновление подписки (Priority: P2)

Пользователь хочет изменить время получения уведомлений о погоде или временно отключить подписку без её удаления.

**Why this priority**: Завершает CRUD операции для подписок. Использует существующие поля БД (`notification_time`, `is_active`), которые пока не задействованы. Улучшает UX — не нужно удалять и создавать подписку заново.

**Independent Test**: Можно протестировать созданием подписки через POST `/subscribe`, затем отправкой PATCH `/subscribe/{id}` с новыми значениями и проверкой обновления в БД.

### Acceptance Scenarios

#### Scenario 1: Успешное обновление времени уведомления

**Given** существует подписка с ID=1, notification_time="09:00:00"  
**When** отправляет PATCH `/subscribe/1` с `{"notification_time": "18:30"}`  
**Then** подписка обновляется, notification_time="18:30:00"  
**And** возвращается 200 OK с обновлённой подпиской в JSON

#### Scenario 2: Успешная деактивация подписки

**Given** существует активная подписка с ID=2, is_active=true  
**When** отправляет PATCH `/subscribe/2` с `{"is_active": false}`  
**Then** подписка деактивируется, is_active=false  
**And** возвращается 200 OK с обновлённой подпиской

#### Scenario 3: Частичное обновление (только одно поле)

**Given** существует подписка с ID=3  
**When** отправляет PATCH `/subscribe/3` с `{"notification_time": "12:00"}`  
**Then** обновляется только notification_time, остальные поля не изменяются  
**And** возвращается 200 OK

#### Scenario 4: Обновление обоих полей одновременно

**Given** существует подписка с ID=4  
**When** отправляет PATCH `/subscribe/4` с `{"notification_time": "20:00", "is_active": false}`  
**Then** оба поля обновляются  
**And** возвращается 200 OK

#### Scenario 5: Ошибка - подписка не найдена

**Given** подписка с ID=999 не существует  
**When** отправляет PATCH `/subscribe/999` с `{"is_active": false}`  
**Then** возвращается 404 Not Found с сообщением "Subscription not found"

#### Scenario 6: Ошибка - невалидное время

**Given** существует подписка с ID=5
**When** отправляет PATCH `/subscribe/5` с `{"notification_time": "25:00"}`
**Then** возвращается 422 Unprocessable Entity с сообщением о невалидном формате времени

#### Scenario 7: Ошибка - пустое тело запроса

**Given** существует подписка с ID=6
**When** отправляет PATCH `/subscribe/6` с пустым JSON `{}`
**Then** возвращается 422 Unprocessable Entity с сообщением "At least one field must be provided"

#### Scenario 8: Ошибка - попытка изменить city

**Given** существует подписка с ID=7
**When** отправляет PATCH `/subscribe/7` с `{"city": "Berlin"}`
**Then** возвращается 422 Unprocessable Entity (extra fields not permitted)

#### Scenario 9: Ошибка - попытка изменить email

**Given** существует подписка с ID=8
**When** отправляет PATCH `/subscribe/8` с `{"email": "new@example.com"}`
**Then** возвращается 422 Unprocessable Entity (extra fields not permitted)

### Edge Cases

- **Невалидный ID** (не число): FastAPI автоматически вернёт 422 Unprocessable Entity
- **Отрицательный ID**: Вернёт 404 Not Found (подписка не существует)
- **Время в формате "9:00"** (без ведущего нуля): Pydantic должен принять и нормализовать до "09:00:00"
- **Время "00:00"** (полночь): Валидное значение, должно быть принято
- **Время "23:59"**: Валидное значение, должно быть принято
- **is_active как строка** ("true"/"false"): Pydantic должен преобразовать в boolean
- **Дополнительные поля в запросе**: Запрещены — Pydantic `extra="forbid"` вернёт 422 Unprocessable Entity
- **Обновление уже деактивированной подписки**: Должно работать (можно повторно деактивировать или изменить время)

## Requirements

### Functional Requirements

- **FR-015**: Система ДОЛЖНА предоставлять эндпоинт PATCH `/subscribe/{id}` для обновления подписки
- **FR-016**: Система ДОЛЖНА поддерживать частичное обновление (можно обновить только одно поле)
- **FR-017**: Система ДОЛЖНА валидировать `notification_time` в формате HH:MM (00:00 - 23:59)
- **FR-018**: Система ДОЛЖНА валидировать `is_active` как boolean значение
- **FR-019**: Система ДОЛЖНА возвращать 404 Not Found если подписка с указанным ID не существует
- **FR-020**: Система ДОЛЖНА возвращать 422 Unprocessable Entity если тело запроса пустое или содержит невалидные данные
- **FR-021**: Система ДОЛЖНА запрещать изменение полей `city` и `email` (возвращать 422 при попытке передать эти поля)
- **FR-022**: Система ДОЛЖНА возвращать обновлённую подписку в ответе (200 OK)
- **FR-023**: Система ДОЛЖНА логировать каждую попытку обновления подписки

### Non-Functional Requirements

- **NFR-001**: Обновление подписки должно выполняться за < 100ms (только запрос к БД, без внешних API)
- **NFR-002**: Эндпоинт должен быть идемпотентным (повторное обновление с теми же данными даёт тот же результат)
- **NFR-003**: Код должен соответствовать PEP 8 и использовать type hints
- **NFR-004**: Покрытие тестами минимум 80%

## Success Criteria

- **SC-009**: PATCH `/subscribe/{id}` с валидными данными возвращает 200 OK и обновлённую подписку
- **SC-010**: PATCH `/subscribe/999` (несуществующий ID) возвращает 404 Not Found
- **SC-011**: PATCH `/subscribe/{id}` с невалидным временем возвращает 422 Unprocessable Entity
- **SC-012**: PATCH `/subscribe/{id}` с пустым телом возвращает 422 Unprocessable Entity
- **SC-013**: PATCH `/subscribe/{id}` с попыткой изменить city/email возвращает 422 Unprocessable Entity
- **SC-014**: Все тесты (unit + integration) проходят успешно
- **SC-015**: Код прошёл code review и соответствует стандартам проекта

## Data Model

### Request Schema (SubscriptionUpdate)

```python
class SubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notification_time: Optional[time] = Field(None, description="Время уведомления в формате HH:MM")
    is_active: Optional[bool] = Field(None, description="Активна ли подписка")

    @field_validator("notification_time")
    @classmethod
    def validate_time(cls, v: Optional[time]) -> Optional[time]:
        if v is not None:
            if not (0 <= v.hour <= 23 and 0 <= v.minute <= 59):
                raise ValueError("Time must be in range 00:00 - 23:59")
        return v

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "SubscriptionUpdate":
        if self.notification_time is None and self.is_active is None:
            raise ValueError("At least one field must be provided for update")
        return self
```

### Response Schema (SubscriptionResponse)

Используется существующая модель `SubscriptionResponse` из `models/subscription.py`:

```python
class SubscriptionResponse(BaseModel):
    subscription_id: int
    email: str
    city: str
    notification_time: time
    is_active: bool
    created_at: datetime
```

## API Contract

### Endpoint

```http
PATCH /subscribe/{id}
```

### Path Parameters

- `id` (integer, required): ID подписки для обновления

### Request Body

```json
{
  "notification_time": "18:30",
  "is_active": false
}
```

Оба поля опциональны, но хотя бы одно должно быть указано.

### Response Examples

#### Success (200 OK)

```json
{
  "subscription_id": 1,
  "email": "user@example.com",
  "city": "Moscow",
  "notification_time": "18:30:00",
  "is_active": false,
  "created_at": "2026-04-26T10:30:00"
}
```

#### Not Found (404)

```json
{
  "detail": "Subscription not found"
}
```

#### Unprocessable Entity (422) - Empty Body

```json
{
  "detail": [{"msg": "At least one field must be provided for update"}]
}
```

#### Unprocessable Entity (422) - Invalid Time

```json
{
  "detail": [{"msg": "Time must be in range 00:00 - 23:59"}]
}
```

#### Unprocessable Entity (422) - Forbidden Field

```json
{
  "detail": [{"msg": "Extra inputs are not permitted", "loc": ["body", "city"]}]
}
```

## Implementation Notes

### Database Layer (db/repository.py)

Добавить функцию:

```python
async def update_subscription(
    db: AsyncSession,
    subscription_id: int,
    notification_time: Optional[time] = None,
    is_active: Optional[bool] = None
) -> Optional[Subscription]:
    """
    Обновляет подписку по ID.
    Возвращает обновлённую подписку или None если не найдена.
    """
```

### Router Layer (routers/subscription.py)

Добавить эндпоинт:

```python
@router.patch("/subscribe/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription_endpoint(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновляет существующую подписку.
    Можно изменить время уведомления и/или активность.
    """
```

### Testing Strategy

1. **Unit Tests** (tests/routers/test_subscription.py):
   - Успешное обновление notification_time
   - Успешное обновление is_active
   - Обновление обоих полей
   - 404 для несуществующей подписки
   - 422 для пустого тела
   - 422 для невалидного времени

2. **Integration Tests**:
   - Создать подписку → обновить → проверить в БД
   - Обновить несуществующую подписку

## Dependencies

- Существующая таблица `subscriptions` в PostgreSQL (уже есть)
- Поля `notification_time` и `is_active` в БД (уже есть)
- Pydantic модели для валидации
- SQLAlchemy async для работы с БД

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Concurrent updates одной подписки | Medium | SQLAlchemy использует транзакции, последнее обновление побеждает |
| Попытка обновить удалённую подписку | Low | Вернуть 404, пользователь создаст новую |
| Невалидные данные в запросе | Low | Pydantic валидация на уровне модели |

## Timeline

- Спецификация: 30 минут ✅
- Реализация: 1 час
- Тестирование: 30 минут
- Code Review: 15 минут

**Total**: ~2 часа 15 минут
