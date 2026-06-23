from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from sqlalchemy import select, desc

from config import TELEGRAM_TOKEN, LOG_LEVEL, LOG_FORMAT, validate_environment
from database import create_database, health_check, get_session
from telegram_bot.handlers import router

from models.user import User
from models.user_settings import UserSettings
from models.auto_signal_log import AutoSignalLog
from models.trade import Trade

from services.market_data import get_btc_market_analysis


logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
dp.include_router(router)

last_auto_signal: str | None = None


async def set_bot_commands() -> None:
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="analysis", description="Анализ рынка"),
        BotCommand(command="demo", description="Демо торговля"),
        BotCommand(command="learning", description="Самообучение"),
        BotCommand(command="settings", description="Настройки"),
    ]

    await bot.set_my_commands(commands)


async def test_notification() -> None:
    global last_auto_signal

    while True:
        await asyncio.sleep(300)

        try:
            analysis = await get_btc_market_analysis()

            current_price = analysis["last_price"]
            signal = analysis["signal"]
            confidence = analysis["confidence"]

            print("AUTO_SIGNAL_CHECK:", signal, confidence)

            async with get_session() as session:
                result = await session.execute(
                    select(Trade).where(
                        Trade.asset == "BTC",
                        Trade.status == "OPEN",
                    )
                )

                open_trades = result.scalars().all()

                for trade in open_trades:
                    result = await session.execute(
                        select(User).where(User.id == trade.user_id)
                    )

                    user = result.scalar_one_or_none()

                    if user is None:
                        continue

                    if (
                        trade.take_profit_pct > 0
                        and current_price >= trade.take_profit_pct
                    ):
                        trade.status = "CLOSED"
                        trade.pnl = (current_price - trade.price) * trade.quantity
                        user.balance += trade.pnl

                        await bot.send_message(
                            user.telegram_id,
                            "🎯 Take Profit достигнут\n\n"
                            f"Сделка #{trade.id} закрыта с прибылью.\n"
                            f"Цена входа: {trade.price:.2f} USDT\n"
                            f"Цена закрытия: {current_price:.2f} USDT\n"
                            f"PnL: {trade.pnl:.2f} USDT"
                        )

                        print("AUTO_TRADE_TP_CLOSED:", trade.id, trade.pnl)

                    elif (
                        trade.stop_loss_pct > 0
                        and current_price <= trade.stop_loss_pct
                    ):
                        trade.status = "CLOSED"
                        trade.pnl = (current_price - trade.price) * trade.quantity
                        user.balance += trade.pnl

                        await bot.send_message(
                            user.telegram_id,
                            "🛡 Stop Loss достигнут\n\n"
                            f"Сделка #{trade.id} закрыта с убытком.\n"
                            f"Цена входа: {trade.price:.2f} USDT\n"
                            f"Цена закрытия: {current_price:.2f} USDT\n"
                            f"PnL: {trade.pnl:.2f} USDT"
                        )

                        print("AUTO_TRADE_SL_CLOSED:", trade.id, trade.pnl)

                await session.commit()

            if (
                "BUY" in signal
                and confidence >= 75
                and signal != last_auto_signal
            ):
                print("AUTO_TRADING_SIGNAL:", signal, confidence)

                async with get_session() as session:
                    result = await session.execute(select(User))
                    users = result.scalars().all()

                    for user in users:
                        result = await session.execute(
                            select(UserSettings).where(
                                UserSettings.user_id == user.id
                            )
                        )

                        settings = result.scalar_one_or_none()

                        if (
                            settings is None
                            or not settings.auto_signals_enabled
                        ):
                            continue

                        result = await session.execute(
                            select(Trade).where(
                                Trade.user_id == user.id,
                                Trade.asset == "BTC",
                                Trade.status == "OPEN",
                            )
                        )

                        open_trade = result.scalar_one_or_none()

                        if open_trade is not None:
                            continue

                        result = await session.execute(
                            select(Trade)
                            .where(
                                Trade.user_id == user.id,
                                Trade.status == "CLOSED",
                            )
                            .order_by(desc(Trade.timestamp))
                            .limit(3)
                        )

                        last_closed_trades = result.scalars().all()

                        losing_streak = (
                            len(last_closed_trades) == 3
                            and all(trade.pnl < 0 for trade in last_closed_trades)
                        )

                        if losing_streak:
                            await bot.send_message(
                                user.telegram_id,
                                "🛑 Circuit Breaker активирован\n\n"
                                "3 последние закрытые сделки были убыточными.\n"
                                "Автооткрытие новой сделки пропущено."
                            )
                            continue

                        trade = Trade(
                            user_id=user.id,
                            asset="BTC",
                            side="BUY",
                            price=current_price,
                            quantity=analysis["position_size"],
                            market_snapshot=(
                                f"signal={signal}; "
                                f"confidence={confidence}; "
                                f"rsi={analysis['rsi']:.2f}; "
                                f"ema20={analysis['ema20']:.2f}; "
                                f"ema50={analysis['ema50']:.2f}; "
                                f"atr={analysis['atr']:.2f}"
                            ),
                            trigger_news=None,
                            status="OPEN",
                            pnl=0.0,
                            confidence_score=confidence,
                            stop_loss_pct=analysis["stop_loss"],
                            take_profit_pct=analysis["take_profit"],
                            rationale=analysis["recommendation"],
                        )

                        session.add(trade)

                        await bot.send_message(
                            user.telegram_id,
                            "🤖 Демо-автоторговля\n\n"
                            "Открыта автоматическая демо-сделка BTC.\n\n"
                            f"Цена входа: {current_price:.2f} USDT\n"
                            f"Размер позиции: {analysis['position_size']:.6f} BTC\n"
                            f"Stop Loss: {analysis['stop_loss']:.2f} USDT\n"
                            f"Take Profit: {analysis['take_profit']:.2f} USDT\n"
                            f"Сигнал: {signal}\n"
                            f"Уверенность: {confidence}%"
                        )

                        print(
                            "AUTO_TRADE_OPENED:",
                            user.telegram_id,
                            signal,
                            confidence,
                        )

                    await session.commit()

            if confidence < 70:
                continue

            if signal == last_auto_signal:
                continue

            async with get_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()

                for user in users:
                    result = await session.execute(
                        select(UserSettings).where(
                            UserSettings.user_id == user.id
                        )
                    )

                    settings = result.scalar_one_or_none()

                    if (
                        settings is None
                        or not settings.auto_signals_enabled
                    ):
                        continue

                    await bot.send_message(
                        user.telegram_id,
                        f"🔔 BTC ALERT\n\n"
                        f"Цена: {current_price:.2f} USDT\n"
                        f"Сигнал: {signal}\n"
                        f"Уверенность: {confidence}%\n\n"
                        f"{analysis['recommendation']}"
                    )

                    last_auto_signal = signal

                    log = AutoSignalLog(
                        asset="BTC",
                        price=current_price,
                        signal=signal,
                        confidence=confidence,
                        recommendation=analysis["recommendation"],
                    )

                    session.add(log)

                await session.commit()

        except Exception as error:
            print("AUTO_NOTIFICATION_ERROR:", repr(error))


async def startup() -> None:
    logger.info("Starting AI Trading Bot...")

    validate_environment()

    logger.info("Environment validated.")

    database_ok = await health_check()

    print("DATABASE_OK =", database_ok)

    logger.info(f"DATABASE_OK = {database_ok}")
    logger.info("Database connection check completed.")

    await create_database()

    logger.info("Database initialized.")

    await set_bot_commands()

    logger.info("Telegram commands registered.")

    asyncio.create_task(test_notification())


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
