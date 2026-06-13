from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import BotCommand

from config import (
    TELEGRAM_TOKEN,
    LOG_LEVEL,
    LOG_FORMAT,
    validate_environment,
)

from database import (
    create_database,
    health_check,
)

from telegram_bot.handlers import router

from database import get_session

from sqlalchemy import select

from models.user import User

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
)

logger = logging.getLogger(__name__)


bot = Bot(
    token=TELEGRAM_TOKEN,
)

dp = Dispatcher()

dp.include_router(router)


async def set_bot_commands() -> None:
    commands = [
        BotCommand(
            command="start",
            description="Запуск бота",
        ),
        BotCommand(
            command="analysis",
            description="Анализ рынка",
        ),
        BotCommand(
            command="demo",
            description="Демо торговля",
        ),
        BotCommand(
            command="learning",
            description="Самообучение",
        ),
        BotCommand(
            command="settings",
            description="Настройки",
        ),
    ]

    await bot.set_my_commands(commands)

async def test_notification() -> None:

    await asyncio.sleep(30)

    async with get_session() as session:

        result = await session.execute(
            select(User)
        )

        users = result.scalars().all()

        for user in users:

            try:
                await bot.send_message(
                    user.telegram_id,
                    "🔔 Тест автоуведомлений работает."
                )

            except Exception as error:
                print(
                    "NOTIFICATION_ERROR:",
                    repr(error)
                )
async def startup() -> None:
    logger.info("Starting AI Trading Bot...")

    validate_environment()

    logger.info("Environment validated.")

    database_ok = await health_check()

    print("DATABASE_OK =", database_ok)

    logger.info(
        f"DATABASE_OK = {database_ok}"
    )

    # Временно отключаем остановку бота при ошибке PostgreSQL
    logger.info(
        "Database connection check completed."
    )

    await create_database()

    logger.info("Database initialized.")

    await set_bot_commands()

    logger.info("Telegram commands registered.")

    asyncio.create_task(
        test_notification()
    )


async def shutdown() -> None:
    logger.info("Stopping AI Trading Bot...")

    await bot.session.close()

    logger.info("Bot stopped.")


async def main() -> None:
    try:
        await startup()

        logger.info("Bot polling started.")

        await dp.start_polling(bot)

    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
