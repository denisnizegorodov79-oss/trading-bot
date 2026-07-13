from __future__ import annotations


def make_trading_decision(
    rsi: float,
    ema20: float,
    ema50: float,
) -> dict:
    if rsi < 35 and ema20 > ema50:
        signal = "BUY 🟢"
        confidence = 75
        recommendation = (
            "Цена выглядит перепроданной, "
            "тренд поддерживает покупку."
        )

    elif rsi > 70:
        signal = "SELL / WAIT 🔴"
        confidence = 70
        recommendation = (
            "RSI высокий, возможна коррекция."
        )

    elif ema20 > ema50:
        signal = "HOLD / BUY осторожно 🟡"
        confidence = 60
        recommendation = (
            "Тренд восходящий, "
            "но сильного сигнала нет."
        )

    else:
        signal = "WAIT ⚪"
        confidence = 50
        recommendation = (
            "Лучше дождаться более сильного сигнала."
        )

    return {
        "signal": signal,
        "confidence": confidence,
        "recommendation": recommendation,
    }
