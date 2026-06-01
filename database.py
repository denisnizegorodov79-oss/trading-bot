import asyncpg
from config import config

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(config.DATABASE_URL)
        await self.create_tables()
        return self.pool

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {config.DB_TABLE_TRADES} (
                    id SERIAL PRIMARY KEY,
                    trade_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    asset VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    market_snapshot TEXT,
                    trigger_news TEXT,
                    status VARCHAR(10) DEFAULT 'OPEN',
                    pnl DECIMAL(20, 8) DEFAULT 0
                )
            """)

            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {config.DB_TABLE_ERRORS} (
                    id SERIAL PRIMARY KEY,
                    error_pattern TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    async def save_trade(self, trade_id: int, asset: str, side: str, market_snapshot: str, trigger_news: str):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {config.DB_TABLE_TRADES} (trade_id, asset, side, market_snapshot, trigger_news)
                VALUES ($1, $2, $3, $4, $5)
            """, trade_id, asset, side, market_snapshot, trigger_news)

    async def update_trade_status(self, trade_id: int, status: str, pnl: float):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE {config.DB_TABLE_TRADES}
                SET status = $1, pnl = $2
                WHERE trade_id = $3
            """, status, pnl, trade_id)

    async def save_error_pattern(self, error_pattern: str):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {config.DB_TABLE_ERRORS} (error_pattern)
                VALUES ($1)
            """, error_pattern)

    async def get_all_errors(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch(f"SELECT error_pattern FROM {config.DB_TABLE_ERRORS}")

    async def get_trades_by_status(self, status: str):
        async with self.pool.acquire() as conn:
            return await conn.fetch(f"""
                SELECT * FROM {config.DB_TABLE_TRADES}
                WHERE status = $1
            """, status)

    async def get_all_trades(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch(f"SELECT * FROM {config.DB_TABLE_TRADES} ORDER BY id DESC")

db = Database()