from pydantic import BaseModel, EmailStr, Field

from models.weather import WeatherResponse


class SubscriptionRequest(BaseModel):
    """Тело запроса для создания подписки на уведомления о погоде."""

    email: EmailStr
    city: str = Field(min_length=2, max_length=100)


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
