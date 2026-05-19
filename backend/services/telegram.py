import os

import httpx

_API = "https://api.telegram.org/bot{token}/sendMessage"
_EMOJI = {"BUY": "🟢", "WATCH": "🟡", "AVOID": "🔴"}


class TelegramNotifier:
    def __init__(self):
        self._token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self._token and self._chat_id)

    async def send_signal_alert(self, signal: dict) -> None:
        if not self.enabled:
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                _API.format(token=self._token),
                json={
                    "chat_id": self._chat_id,
                    "text": _format_signal(signal),
                    "parse_mode": "Markdown",
                },
            )


def _format_signal(signal: dict) -> str:
    emoji = _EMOJI.get(signal["type"], "⚪")
    lines = [
        f"{emoji} *SOSOLENS SIGNAL: {signal['type']}*",
        f"📊 {signal.get('sector', '—')}",
        f"Confidence: {signal.get('confidence', 0)}%  ·  Risk: {signal.get('riskLevel', '—')}",
    ]
    if signal.get("explanation"):
        lines.append(f"\n_{signal['explanation']}_")
    return "\n".join(lines)
