from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from models.base import Base


class AutoSignalLog(Base):
    __tablename__ = "auto_signal_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    asset: Mapped[str] = mapped_column(
        String(20),
        default="BTC",
    )

    price: Mapped[float] = mapped_column(
        Float,
    )

    signal: Mapped[str] = mapped_column(
        String(50),
    )

    confidence: Mapped[int] = mapped_column(
        Integer,
    )

    recommendation: Mapped[str] = mapped_column(
        Text,
    )
