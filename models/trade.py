from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from models.base import Base


class Trade(Base):
    """
    Таблица всех торговых решений бота.

    Хранит полный контекст рынка перед открытием позиции
    и результат сделки для дальнейшего самообучения.
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    market_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    trigger_news: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="OPEN",
        nullable=False,
        index=True,
    )

    pnl: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    confidence_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    stop_loss_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    take_profit_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"Trade("
            f"id={self.id}, "
            f"asset='{self.asset}', "
            f"side='{self.side}', "
            f"status='{self.status}', "
            f"pnl={self.pnl}"
            f")"
        )
