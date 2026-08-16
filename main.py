from __future__ import annotations

import asyncio
import logging

from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from sqlalchemy import select, desc

from config import (
    TELEGRAM_TOKEN,
    LOG_LEVEL,
    LOG_FORMAT,
    validate_environment,
)

from database import (
    create_database,
    health_check,
    get_session,
)

from telegram_bot.handlers import router

from models.user import User
from models.user_settings import UserSettings
from models.auto_signal_log import AutoSignalLog
from models.trade import Trade

from services.market_data import get_btc_market_analysis


logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
)

logger = logging.getLogger(__name__)


bot = Bot(token=TELEGRAM_TOKEN)

dp = Dispatcher()
dp.include_router(router)


last_auto_signal: str | None = None

CIRCUIT_BREAKER_LOSSES = 3
CIRCUIT_BREAKER_COOLDOWN_HOURS = 6


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
    global last_auto_signal

    while True:
        await asyncio.sleep(300)

        try:
            analysis = await get_btc_market_analysis()

            current_price = analysis["last_price"]
            signal = analysis["signal"]
            confidence = analysis["confidence"]

            print(
                "AUTO_SIGNAL_CHECK:",
                signal,
                confidence,
            )

            # ==========================================
            # 1. ПРОВЕРКА И ЗАКРЫТИЕ OPEN-СДЕЛОК
            # ==========================================

            async with get_session() as session:
                result = await session.execute(
                    select(Trade).where(
                        Trade.asset == "BTC",
                        Trade.status == "OPEN",
                    )
                )

                open_trades = result.scalars().all()

                for trade in open_trades:

                    # Старые сделки со старой системой
                    # SL=5 / TP=10 не обрабатываем.
                    if (
                        trade.stop_loss_pct < 1000
                        or trade.take_profit_pct < 1000
                    ):
                        continue

                    result = await session.execute(
                        select(User).where(
                            User.id == trade.user_id
                        )
                    )

                    user = result.scalar_one_or_none()

                    if user is None:
                        continue

                    # TAKE PROFIT
                    if (
                        trade.take_profit_pct > 0
                        and current_price >= trade.take_profit_pct
                    ):
                        trade.status = "CLOSED"

                        trade.pnl = (
                            current_price - trade.price
                        ) * trade.quantity

                        user.balance += trade.pnl

                        await bot.send_message(
                            user.telegram_id,
                            "🎯 Take Profit достигнут\n\n"
                            f"Сделка #{trade.id} закрыта с прибылью.\n"
                            f"Цена входа: {trade.price:.2f} USDT\n"
                            f"Цена закрытия: {current_price:.2f} USDT\n"
                            f"PnL: {trade.pnl:.2f} USDT"
                        )

                        print(
                            "AUTO_TRADE_TP_CLOSED:",
                            trade.id,
                            trade.pnl,
                        )

                    # STOP LOSS
                    elif (
                        trade.stop_loss_pct > 0
                        and current_price <= trade.stop_loss_pct
                    ):
                        trade.status = "CLOSED"

                        trade.pnl = (
                            current_price - trade.price
                        ) * trade.quantity

                        user.balance += trade.pnl

                        await bot.send_message(
                            user.telegram_id,
                            "🛡 Stop Loss достигнут\n\n"
                            f"Сделка #{trade.id} закрыта с убытком.\n"
                            f"Цена входа: {trade.price:.2f} USDT\n"
                            f"Цена закрытия: {current_price:.2f} USDT\n"
                            f"PnL: {trade.pnl:.2f} USDT"
                        )

                        print(
                            "AUTO_TRADE_SL_CLOSED:",
                            trade.id,
                            trade.pnl,
                        )

                await session.commit()

            # ==========================================
            # 2. АВТООТКРЫТИЕ BUY-СДЕЛКИ
            # ==========================================

            if (
                "BUY" in signal
                and confidence >= 75
                and signal != last_auto_signal
            ):
                print(
                    "AUTO_TRADING_SIGNAL:",
                    signal,
                    confidence,
                )

                async with get_session() as session:

                    result = await session.execute(
                        select(User)
                    )

                    users = result.scalars().all()

                    for user in users:

                        # ----------------------------------
                        # Проверяем настройки пользователя
                        # ----------------------------------

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

                        # ----------------------------------
                        # Проверяем существующую OPEN сделку
                        # ----------------------------------

                        result = await session.execute(
                            select(Trade).where(
                                Trade.user_id == user.id,
                                Trade.asset == "BTC",
                                Trade.status == "OPEN",
                            )
                        )

                        open_trade = result.scalar_one_or_none()

                        if open_trade is not None:
                            print(
                                "AUTO_TRADE_SKIPPED_OPEN_EXISTS:",
                                user.id,
                                open_trade.id,
                            )
                            continue

                        # ==================================
                        # CIRCUIT BREAKER 2.0
                        # ==================================
                        #
                        # Берём только НОВЫЕ реальные сделки.
                        # LEGACY_TEST_TRADE полностью исключаем.
                        #
                        # Если три последних сделки убыточны,
                        # торговля ставится на паузу на 6 часов.
                        #
                        # После 6 часов торговля автоматически
                        # снова разрешается.
                        # ==================================

                        result = await session.execute(
                            select(Trade)
                            .where(
                                Trade.user_id == user.id,
                                Trade.status == "CLOSED",
                                Trade.rationale
                                != "LEGACY_TEST_TRADE",
                            )
                            .order_by(
                                desc(Trade.timestamp)
                            )
                            .limit(
                                CIRCUIT_BREAKER_LOSSES
                            )
                        )

                        last_closed_trades = (
                            result.scalars().all()
                        )

                        losing_streak = (
                            len(last_closed_trades)
                            == CIRCUIT_BREAKER_LOSSES
                            and all(
                                trade.pnl < 0
                                for trade
                                in last_closed_trades
                            )
                        )

                        if losing_streak:
                            last_loss_time = (
                                last_closed_trades[0].timestamp
                            )

                            cooldown_until = (
                                last_loss_time
                                + timedelta(
                                    hours=(
                                        CIRCUIT_BREAKER_COOLDOWN_HOURS
                                    )
                                )
                            )

                            now = datetime.utcnow()

                            if now < cooldown_until:
                                remaining = (
                                    cooldown_until - now
                                )

                                remaining_minutes = max(
                                    1,
                                    int(
                                        remaining.total_seconds()
                                        / 60
                                    ),
                                )

                                remaining_hours = (
                                    remaining_minutes // 60
                                )

                                remaining_minutes = (
                                    remaining_minutes % 60
                                )

                                await bot.send_message(
                                    user.telegram_id,
                                    "🛑 Circuit Breaker активирован\n\n"
                                    "3 последние реальные сделки "
                                    "были убыточными.\n\n"
                                    "Автоторговля временно "
                                    "приостановлена.\n"
                                    f"До восстановления: "
                                    f"{remaining_hours} ч "
                                    f"{remaining_minutes} мин.\n\n"
                                    "После окончания паузы бот "
                                    "автоматически снова сможет "
                                    "открывать сделки."
                                )

                                print(
                                    "CIRCUIT_BREAKER_ACTIVE:",
                                    user.id,
                                    cooldown_until,
                                )

                                continue

                            print(
                                "CIRCUIT_BREAKER_RESET:",
                                user.id,
                            )

                        # ----------------------------------
                        # Создание новой сделки
                        # ----------------------------------

                        trade = Trade(
                            user_id=user.id,
                            asset="BTC",
                            side="BUY",
                            price=current_price,
                            quantity=analysis[
                                "position_size"
                            ],
                            market_snapshot=(
                                f"signal={signal}; "
                                f"confidence={confidence}; "
                                f"rsi={analysis['rsi']:.2f}; "
                                f"ema20={analysis['ema20']:.2f}; "
                                f"ema50={analysis['ema50']:.2f}; "
                                f"macd={analysis.get('macd', 0):.2f}; "
                                f"macd_signal="
                                f"{analysis.get('macd_signal', 0):.2f}; "
                                f"atr={analysis['atr']:.2f}"
                            ),
                            trigger_news=None,
                            status="OPEN",
                            pnl=0.0,
                            confidence_score=confidence,
                            stop_loss_pct=analysis[
                                "stop_loss"
                            ],
                            take_profit_pct=analysis[
                                "take_profit"
                            ],
                            rationale=analysis[
                                "recommendation"
                            ],
                        )

                        session.add(trade)

                        await bot.send_message(
                            user.telegram_id,
                            "🤖 Демо-автоторговля\n\n"
                            "Открыта автоматическая "
                            "демо-сделка BTC.\n\n"
                            f"Цена входа: "
                            f"{current_price:.2f} USDT\n"
                            f"Размер позиции: "
                            f"{analysis['position_size']:.6f} BTC\n"
                            f"Stop Loss: "
                            f"{analysis['stop_loss']:.2f} USDT\n"
                            f"Take Profit: "
                            f"{analysis['take_profit']:.2f} USDT\n"
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

            # ==========================================
            # 3. АВТО-СИГНАЛЫ TELEGRAM
            # ==========================================

            if confidence < 70:
                continue

            if signal == last_auto_signal:
                continue

            async with get_session() as session:

                result = await session.execute(
                    select(User)
                )

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
                        "🔔 BTC ALERT\n\n"
                        f"Цена: {current_price:.2f} USDT\n"
                        f"Сигнал: {signal}\n"
                        f"Уверенность: {confidence}%\n\n"
                        f"{analysis['recommendation']}"
                    )

                    log = AutoSignalLog(
                        asset="BTC",
                        price=current_price,
                        signal=signal,
                        confidence=confidence,
                        recommendation=analysis[
                            "recommendation"
                        ],
                    )

                    session.add(log)

                last_auto_signal = signal

                await session.commit()

        except Exception as error:
            print(
                "AUTO_NOTIFICATION_ERROR:",
                repr(error),
            )


async def startup() -> None:
    logger.info(
        "Starting AI Trading Bot..."
    )

    validate_environment()

    logger.info(
        "Environment validated."
    )

    database_ok = await health_check()

    print(
        "DATABASE_OK =",
        database_ok,
    )

    logger.info(
        f"DATABASE_OK = {database_ok}"
    )

    logger.info(
        "Database connection check completed."
    )

    await create_database()

    logger.info(
        "Database initialized."
    )

    await set_bot_commands()

    logger.info(
        "Telegram commands registered."
    )

    asyncio.create_task(
        test_notification()
    )


async def shutdown() -> None:
    logger.info(
        "Stopping AI Trading Bot..."
    )

    await bot.session.close()

    logger.info(
        "Bot stopped."
    )


async def main() -> None:
    try:
        await startup()

        logger.info(
            "Bot polling started."
        )

        await dp.start_polling(bot)

    finally:
        await shutdown()


if __name__ == "__main__":
    asyncio.run(main())
