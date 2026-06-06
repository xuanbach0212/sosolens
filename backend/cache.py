"""
In-memory cache for slow SoSoValue API data.
The hourly agent populates this; REST endpoints read from it instantly.
A snapshot is persisted to disk so restarts can show last-known data immediately.
"""
import json
import logging
import os
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

_store: dict[str, Any] = {}

_SNAPSHOT_PATH = os.environ.get(
    "CACHE_SNAPSHOT_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "cache_snapshot.json")),
)


def put(key: str, value: Any) -> None:
    _store[key] = value


def get(key: str) -> Any:
    return _store.get(key)


def get_or(key: str, fallback: Any) -> Any:
    v = _store.get(key)
    return v if v is not None else fallback


def has(key: str) -> bool:
    return key in _store


def save_to_disk() -> None:
    """Atomic write of current cache to disk. Safe to call from any task."""
    try:
        dir_ = os.path.dirname(_SNAPSHOT_PATH) or "."
        fd, tmp = tempfile.mkstemp(prefix=".cache.", suffix=".tmp", dir=dir_)
        with os.fdopen(fd, "w") as f:
            json.dump(_store, f)
        os.replace(tmp, _SNAPSHOT_PATH)
    except Exception as exc:
        logger.warning("[cache] save_to_disk failed: %s", exc)


def load_from_disk() -> int:
    """Load snapshot into _store if file exists. Returns number of keys loaded."""
    if not os.path.exists(_SNAPSHOT_PATH):
        return 0
    try:
        with open(_SNAPSHOT_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            _store.update(data)
            return len(data)
    except Exception as exc:
        logger.warning("[cache] load_from_disk failed: %s", exc)
    return 0
