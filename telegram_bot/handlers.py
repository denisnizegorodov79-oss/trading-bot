from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from telegram_bot.keyboards import MAIN_MENU_KEYBOARD


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """
    Обработчик команды /start
    """

    welcome_text = (
        "🤖 AI Trading Bot\n\n"
        "Добро пожаловать в систему анализа и демо-трейдинга.\n\n"
        "Выберите необходимый раздел в меню ниже."
    )

    await message.answer(
        text=welcome_text,
        reply_markup=MAIN_MENU_KEYBOARD,
    )


@router.message(lambda message: message.text == "📊 Анализ")
async def analysis_handler(message: Message) -> None:
    """
    Анализ рынка
    """

    await message.answer(
        "📊 Модуль анализа рынка находится в разработке."
    )


@router.message(lambda message: message.text == "💹 Демо-Торговля")
async def demo_trading_handler(message: Message) -> None:
    """
    Демо торговля
    """

    await message.answer(
        "💹 Модуль демо-торговли находится в разработке."
    )


@router.message(lambda message: message.text == "🧠 Самообучение")
async def self_learning_handler(message: Message) -> None:
    """
    Самообучение
    """

    await message.answer(
        "🧠 Модуль самообучения находится в разработке."
    )


@router.message(lambda message: message.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    """
    Настройки
    """

    await message.answer(
        "⚙️ Модуль настроек находится в разработке."
    )
