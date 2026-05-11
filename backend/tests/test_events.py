"""Unit tests for backend/events.py pub/sub broker."""
import asyncio
import backend.events as events


def setup_function():
    events._subscribers.clear()


async def test_subscribe_returns_queue():
    q = events.subscribe()
    assert isinstance(q, asyncio.Queue)
    assert q in events._subscribers


async def test_broadcast_delivers_to_all_subscribers():
    q1 = events.subscribe()
    q2 = events.subscribe()
    payload = {"signals": [], "market": None}
    await events.broadcast(payload)
    assert q1.get_nowait() == payload
    assert q2.get_nowait() == payload


async def test_unsubscribe_removes_queue():
    q = events.subscribe()
    events.unsubscribe(q)
    assert q not in events._subscribers
    await events.broadcast({"x": 1})
    assert q.empty()


async def test_broadcast_with_no_subscribers_does_not_raise():
    await events.broadcast({"x": 1})  # no-op, must not raise
