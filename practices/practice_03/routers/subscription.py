import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from db.repository import (
    create_subscription,
    delete_subscription,
    get_all_subscriptions,
    get_or_create_user,
    get_subscription_by_id,
    get_subscription_by_user_city,
    update_subscription,
)
from models.db_models import Subscription, User
from models.weather import ErrorResponse
from models.subscription import (
    SubscriptionRequest,
    SubscriptionResponse,
    SubscriptionItem,
    SubscriptionsListResponse,
    SubscriptionUpdate,
    SubscriptionUpdateResponse,
)
from routers.weather import _fetch_weather

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/subscribe",
    response_model=SubscriptionResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Невалидные входные данные"},
        404: {"model": ErrorResponse, "description": "Город не найден"},
        409: {"model": ErrorResponse, "description": "Подписка уже существует"},
        503: {"model": ErrorResponse, "description": "Weather API недоступен"},
    },
    summary="Подписаться на уведомления о погоде",
)
async def create_subscription_route(
    request: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Создаёт подписку на уведомления о погоде для указанного города и email."""
    logger.info("POST /subscribe — email=%s city=%s", request.email, request.city)

    user = await get_or_create_user(db, str(request.email))

    existing = await get_subscription_by_user_city(db, user.id, request.city)
    if existing is not None:
        logger.warning(
            "POST /subscribe — дубликат: email=%s city=%s", request.email, request.city
        )
        raise HTTPException(status_code=409, detail="Subscription already exists")

    weather = await _fetch_weather(request.city)

    subscription = await create_subscription(db, user.id, request.city)

    logger.info("POST /subscribe — создана подписка id=%d", subscription.id)

    return SubscriptionResponse(
        subscription_id=subscription.id,
        city=weather.city,
        email=str(request.email),
        weather=weather,
    )


@router.delete(
    "/subscribe/{subscription_id}",
    status_code=204,
    responses={
        404: {"model": ErrorResponse, "description": "Подписка не найдена"},
    },
    summary="Удалить подписку по ID",
)
async def delete_subscription_route(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет подписку по её идентификатору."""
    logger.info("DELETE /subscribe/%d", subscription_id)

    deleted = await delete_subscription(db, subscription_id)
    if not deleted:
        logger.warning("DELETE /subscribe/%d — не найдена", subscription_id)
        raise HTTPException(status_code=404, detail="Subscription not found")

    logger.info("DELETE /subscribe/%d — удалена", subscription_id)


@router.get(
    "/subscriptions",
    response_model=SubscriptionsListResponse,
    summary="Получить список всех подписок",
)
async def get_subscriptions_route(
    db: AsyncSession = Depends(get_db),
) -> SubscriptionsListResponse:
    """Возвращает список всех активных подписок."""
    rows = await get_all_subscriptions(db)

    logger.info("GET /subscriptions — всего: %d", len(rows))

    items = [
        SubscriptionItem(
            subscription_id=sub.id,
            email=email,
            city=sub.city,
        )
        for sub, email in rows
    ]
    return SubscriptionsListResponse(subscriptions=items, total=len(items))


@router.patch(
    "/subscribe/{subscription_id}",
    response_model=SubscriptionUpdateResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Невалидные данные или пустое тело запроса"},
        404: {"model": ErrorResponse, "description": "Подписка не найдена"},
    },
    summary="Обновить подписку",
)
async def update_subscription_route(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionUpdateResponse:
    """Обновляет существующую подписку (время уведомления и/или активность)."""
    logger.info(
        "PATCH /subscribe/%d — notification_time=%s is_active=%s",
        subscription_id,
        update_data.notification_time,
        update_data.is_active,
    )

    updated_subscription = await update_subscription(
        db,
        subscription_id,
        notification_time=update_data.notification_time,
        is_active=update_data.is_active,
    )

    if updated_subscription is None:
        logger.warning("PATCH /subscribe/%d — не найдена", subscription_id)
        raise HTTPException(status_code=404, detail="Subscription not found")

    result = await db.execute(
        select(Subscription, User.email)
        .join(User, Subscription.user_id == User.id)
        .where(Subscription.id == subscription_id)
    )
    row = result.first()
    if row is None:
        logger.error("PATCH /subscribe/%d — не удалось получить email пользователя", subscription_id)
        raise HTTPException(status_code=404, detail="Subscription not found")

    user_email = row[1]

    logger.info("PATCH /subscribe/%d — обновлена", subscription_id)

    return SubscriptionUpdateResponse(
        subscription_id=updated_subscription.id,
        email=user_email,
        city=updated_subscription.city,
        notification_time=updated_subscription.notification_time,
        is_active=updated_subscription.is_active,
        created_at=updated_subscription.created_at,
    )
