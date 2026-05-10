import asyncio
from typing import Any

_subscribers: list[asyncio.Queue] = []


def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue) -> None:
    if q in _subscribers:
        _subscribers.remove(q)


async def broadcast(data: dict[str, Any]) -> None:
    for q in _subscribers:
        await q.put(data)
