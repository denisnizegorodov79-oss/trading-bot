from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import (
    DATABASE_URL,
    DB_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
)

from models.base import Base
from models.trade import Trade
from models.historical_error import HistoricalError
from models.user import User
from models.market_signal import MarketSignal
from models.user_settings import UserSettings
def build_database_url() -> str:
    """
    Преобразование DATABASE_URL для SQLAlchemy Async.
    """

    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        return DATABASE_URL

    if DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace(
            "postgres://",
            "postgresql+asyncpg://",
            1,
        )

    if DATABASE_URL.startswith("postgresql://"):
        return DATABASE_URL.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    return DATABASE_URL


DATABASE_CONNECTION_URL = build_database_url()

print("DATABASE_CONNECTION_URL =", repr(DATABASE_CONNECTION_URL))


engine = create_async_engine(
    DATABASE_CONNECTION_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронная сессия PostgreSQL.
    """

    session = async_session_factory()

    try:
        yield session
        await session.commit()

    except Exception:
        await session.rollback()
        raise

    finally:
        await session.close()


async def create_database() -> None:
    """
    Создание всех таблиц проекта.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )


async def drop_database() -> None:
    """
    Полное удаление таблиц проекта.
    Использовать только во время разработки.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )

print("DATABASE.PY VERSION 999")
async def health_check() -> bool:
    """
    Проверка подключения к PostgreSQL.
    """

    try:
        async with engine.begin() as connection:
            await connection.exec_driver_sql(
                "SELECT 1"
            )

        return True

    except Exception as e:
        print("POSTGRES ERROR:", repr(e))
        return False


async def dispose_database() -> None:
    """
    Корректное закрытие пула соединений.
    """

    await engine.dispose()
