from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import Subscription, User


async def get_or_create_user(db: AsyncSession, email: str) -> User:
    """Возвращает существующего пользователя по email или создаёт нового."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email)
        db.add(user)
        await db.flush()
    return user


async def get_subscription_by_user_city(
    db: AsyncSession,
    user_id: int,
    city: str,
) -> Subscription | None:
    """Возвращает подписку по user_id и городу (без учёта регистра) или None."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.city.ilike(city),
        )
    )
    return result.scalar_one_or_none()


async def create_subscription(db: AsyncSession, user_id: int, city: str) -> Subscription:
    """Создаёт новую подписку и сохраняет её в БД."""
    subscription = Subscription(user_id=user_id, city=city)
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def delete_subscription(db: AsyncSession, subscription_id: int) -> bool:
    """Удаляет подписку по ID. Возвращает True если удалена, False если не найдена."""
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return False
    await db.delete(subscription)
    await db.commit()
    return True


async def get_all_subscriptions(db: AsyncSession) -> list[tuple[Subscription, str]]:
    """Возвращает список всех подписок вместе с email пользователя."""
    result = await db.execute(
        select(Subscription, User.email).join(User, Subscription.user_id == User.id)
    )
    return result.all()
