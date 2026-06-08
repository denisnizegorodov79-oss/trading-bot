from __future__ import annotations

import aiohttp


async def get_btc_price() -> float:
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            data = await response.json()

    return float(data["data"][0]["last"])


async def get_btc_market_analysis() -> dict:
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            data = await response.json()

    ticker = data["data"][0]

    last_price = float(ticker["last"])
    open_24h = float(ticker["open24h"])
    high_24h = float(ticker["high24h"])
    low_24h = float(ticker["low24h"])
    volume_24h = float(ticker["volCcy24h"])

    change_24h = ((last_price - open_24h) / open_24h) * 100

    if change_24h > 1:
        trend = "Восходящий 📈"
        recommendation = "Покупка возможна, но с контролем риска 🟢"
    elif change_24h < -1:
        trend = "Нисходящий 📉"
        recommendation = "Лучше не спешить с покупкой 🔴"
    else:
        trend = "Боковой ➡️"
        recommendation = "Рынок без явного направления 🟡"

    return {
        "last_price": last_price,
        "open_24h": open_24h,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "volume_24h": volume_24h,
        "change_24h": change_24h,
        "trend": trend,
        "recommendation": recommendation,
    }
