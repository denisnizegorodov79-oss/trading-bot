from services.market_data import get_btc_price
from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from sqlalchemy import select

from telegram_bot.keyboards import (
    MAIN_MENU_KEYBOARD,
    DEMO_MENU_KEYBOARD,
)

from database import get_session

from models.user import User
from models.trade import Trade
router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:

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

    await message.answer(
        text=(
            "🤖 AI Trading Bot\n\n"
            "Добро пожаловать в систему анализа и демо-трейдинга."
        ),
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
            await message.answer("Пользователь не найден.")
            return

    await message.answer(
        (
            "💹 Демо-счет\n\n"
            f"💰 Баланс: {user.balance} USDT\n"
            f"👤 Пользователь: {user.first_name}\n\n"
            "Выберите действие:"
        ),
        reply_markup=DEMO_MENU_KEYBOARD,
    )


@router.message(lambda message: message.text == "📈 Купить BTC")
async def buy_btc_handler(message: Message) -> None:

BTC_PRICE = await get_btc_price()
    BUY_AMOUNT_USDT = 1000

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

        if user.balance < BUY_AMOUNT_USDT:
            await message.answer(
                "❌ Недостаточно средств."
            )
            return

        btc_amount = BUY_AMOUNT_USDT / BTC_PRICE

        user.balance -= BUY_AMOUNT_USDT

        trade = Trade(
            user_id=user.id,
            asset="BTC",
            side="BUY",
            price=BTC_PRICE,
            quantity=btc_amount,
            market_snapshot="Demo BTC purchase",
            trigger_news=None,
            status="OPEN",
            pnl=0.0,
            confidence_score=90,
            stop_loss_pct=5.0,
            take_profit_pct=10.0,
            rationale="Demo purchase",
        )

        session.add(trade)

    await message.answer(
        f"✅ BTC куплен\n\n"
        f"Цена: {BTC_PRICE} USDT\n"
        f"Количество BTC: {btc_amount:.8f}\n"
        f"Новый баланс: {user.balance:.2f} USDT"
    )


@router.message(lambda message: message.text == "📉 Продать BTC")
async def sell_btc_handler(message: Message) -> None:

    BTC_PRICE = 100000

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

        result = await session.execute(
            select(Trade).where(
                Trade.user_id == user.id,
                Trade.asset == "BTC",
                Trade.status == "OPEN"
            )
        )

        trade = result.scalars().first()

        if trade is None:
            await message.answer(
                "❌ Открытых сделок BTC нет."
            )
            return

        sell_amount = trade.quantity * BTC_PRICE

        user.balance += sell_amount

        trade.status = "CLOSED"

        await message.answer(
            f"✅ BTC продан\n\n"
            f"Цена: {BTC_PRICE} USDT\n"
            f"Количество: {trade.quantity:.8f}\n"
            f"Получено: {sell_amount:.2f} USDT\n"
            f"Баланс: {user.balance:.2f} USDT"
        )


@router.message(lambda message: message.text == "📋 Мои сделки")
async def trades_handler(message: Message) -> None:

    async with get_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Пользователь не найден.")
            return

        result = await session.execute(
            select(Trade).where(
                Trade.user_id == user.id
            )
        )

        trades = result.scalars().all()

        if not trades:
            await message.answer(
                "📋 У вас пока нет сделок."
            )
            return

        text = "📋 Ваши сделки:\n\n"

        for trade in trades[-10:]:

            text += (
                f"🪙 {trade.asset}\n"
                f"📈 Тип: {trade.side}\n"
                f"💰 Цена: {trade.price}\n"
                f"📦 Количество: {trade.quantity}\n"
                f"📊 Статус: {trade.status}\n\n"
            )

        await message.answer(text)


@router.message(lambda message: message.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message) -> None:

    await message.answer(
        "Главное меню",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


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
