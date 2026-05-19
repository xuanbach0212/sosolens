import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ── _format_signal ────────────────────────────────────────────────────────────

def test_format_buy():
    from backend.services.telegram import _format_signal
    s = {"type": "BUY", "sector": "Gaming", "confidence": 85, "riskLevel": "low"}
    text = _format_signal(s)
    assert "🟢" in text
    assert "BUY" in text
    assert "Gaming" in text
    assert "85%" in text
    assert "low" in text


def test_format_avoid():
    from backend.services.telegram import _format_signal
    s = {"type": "AVOID", "sector": "Macro", "confidence": 72, "riskLevel": "high"}
    text = _format_signal(s)
    assert "🔴" in text
    assert "AVOID" in text


def test_format_watch():
    from backend.services.telegram import _format_signal
    s = {"type": "WATCH", "sector": "ETF", "confidence": 50, "riskLevel": "medium"}
    text = _format_signal(s)
    assert "🟡" in text
    assert "WATCH" in text


def test_format_includes_explanation():
    from backend.services.telegram import _format_signal
    s = {"type": "BUY", "sector": "DeFi", "confidence": 60, "riskLevel": "medium",
         "explanation": "Strong inflows detected"}
    text = _format_signal(s)
    assert "Strong inflows detected" in text


def test_format_missing_explanation():
    from backend.services.telegram import _format_signal
    s = {"type": "AVOID", "sector": "Macro", "confidence": 80, "riskLevel": "high"}
    text = _format_signal(s)
    assert text.count("\n") == 2  # only 3 lines, no explanation appended


# ── TelegramNotifier.enabled ──────────────────────────────────────────────────

def test_disabled_when_no_env_vars(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from backend.services.telegram import TelegramNotifier
    assert TelegramNotifier().enabled is False


def test_disabled_when_only_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from backend.services.telegram import TelegramNotifier
    assert TelegramNotifier().enabled is False


def test_enabled_when_both_set(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    from backend.services.telegram import TelegramNotifier
    assert TelegramNotifier().enabled is True


# ── send_signal_alert ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_alert_noop_when_disabled(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    from backend.services.telegram import TelegramNotifier
    notifier = TelegramNotifier()
    with patch("httpx.AsyncClient") as mock_client:
        await notifier.send_signal_alert({"type": "BUY", "sector": "X", "confidence": 80, "riskLevel": "low"})
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_send_alert_posts_to_telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mytoken")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "456")
    from backend.services.telegram import TelegramNotifier

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        notifier = TelegramNotifier()
        await notifier.send_signal_alert({"type": "AVOID", "sector": "Macro", "confidence": 70, "riskLevel": "high"})

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    url = call_kwargs[0][0]
    assert "mytoken" in url
    assert "sendMessage" in url
    payload = call_kwargs[1]["json"]
    assert payload["chat_id"] == "456"
    assert payload["parse_mode"] == "Markdown"
    assert "AVOID" in payload["text"]


# ── _notify_new_signals ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_skips_watch(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    import backend.agent.runner as runner
    runner._notified_signal_states = {}
    runner._telegram = None

    sent = []

    async def fake_alert(signal):
        sent.append(signal)

    import backend.services.telegram as tg_mod
    notifier = tg_mod.TelegramNotifier()
    notifier.send_signal_alert = fake_alert
    runner._telegram = notifier

    await runner._notify_new_signals([
        {"id": "macro-risk", "type": "WATCH", "sector": "Macro", "confidence": 50, "riskLevel": "medium"}
    ])
    assert sent == []


@pytest.mark.asyncio
async def test_notify_sends_for_new_buy(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    import backend.agent.runner as runner
    runner._notified_signal_states = {}
    runner._telegram = None

    sent = []

    async def fake_alert(signal):
        sent.append(signal["id"])

    import backend.services.telegram as tg_mod
    notifier = tg_mod.TelegramNotifier()
    notifier.send_signal_alert = fake_alert
    runner._telegram = notifier

    await runner._notify_new_signals([
        {"id": "etf-flow", "type": "BUY", "sector": "ETF", "confidence": 80, "riskLevel": "low"}
    ])
    assert sent == ["etf-flow"]
    assert runner._notified_signal_states["etf-flow"] == "BUY"


@pytest.mark.asyncio
async def test_notify_deduplicates_same_state(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    import backend.agent.runner as runner
    runner._notified_signal_states = {"etf-flow": "BUY"}

    sent = []

    async def fake_alert(signal):
        sent.append(signal["id"])

    import backend.services.telegram as tg_mod
    notifier = tg_mod.TelegramNotifier()
    notifier.send_signal_alert = fake_alert
    runner._telegram = notifier

    await runner._notify_new_signals([
        {"id": "etf-flow", "type": "BUY", "sector": "ETF", "confidence": 80, "riskLevel": "low"}
    ])
    assert sent == []


@pytest.mark.asyncio
async def test_notify_resends_on_type_change(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    import backend.agent.runner as runner
    runner._notified_signal_states = {"etf-flow": "BUY"}

    sent = []

    async def fake_alert(signal):
        sent.append(signal["type"])

    import backend.services.telegram as tg_mod
    notifier = tg_mod.TelegramNotifier()
    notifier.send_signal_alert = fake_alert
    runner._telegram = notifier

    await runner._notify_new_signals([
        {"id": "etf-flow", "type": "AVOID", "sector": "ETF", "confidence": 75, "riskLevel": "high"}
    ])
    assert sent == ["AVOID"]
    assert runner._notified_signal_states["etf-flow"] == "AVOID"
