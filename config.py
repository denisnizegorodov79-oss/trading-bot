from __future__ import annotations

import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()


def get_required_env(variable_name: str) -> str:
    """
    Получить обязательную переменную окружения.
    """

    value = os.getenv(variable_name)

    if value is None or not value.strip():
        raise ValueError(
            f"Environment variable '{variable_name}' is required."
        )

    return value


# ============================================================
# SYSTEM
# ============================================================

ENVIRONMENT: Final[str] = os.getenv(
    "ENVIRONMENT",
    "production"
)

DEBUG: Final[bool] = os.getenv(
    "DEBUG",
    "False"
).lower() == "true"

LOG_LEVEL: Final[str] = os.getenv(
    "LOG_LEVEL",
    "INFO"
).upper()

LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


# ============================================================
# TELEGRAM BOT
# ============================================================

TELEGRAM_TOKEN: Final[str] = get_required_env(
    "TELEGRAM_TOKEN"
)


# ============================================================
# TELEGRAM USERBOT (PYROGRAM)
# ============================================================

TELEGRAM_API_ID: Final[int] = int(
    get_required_env("TELEGRAM_API_ID")
)

TELEGRAM_API_HASH: Final[str] = get_required_env(
    "TELEGRAM_API_HASH"
)

TELEGRAM_SESSION_NAME: Final[str] = os.getenv(
    "TELEGRAM_SESSION_NAME",
    "ai_trading_session"
)

TELEGRAM_PHONE_NUMBER: Final[str] = os.getenv(
    "TELEGRAM_PHONE_NUMBER",
    ""
)


# ============================================================
# POSTGRESQL / RAILWAY
# ============================================================

DATABASE_URL: Final[str] = get_required_env(
    "DATABASE_URL"
)

DB_POOL_SIZE: Final[int] = int(
    os.getenv("DB_POOL_SIZE", "10")
)

DB_MAX_OVERFLOW: Final[int] = int(
    os.getenv("DB_MAX_OVERFLOW", "20")
)

DB_POOL_TIMEOUT: Final[int] = int(
    os.getenv("DB_POOL_TIMEOUT", "30")
)


# ============================================================
# DEEPSEEK
# ============================================================

DEEPSEEK_API_KEY: Final[str] = get_required_env(
    "DEEPSEEK_API_KEY"
)

DEEPSEEK_BASE_URL: Final[str] = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com"
)

DEEPSEEK_MODEL: Final[str] = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-chat"
)

DEEPSEEK_MAX_TOKENS: Final[int] = int(
    os.getenv("DEEPSEEK_MAX_TOKENS", "2000")
)

DEEPSEEK_TEMPERATURE: Final[float] = float(
    os.getenv("DEEPSEEK_TEMPERATURE", "0.3")
)


# ============================================================
# TWITTER / X
# ============================================================

TWITTER_BEARER_TOKEN: Final[str] = get_required_env(
    "TWITTER_BEARER_TOKEN"
)

TWITTER_USER_IDS: Final[dict[str, str]] = {
    "realDonaldTrump": "25073877",
    "elonmusk": "44196397",
    "federalreserve": "108114995",
    "saylor": "23060680",
    "VitalikButerin": "11893397",
    "tier10k": "145334466",
    "whale_alert": "14225813",
}

TWITTER_WEIGHTS: Final[dict[str, float]] = {
    "realDonaldTrump": 1.0,
    "elonmusk": 1.0,
    "federalreserve": 1.0,
    "saylor": 1.0,
    "VitalikButerin": 0.8,
    "tier10k": 1.0,
    "whale_alert": 1.0,
}


# ============================================================
# TELEGRAM CHANNELS
# ============================================================

TELEGRAM_CHANNELS: Final[tuple[str, ...]] = (
    "tier10k_ru",
    "crypto_headlines",
    "whales_grail",
)


# ============================================================
# REDDIT
# ============================================================

REDDIT_CLIENT_ID: Final[str] = get_required_env(
    "REDDIT_CLIENT_ID"
)

REDDIT_CLIENT_SECRET: Final[str] = get_required_env(
    "REDDIT_CLIENT_SECRET"
)

REDDIT_USER_AGENT: Final[str] = os.getenv(
    "REDDIT_USER_AGENT",
    "ai_trading_bot/1.0"
)

REDDIT_SUBREDDITS: Final[tuple[str, ...]] = (
    "CryptoCurrency",
    "dogecoin",
)


# ============================================================
# CRYPTOQUANT
# ============================================================

CRYPTOQUANT_API_KEY: Final[str] = get_required_env(
    "CRYPTOQUANT_API_KEY"
)

CRYPTOQUANT_BASE_URL: Final[str] = (
    "https://api.cryptoquant.com"
)


# ============================================================
# GLASSNODE
# ============================================================

GLASSNODE_API_KEY: Final[str] = os.getenv(
    "GLASSNODE_API_KEY",
    ""
)

GLASSNODE_BASE_URL: Final[str] = (
    "https://api.glassnode.com"
)


# ============================================================
# SEC EDGAR
# ============================================================

SEC_EDGAR_BASE_URL: Final[str] = (
    "https://data.sec.gov"
)


# ============================================================
# INVESTING.COM
# ============================================================

MACRO_CALENDAR_URL: Final[str] = (
    "https://www.investing.com/economic-calendar/"
)

MACRO_HOLD_MINUTES_BEFORE: Final[int] = 10
MACRO_HOLD_MINUTES_AFTER: Final[int] = 10


# ============================================================
# RSS LISTINGS
# ============================================================

RSS_FEEDS: Final[dict[str, str]] = {
    "binance": "https://www.binance.com/en/support/announcement/rss",
    "bybit": "https://announcements.bybit.com/rss",
    "okx": "https://www.okx.com/support/rss",
    "coinbase": "https://www.coinbase.com/blog/rss",
}


# ============================================================
# EXCHANGES
# ============================================================

EXCHANGES: Final[dict[str, dict[str, str]]] = {
    "binance": {
        "api_key": os.getenv("BINANCE_API_KEY", ""),
        "api_secret": os.getenv("BINANCE_API_SECRET", ""),
    },
    "bybit": {
        "api_key": os.getenv("BYBIT_API_KEY", ""),
        "api_secret": os.getenv("BYBIT_API_SECRET", ""),
    },
    "okx": {
        "api_key": os.getenv("OKX_API_KEY", ""),
        "api_secret": os.getenv("OKX_API_SECRET", ""),
        "api_passphrase": os.getenv(
            "OKX_API_PASSPHRASE",
            ""
        ),
    },
}


# ============================================================
# TRADING ASSETS
# ============================================================

TRADING_ASSETS: Final[tuple[str, ...]] = (
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "DOGE/USDT",
)


# ============================================================
# DEMO ACCOUNT
# ============================================================

DEFAULT_DEMO_BALANCE: Final[float] = 10000.0

BASE_CURRENCY: Final[str] = "USDT"


# ============================================================
# RISK MANAGEMENT
# ============================================================

RISK_PERCENT_PER_TRADE: Final[float] = 0.01

MAX_DAILY_TRADES: Final[int] = 10

CIRCUIT_BREAKER_LOSSES: Final[int] = 3

CIRCUIT_BREAKER_HOURS: Final[int] = 24


# ============================================================
# ATR
# ============================================================

ATR_PERIOD: Final[int] = 14

ATR_MULTIPLIER_SL: Final[float] = 2.0

ATR_MULTIPLIER_TP: Final[float] = 3.0


# ============================================================
# OFI
# ============================================================

OFI_DEPTH_LEVELS: Final[int] = 10


# ============================================================
# MARKET PHASE DETECTOR
# ============================================================

TREND_THRESHOLD: Final[float] = 0.02


# ============================================================
# AI SETTINGS
# ============================================================

MIN_CONFIDENCE_SCORE: Final[int] = 60

DEFAULT_AI_ACTION: Final[str] = "HOLD"


# ============================================================
# FEEDBACK LOOP
# ============================================================

FEEDBACK_LOOP_DAYS: Final[int] = 5


# ============================================================
# DATABASE TABLES
# ============================================================

TRADES_TABLE: Final[str] = "trades"

HISTORICAL_ERRORS_TABLE: Final[str] = (
    "historical_errors"
)


# ============================================================
# ENV VALIDATION
# ============================================================

REQUIRED_ENV_VARS: Final[tuple[str, ...]] = (
    "TELEGRAM_TOKEN",
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
    "DATABASE_URL",
    "DEEPSEEK_API_KEY",
    "TWITTER_BEARER_TOKEN",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "CRYPTOQUANT_API_KEY",
)


def validate_environment() -> None:
    """
    Проверка обязательных переменных окружения.
    Вызывается из main.py при запуске.
    """

    for variable_name in REQUIRED_ENV_VARS:
        get_required_env(variable_name)
