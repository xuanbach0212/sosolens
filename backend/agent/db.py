import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.agent.models import Base

_DATABASE_URL = os.environ.get("DATABASE_URL")

if _DATABASE_URL:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
else:
    _DB_PATH = os.environ.get(
        "DATABASE_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agent.db")),
    )
    engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
