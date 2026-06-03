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


class HistoricalError(Base):
    """
    Таблица ошибок и неудачных паттернов торговли.

    Используется механизмом Feedback Loop для хранения
    закономерностей, найденных DeepSeek после анализа
    убыточных сделок.
    """

    __tablename__ = "historical_errors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    pattern_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    pattern_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    ai_rule: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    source_trades_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    last_detected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"HistoricalError("
            f"id={self.id}, "
            f"pattern_name='{self.pattern_name}', "
            f"confidence_score={self.confidence_score}, "
            f"is_active={self.is_active}"
            f")"
        )
