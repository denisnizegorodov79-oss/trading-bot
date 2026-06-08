from __future__ import annotations

import aiohttp


async def get_btc_price() -> float:
    url = "https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            data = await response.json()

    return float(data["data"][0]["last"])
