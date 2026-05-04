from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True)
    signal_id = Column(String, unique=True, nullable=False, index=True)
    type = Column(String, nullable=False)        # BUY | SELL | WATCH | AVOID
    sector = Column(String, nullable=False)
    confidence = Column(Integer, nullable=False)  # 0–100 (matches frontend format)
    risk = Column(String, nullable=False)         # LOW | MEDIUM | HIGH
    explanation = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)        # full signal dict served to frontend
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
