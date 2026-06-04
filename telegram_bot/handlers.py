from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from sqlalchemy import select

from telegram_bot.keyboards import MAIN_MENU_KEYBOARD

from database import get_session

from models.user import User
from models.trade import Trade


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """
    Обработчик команды /start
    """

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
            )

            session.add(user)

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

    await message.answer(
        "📊 Модуль анализа рынка находится в разработке."
    )


@router.message(lambda message: message.text == "💹 Демо-Торговля")
async def demo_trading_handler(message: Message) -> None:

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "Пользователь не найден."
            )
            return

        text = (
            "💹 Демо-счет\n\n"
            f"💰 Баланс: {user.balance} USDT\n"
            f"🆔 Пользователь: {user.first_name}\n\n"
            "Демо-торговля готова к работе."
        )

        await message.answer(text)
async def demo_trading_handler(message: Message) -> None:

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            await message.answer(
                "Пользователь не найден."
            )
            return

        trades_result = await session.execute(
            select(Trade).where(
                Trade.user_id == user.id
            )
        )

        trades = trades_result.scalars().all()

        total_trades = len(trades)

        open_trades = len(
            [
                trade
                for trade in trades
                if trade.status == "OPEN"
            ]
        )

        closed_trades = len(
            [
                trade
                for trade in trades
                if trade.status == "CLOSED"
            ]
        )

        text = (
            "💹 Демо-счет\n\n"
            f"💰 Баланс: {user.balance} USDT\n"
            f"📈 Всего сделок: {total_trades}\n"
            f"🟢 Открытых: {open_trades}\n"
            f"🔴 Закрытых: {closed_trades}"
        )

        await message.answer(text)


@router.message(lambda message: message.text == "🧠 Самообучение")
async def self_learning_handler(message: Message) -> None:

    await message.answer(
        "🧠 Модуль самообучения находится в разработке."
    )


@router.message(lambda message: message.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:

    await message.answer(
        "⚙️ Модуль настроек находится в разработке."
    )
