import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан в переменных окружения")

    # DeepSeek API
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY не задан в переменных окружения")
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_MAX_TOKENS: int = 2000
    DEEPSEEK_TEMPERATURE: float = 0.3

    # PostgreSQL (Railway)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не задан в переменных окружения")

    # Twitter API v2
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    TWITTER_USER_IDS: dict = {
        "realDonaldTrump": "25073877",
        "elonmusk": "44196397",
        "federalreserve": "108114995",
        "saylor": "23060680",
        "VitalikButerin": "11893397",
        "tier10k": "145334466",
        "whale_alert": "14225813"
    }
    TWITTER_WEIGHTS: dict = {
        "realDonaldTrump": 1.0,
        "elonmusk": 1.0,
        "federalreserve": 1.0,
        "saylor": 1.0,
        "VitalikButerin": 0.8,
        "tier10k": 1.0,
        "whale_alert": 1.0
    }

    # Telegram Client API (Pyrogram)
    TELEGRAM_API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE_NUMBER: str = os.getenv("TELEGRAM_PHONE_NUMBER", "")
    TELEGRAM_CHANNELS: list = [
        "Tier10k_ru",
        "crypto_headlines",
        "whales_grail"
    ]

    # Reddit API (PRAW)
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = "trading_bot/1.0"
    REDDIT_SUBREDDITS: list = ["CryptoCurrency", "dogecoin"]

    # RSS-парсеры бирж
    RSS_FEEDS: dict = {
        "binance": "https://www.binance.com/en/support/announcement/rss",
        "bybit": "https://announcements.bybit.com/rss",
        "okx": "https://www.okx.com/support/rss",
        "coinbase": "https://www.coinbase.com/blog/rss"
    }

    # CryptoQuant API
    CRYPTOQUANT_API_KEY: str = os.getenv("CRYPTOQUANT_API_KEY", "")
    CRYPTOQUANT_BASE_URL: str = "https://api.cryptoquant.com/v1"

    # Glassnode API
    GLASSNODE_API_KEY: str = os.getenv("GLASSNODE_API_KEY", "")
    GLASSNODE_BASE_URL: str = "https://api.glassnode.com/v1"

    # Investing.com (парсинг без API)
    MACRO_CALENDAR_URL: str = "https://www.investing.com/economic-calendar/"
    MACRO_HOLD_MINUTES_BEFORE: int = 10
    MACRO_HOLD_MINUTES_AFTER: int = 10

    # SEC EDGAR API
    SEC_EDGAR_BASE_URL: str = "https://www.sec.gov/edgar/sec-api"

    # WebSocket биржи (ccxt.pro)
    EXCHANGES: dict = {
        "bybit": {
            "api_key": os.getenv("BYBIT_API_KEY", ""),
            "api_secret": os.getenv("BYBIT_API_SECRET", "")
        },
        "binance": {
            "api_key": os.getenv("BINANCE_API_KEY", ""),
            "api_secret": os.getenv("BINANCE_API_SECRET", "")
        },
        "okx": {
            "api_key": os.getenv("OKX_API_KEY", ""),
            "api_secret": os.getenv("OKX_API_SECRET", ""),
            "api_passphrase": os.getenv("OKX_API_PASSPHRASE", "")
        }
    }
    SYMBOLS: list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "DOGE/USDT"]

    # Риск-менеджмент
    RISK_PERCENT_PER_TRADE: float = 0.01
    CIRCUIT_BREAKER_LOSSES: int = 3
    CIRCUIT_BREAKER_HOURS: int = 24
    MAX_DAILY_TRADES: int = 10

    # Параметры ATR (Average True Range)
    ATR_PERIOD: int = 14
    ATR_MULTIPLIER_SL: float = 2.0
    ATR_MULTIPLIER_TP: float = 3.0

    # Order Flow Imbalance (OFI)
    OFI_DEPTH_LEVELS: int = 10

    # Детекция фаз рынка
    TREND_THRESHOLD: float = 0.02

    # Самообучение
    FEEDBACK_LOOP_WEEKDAY: int = 6
    FEEDBACK_LOOP_HOUR: int = 0

    # База данных
    DB_TABLE_TRADES: str = "trades"
    DB_TABLE_ERRORS: str = "historical_errors"

config = Config()
