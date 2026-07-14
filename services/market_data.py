from __future__ import annotations

import aiohttp
from services.trading_engine import make_trading_decision

async def get_btc_price() -> float:
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            data = await response.json()

    return float(data["data"][0]["last"])


async def get_btc_candles() -> list[float]:
    url = "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1H&limit=100"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            data = await response.json()

    candles = data["data"]

    closes = [
        float(candle[4])
        for candle in reversed(candles)
    ]

    return closes


def calculate_ema(prices: list[float], period: int) -> float:
    multiplier = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema

    return ema
def calculate_ema_series(
    prices: list[float],
    period: int,
) -> list[float]:
    if not prices:
        return []

    multiplier = 2 / (period + 1)
    ema_values = [prices[0]]

    for price in prices[1:]:
        next_ema = (
            (price - ema_values[-1]) * multiplier
            + ema_values[-1]
        )

        ema_values.append(next_ema)

    return ema_values


def calculate_macd(
    prices: list[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[float, float, float]:
    if len(prices) < slow_period + signal_period:
        return 0.0, 0.0, 0.0

    fast_ema = calculate_ema_series(
        prices,
        fast_period,
    )

    slow_ema = calculate_ema_series(
        prices,
        slow_period,
    )

    macd_values = [
        fast_value - slow_value
        for fast_value, slow_value in zip(
            fast_ema,
            slow_ema,
        )
    ]

    signal_values = calculate_ema_series(
        macd_values,
        signal_period,
    )

    macd = macd_values[-1]
    macd_signal = signal_values[-1]
    macd_histogram = macd - macd_signal

    return macd, macd_signal, macd_histogram

def calculate_rsi(prices: list[float], period: int = 14) -> float:
    gains = []
    losses = []

    for index in range(1, period + 1):
        change = prices[index] - prices[index - 1]

        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    average_gain = sum(gains) / period
    average_loss = sum(losses) / period

    if average_loss == 0:
        return 100.0

    rs = average_gain / average_loss
    return 100 - (100 / (1 + rs))


def calculate_atr(prices: list[float], period: int = 14) -> float:
    ranges = []

    for index in range(1, len(prices)):
        ranges.append(
            abs(prices[index] - prices[index - 1])
        )

    if len(ranges) < period:
        return 0.0

    return sum(ranges[-period:]) / period


async def get_btc_market_analysis() -> dict:
    ticker_url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(ticker_url, timeout=10) as response:
            data = await response.json()

    ticker = data["data"][0]

    last_price = float(ticker["last"])
    open_24h = float(ticker["open24h"])
    high_24h = float(ticker["high24h"])
    low_24h = float(ticker["low24h"])
    volume_24h = float(ticker["volCcy24h"])

    change_24h = ((last_price - open_24h) / open_24h) * 100

    closes = await get_btc_candles()

    rsi = calculate_rsi(closes)
    ema20 = calculate_ema(closes[-20:], 20)
    ema50 = calculate_ema(closes[-50:], 50)
    atr = calculate_atr(closes)
    
    stop_loss = last_price - (atr * 1.5)
    take_profit = last_price + (atr * 3)
    risk_per_trade_pct = 1

    risk_amount = 100

    position_size = (
    risk_amount /
    abs(last_price - stop_loss)
    )
    
    decision = make_trading_decision(
        rsi=rsi,
        ema20=ema20,
        ema50=ema50,
    )

    signal = decision["signal"]
    confidence = decision["confidence"]
    recommendation = decision["recommendation"]

    return {
        "last_price": last_price,
        "open_24h": open_24h,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "volume_24h": volume_24h,
        "change_24h": change_24h,
        "rsi": rsi,
        "ema20": ema20,
        "ema50": ema50,
        "atr": atr,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size": position_size,
        "signal": signal,
        "confidence": confidence,
        "recommendation": recommendation,
    }
