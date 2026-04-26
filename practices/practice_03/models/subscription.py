from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from models.weather import WeatherResponse


class SubscriptionRequest(BaseModel):
    """Тело запроса для создания подписки на уведомления о погоде."""

    email: EmailStr
    city: str = Field(min_length=2, max_length=100)


class SubscriptionUpdate(BaseModel):
    """Тело запроса для обновления подписки. Запрещает неизвестные поля (city, email и т.д.)."""

    model_config = ConfigDict(extra="forbid")

    notification_time: Optional[time] = Field(None, description="Время уведомления в формате HH:MM")
    is_active: Optional[bool] = Field(None, description="Активна ли подписка")

    @field_validator("notification_time")
    @classmethod
    def validate_time(cls, v: Optional[time]) -> Optional[time]:
        """Валидация времени уведомления."""
        if v is not None:
            if not (0 <= v.hour <= 23 and 0 <= v.minute <= 59):
                raise ValueError("Time must be in range 00:00 - 23:59")
        return v

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "SubscriptionUpdate":
        """Проверка что хотя бы одно поле указано."""
        if self.notification_time is None and self.is_active is None:
            raise ValueError("At least one field must be provided for update")
        return self


class SubscriptionUpdateResponse(BaseModel):
    """Ответ после успешного обновления подписки."""

    subscription_id: int
    email: str
    city: str
    notification_time: time
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    """Ответ после успешного создания подписки."""

    subscription_id: int
    city: str
    email: str
    weather: WeatherResponse


class SubscriptionItem(BaseModel):
    """Элемент списка подписок."""

    subscription_id: int
    email: str
    city: str


class SubscriptionsListResponse(BaseModel):
    """Ответ со списком всех подписок."""

    subscriptions: list[SubscriptionItem]
    total: int
