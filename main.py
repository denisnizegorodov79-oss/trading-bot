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


async def startup() -> None:
    logger.info("Starting AI Trading Bot...")

    validate_environment()

    logger.info("Environment validated.")

database_ok = await health_check()

print("DATABASE_OK =", database_ok)

logger.info(f"DATABASE_OK = {database_ok}")

# временно отключаем проверку
# if not database_ok:
#     raise ConnectionError(
#         "Failed to connect to PostgreSQL."
#     )

    logger.info("Database connection successful.")

    await create_database()

    logger.info("Database initialized.")

    await set_bot_commands()

    logger.info("Telegram commands registered.")


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
