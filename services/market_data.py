import aiohttp


async def get_btc_price() -> float:
    """
    Получение текущей цены BTCUSDT с Binance.
    """

    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            data = await response.json()

            return float(data["price"])
