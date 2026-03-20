import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI

from database import Base, engine
from routers.weather import router as weather_router
from routers.subscription import router as subscription_router

load_dotenv()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализация БД при старте приложения."""
    logger.info("Создание таблиц БД...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы БД готовы")
    yield


app = FastAPI(title="WeatherService", version="1.0.0", lifespan=lifespan)

app.include_router(weather_router)
app.include_router(subscription_router)
