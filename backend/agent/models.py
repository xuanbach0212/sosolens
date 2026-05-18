from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id          = Column(Integer,  primary_key=True)
    recorded_at = Column(DateTime, nullable=False, index=True,
                         default=lambda: datetime.now(timezone.utc))
    btc_price   = Column(Float,    nullable=False)
    eth_price   = Column(Float,    nullable=False)


class EtfSnapshot(Base):
    __tablename__ = "etf_snapshots"

    id          = Column(Integer,  primary_key=True)
    recorded_at = Column(DateTime, nullable=False, index=True,
                         default=lambda: datetime.now(timezone.utc))
    btc_flow    = Column(Float,    nullable=False)
    eth_flow    = Column(Float,    nullable=False)
    total_flow  = Column(Float,    nullable=False)


class SignalOutcome(Base):
    __tablename__ = "signal_outcomes"

    id          = Column(Integer,  primary_key=True)
    detector_id = Column(String,   nullable=False, index=True)
    signal_type = Column(String,   nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    entry_price = Column(Float,    nullable=False)
    exit_price  = Column(Float,    nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    outcome     = Column(String,   nullable=True)   # "WIN" | "LOSS" | "SKIP" | None=pending


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
