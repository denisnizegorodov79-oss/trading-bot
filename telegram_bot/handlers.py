from __future__ import annotations

from services.market_data import (
    get_btc_price,
    get_btc_market_analysis,
)

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from sqlalchemy import select

from telegram_bot.keyboards import (
    MAIN_MENU_KEYBOARD,
    DEMO_MENU_KEYBOARD,
)

from database import get_session
from models.auto_signal_log import AutoSignalLog
from models.user import User
from models.trade import Trade
from models.market_signal import MarketSignal
from models.user_settings import UserSettings

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
    await message.answer("⏳ Получаю анализ BTC...")

    try:
        analysis = await get_btc_market_analysis()

        text = (
            "📊 Анализ BTC/USDT\n\n"
            f"💰 Цена: {analysis['last_price']:.2f} USDT\n"
            f"📈 Изменение 24ч: {analysis['change_24h']:.2f}%\n"
            f"🔼 Максимум 24ч: {analysis['high_24h']:.2f} USDT\n"
            f"🔽 Минимум 24ч: {analysis['low_24h']:.2f} USDT\n"
            f"📊 Объём 24ч: {analysis['volume_24h']:.2f} USDT\n\n"
            f"RSI: {analysis['rsi']:.2f}\n"
            f"EMA20: {analysis['ema20']:.2f}\n"
            f"EMA50: {analysis['ema50']:.2f}\n"
            f"ATR: {analysis['atr']:.2f}\n\n"
            f"🛡 Stop Loss: {analysis['stop_loss']:.2f} USDT\n"
            f"🎯 Take Profit: {analysis['take_profit']:.2f} USDT\n"
            f"📦 Размер позиции: {analysis['position_size']:.6f} BTC\n\n"
            f"Сигнал: {analysis['signal']}\n"
            f"Уверенность: {analysis['confidence']}%\n\n"
            f"Рекомендация:\n{analysis['recommendation']}"
        )

        await message.answer(text)

    except Exception as error:
        print("ANALYSIS_ERROR:", repr(error))

        await message.answer(
            "❌ Не удалось получить анализ BTC.\n\n"
            "Проверь Railway Logs, там будет ANALYSIS_ERROR."
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
            f"💰 Баланс: {user.balance:.2f} USDT\n"
            f"👤 Пользователь: {user.first_name}\n\n"
            "Выберите действие:"
        ),
        reply_markup=DEMO_MENU_KEYBOARD,
    )


@router.message(lambda message: message.text == "📈 Купить BTC")
async def buy_btc_handler(message: Message) -> None:
    analysis = await get_btc_market_analysis()

    btc_price = analysis["last_price"]
    buy_amount_usdt = 1000
    btc_amount = buy_amount_usdt / btc_price

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

        if user.balance < buy_amount_usdt:
            await message.answer("❌ Недостаточно средств.")
            return

        result = await session.execute(
            select(Trade).where(
                Trade.user_id == user.id,
                Trade.status == "CLOSED",
                Trade.rationale != "LEGACY_TEST_TRADE",
            )
        )

        closed_trades = result.scalars().all()
        last_closed_trades = closed_trades[-3:]

        losing_streak = (
            len(last_closed_trades) == 3
            and all(trade.pnl < 0 for trade in last_closed_trades)
        )

        if losing_streak:
            await message.answer(
                "🛑 Circuit Breaker активирован\n\n"
                "У вас 3 убыточные сделки подряд.\n"
                "Новые покупки временно заблокированы.\n\n"
                "Рекомендуется остановиться и пересмотреть стратегию."
            )
            return

        user.balance -= buy_amount_usdt

        market_snapshot = (
            f"price={analysis['last_price']:.2f}; "
            f"change_24h={analysis['change_24h']:.2f}; "
            f"rsi={analysis['rsi']:.2f}; "
            f"ema20={analysis['ema20']:.2f}; "
            f"ema50={analysis['ema50']:.2f}; "
            f"atr={analysis['atr']:.2f}; "
            f"signal={analysis['signal']}; "
            f"confidence={analysis['confidence']}"
        )

        trade = Trade(
            user_id=user.id,
            asset="BTC",
            side="BUY",
            price=btc_price,
            quantity=btc_amount,
            market_snapshot=market_snapshot,
            trigger_news=None,
            status="OPEN",
            pnl=0.0,
            confidence_score=analysis["confidence"],
            stop_loss_pct=analysis["stop_loss"],
            take_profit_pct=analysis["take_profit"],
            rationale=analysis["recommendation"],
        )

        session.add(trade)

        new_balance = user.balance

    await message.answer(
        f"✅ BTC куплен\n\n"
        f"Цена: {btc_price:.2f} USDT\n"
        f"Количество BTC: {btc_amount:.8f}\n"
        f"Новый баланс: {new_balance:.2f} USDT\n\n"
        f"📊 Сигнал: {analysis['signal']}\n"
        f"RSI: {analysis['rsi']:.2f}\n"
        f"EMA20: {analysis['ema20']:.2f}\n"
        f"EMA50: {analysis['ema50']:.2f}\n"
        f"ATR: {analysis['atr']:.2f}\n\n"
        f"🛡 Stop Loss: {analysis['stop_loss']:.2f} USDT\n"
        f"🎯 Take Profit: {analysis['take_profit']:.2f} USDT\n\n"
        f"Уверенность: {analysis['confidence']}%\n\n"
        f"Причина:\n{analysis['recommendation']}"
    )


@router.message(lambda message: message.text == "📉 Продать BTC")
async def sell_btc_handler(message: Message) -> None:
    btc_price = await get_btc_price()

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
                Trade.user_id == user.id,
                Trade.asset == "BTC",
                Trade.status == "OPEN",
            )
        )

        trade = result.scalars().first()

        if trade is None:
            await message.answer("❌ Открытых сделок BTC нет.")
            return

        sell_amount = trade.quantity * btc_price
        buy_amount = trade.quantity * trade.price
        pnl = sell_amount - buy_amount

        user.balance += sell_amount

        trade.status = "CLOSED"
        trade.pnl = pnl

        new_balance = user.balance
        buy_price = trade.price
        quantity = trade.quantity

    pnl_icon = "🟢" if pnl >= 0 else "🔴"

    await message.answer(
        f"✅ BTC продан\n\n"
        f"Цена покупки: {buy_price:.2f} USDT\n"
        f"Цена продажи: {btc_price:.2f} USDT\n"
        f"Количество: {quantity:.8f} BTC\n"
        f"Получено: {sell_amount:.2f} USDT\n"
        f"{pnl_icon} PnL: {pnl:.2f} USDT\n\n"
        f"Баланс: {new_balance:.2f} USDT"
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
            await message.answer("📋 У вас пока нет сделок.")
            return

        text = "📋 Ваши последние сделки:\n\n"

        for trade in trades[-10:]:
            pnl_icon = "🟢" if trade.pnl > 0 else "🔴" if trade.pnl < 0 else "⚪"

            text += (
                f"#{trade.id} 🪙 {trade.asset}\n"
                f"📌 Статус: {trade.status}\n"
                f"📈 Тип: {trade.side}\n"
                f"💰 Цена входа: {trade.price:.2f} USDT\n"
                f"📦 Количество: {trade.quantity:.8f} BTC\n"
                f"{pnl_icon} PnL: {trade.pnl:.2f} USDT\n"
                f"🤖 Уверенность: {trade.confidence_score}%\n"
            )

            if trade.rationale:
                text += f"🧠 Причина: {trade.rationale}\n"

            text += "\n"

        await message.answer(text)


@router.message(lambda message: message.text == "⬅️ Главное меню")
async def back_to_main_menu(message: Message) -> None:
    await message.answer(
        "Главное меню",
        reply_markup=MAIN_MENU_KEYBOARD,
    )


@router.message(lambda message: message.text == "🧠 Самообучение")
async def self_learning_handler(message: Message) -> None:
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

        real_trades = [
            trade
            for trade in trades
            if trade.rationale != "LEGACY_TEST_TRADE"
        ]

        if not real_trades:
            await message.answer(
                "🧠 Самообучение 3.0\n\n"
                "Пока нет новых сделок для анализа.\n"
                "Старые тестовые сделки исключены из статистики."
            )
            return

        closed_trades = [
            trade
            for trade in real_trades
            if trade.status == "CLOSED"
        ]

        profitable_trades = [
            trade
            for trade in closed_trades
            if trade.pnl > 0
        ]

        losing_trades = [
            trade
            for trade in closed_trades
            if trade.pnl < 0
        ]

        total_trades = len(real_trades)
        closed_count = len(closed_trades)
        open_count = total_trades - closed_count
        profitable_count = len(profitable_trades)
        losing_count = len(losing_trades)

        total_pnl = sum(trade.pnl for trade in closed_trades)
        total_confidence = sum(
            trade.confidence_score
            for trade in real_trades
        )

        average_confidence = (
            total_confidence / total_trades
            if total_trades > 0
            else 0
        )

        if closed_count > 0:
            win_rate = profitable_count / closed_count * 100
            average_pnl = total_pnl / closed_count
            best_pnl = max(trade.pnl for trade in closed_trades)
            worst_pnl = min(trade.pnl for trade in closed_trades)
        else:
            win_rate = 0
            average_pnl = 0
            best_pnl = 0
            worst_pnl = 0

        result = await session.execute(
            select(AutoSignalLog)
        )

        auto_signals = result.scalars().all()

        total_auto_signals = len(auto_signals)

        buy_signals = len([
            signal
            for signal in auto_signals
            if "BUY" in signal.signal
        ])

        sell_signals = len([
            signal
            for signal in auto_signals
            if "SELL" in signal.signal
        ])

        hold_signals = len([
            signal
            for signal in auto_signals
            if "HOLD" in signal.signal or "WAIT" in signal.signal
        ])

        if total_auto_signals > 0:
            avg_signal_confidence = sum(
                signal.confidence
                for signal in auto_signals
            ) / total_auto_signals

            last_signal = auto_signals[-1]
            last_signal_text = (
                f"{last_signal.signal} "
                f"({last_signal.confidence}%)"
            )
        else:
            avg_signal_confidence = 0
            last_signal_text = "Нет данных"

        await message.answer(
            "🧠 Самообучение 3.0\n\n"
            "📈 Сделки\n"
            f"📊 Всего новых сделок: {total_trades}\n"
            f"🟢 Открытых: {open_count}\n"
            f"✅ Закрытых: {closed_count}\n"
            f"🏆 Прибыльных: {profitable_count}\n"
            f"🔴 Убыточных: {losing_count}\n"
            f"🎯 Win Rate: {win_rate:.2f}%\n\n"
            f"💰 Общий PnL: {total_pnl:.2f} USDT\n"
            f"📈 Средний PnL: {average_pnl:.2f} USDT\n"
            f"🚀 Лучшая сделка: {best_pnl:.2f} USDT\n"
            f"⚠️ Худшая сделка: {worst_pnl:.2f} USDT\n"
            f"🤖 Средняя уверенность сделок: {average_confidence:.2f}%\n\n"
            "🔔 Авто-сигналы\n"
            f"Всего сигналов: {total_auto_signals}\n"
            f"🟢 BUY: {buy_signals}\n"
            f"🔴 SELL: {sell_signals}\n"
            f"🟡 HOLD / WAIT: {hold_signals}\n"
            f"Средняя уверенность: {avg_signal_confidence:.2f}%\n"
            f"Последний сигнал: {last_signal_text}\n\n"
            "Старые тестовые сделки LEGACY_TEST_TRADE "
            "исключены из статистики."
        )


@router.message(lambda message: message.text == "🔔 Авто-сигналы")
async def auto_signals_handler(message: Message) -> None:
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
            select(UserSettings).where(
                UserSettings.user_id == user.id
            )
        )

        settings = result.scalar_one_or_none()

        if settings is None:
            settings = UserSettings(
                user_id=user.id,
                auto_signals_enabled=True,
            )

            session.add(settings)

        else:
            settings.auto_signals_enabled = not settings.auto_signals_enabled

        status = (
            "ВКЛЮЧЕНЫ ✅"
            if settings.auto_signals_enabled
            else "ВЫКЛЮЧЕНЫ ❌"
        )

    await message.answer(
        "🔔 Авто-сигналы\n\n"
        f"Статус: {status}\n\n"
        "Теперь бот будет использовать эту настройку "
        "для будущих автоматических уведомлений по BTC."
    )


@router.message(lambda message: message.text == "🔔 Проверить сигнал")
async def check_signal_handler(message: Message) -> None:
    analysis = await get_btc_market_analysis()

    signal = analysis["signal"]
    confidence = analysis["confidence"]

    if "BUY" in signal and confidence >= 70:
        await message.answer(
            "🟢 Сильный сигнал BTC\n\n"
            f"Цена: {analysis['last_price']:.2f} USDT\n"
            f"Уверенность: {confidence}%\n\n"
            f"{analysis['recommendation']}"
        )

    elif "SELL" in signal and confidence >= 70:
        await message.answer(
            "🔴 Сильный сигнал BTC\n\n"
            f"Цена: {analysis['last_price']:.2f} USDT\n"
            f"Уверенность: {confidence}%\n\n"
            f"{analysis['recommendation']}"
        )

    else:
        await message.answer(
            "🟡 Сильного сигнала сейчас нет.\n\n"
            f"Текущий сигнал: {signal}\n"
            f"Уверенность: {confidence}%"
        )


@router.message(lambda message: message.text == "📊 Статистика сигналов")
async def signal_stats_handler(message: Message) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(AutoSignalLog)
        )

        signals = result.scalars().all()

        if not signals:
            await message.answer(
                "📊 Статистика сигналов\n\n"
                "Пока нет сохранённых авто-сигналов."
            )
            return

        total_signals = len(signals)

        buy_count = len([
            signal for signal in signals
            if "BUY" in signal.signal
        ])

        sell_count = len([
            signal for signal in signals
            if "SELL" in signal.signal
        ])

        wait_count = len([
            signal for signal in signals
            if "WAIT" in signal.signal or "HOLD" in signal.signal
        ])

        average_confidence = sum(
            signal.confidence
            for signal in signals
        ) / total_signals

        last_signal = signals[-1]

        await message.answer(
            "📊 Статистика авто-сигналов\n\n"
            f"Всего сигналов: {total_signals}\n\n"
            f"🟢 BUY: {buy_count}\n"
            f"🔴 SELL: {sell_count}\n"
            f"🟡 HOLD / WAIT: {wait_count}\n\n"
            f"Средняя уверенность: {average_confidence:.2f}%\n\n"
            f"Последний сигнал:\n"
            f"{last_signal.signal}\n"
            f"Уверенность: {last_signal.confidence}%\n"
            f"Цена: {last_signal.price:.2f} USDT"
        )


@router.message(lambda message: message.text == "⚙️ Настройки")
async def settings_handler(message: Message) -> None:
    await message.answer(
        "⚙️ Модуль настроек находится в разработке."
    )
