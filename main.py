from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import BotCommand

from config import (
    LOG_FORMAT,
    LOG_LEVEL,
    TELEGRAM_TOKEN,
    validate_environment,
)
from database import (
    create_database,
    health_check,
)


logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
)

logger = logging.getLogger(__name__)


bot = Bot(
    token=TELEGRAM_TOKEN,
)

dp = Dispatcher()


async def set_bot_commands() -> None:
    """
    Установка команд Telegram.
    """

    commands = [
        BotCommand(
            command="start",
            description="Запустить бота",
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
    """
    Действия при запуске.
    """

    logger.info("Starting AI Trading Bot...")

    validate_environment()

    logger.info("Environment validation passed.")

    await create_database()

    logger.info("Database tables initialized.")

    database_ok = await health_check()

    if not database_ok:
        raise ConnectionError(
            "PostgreSQL connection failed."
        )

    logger.info("Database connection successful.")

    await set_bot_commands()

    logger.info("Telegram commands registered.")


async def shutdown() -> None:
    """
    Корректное завершение работы.
    """

    logger.info("Stopping AI Trading Bot...")

    await bot.session.close()

    logger.info("Bot stopped.")


async def main() -> None:
    """
    Точка входа.
    """

    try:
        await startup()

        logger.info("Bot polling started.")

        await dp.start_polling(bot)

    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
