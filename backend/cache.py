"""
In-memory cache for slow SoSoValue API data.
The hourly agent populates this; REST endpoints read from it instantly.
"""
from typing import Any

_store: dict[str, Any] = {}


def put(key: str, value: Any) -> None:
    _store[key] = value


def get(key: str) -> Any:
    return _store.get(key)


def get_or(key: str, fallback: Any) -> Any:
    v = _store.get(key)
    return v if v is not None else fallback


def has(key: str) -> bool:
    return key in _store
