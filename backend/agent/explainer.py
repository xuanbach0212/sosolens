import json
import logging
import os
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None

_SYSTEM = (
    "You are a crypto market analyst. "
    "Explain a trading signal in 2–3 plain-English sentences. "
    "Be specific about the data points driving the signal. "
    "No bullet points. No markdown. No disclaimers."
)


def _get_client() -> AsyncAnthropic | None:
    global _client
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    if _client is None:
        _client = AsyncAnthropic(api_key=api_key)
    return _client


async def explain_signal(signal_data: dict) -> str:
    client = _get_client()
    if client is None:
        return _fallback(signal_data)

    summary = {
        "type": signal_data.get("type"),
        "sector": signal_data.get("sector"),
        "confidence": signal_data.get("confidence"),
        "risk": signal_data.get("risk"),
        "data": [
            {"source": ds.get("name"), "value": ds.get("value")}
            for ds in signal_data.get("dataSources", [])[:4]
        ],
    }

    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(summary)}],
        )
        return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("[explainer] Claude call failed: %s", exc)
        return _fallback(signal_data)


def _fallback(signal_data: dict) -> str:
    sig_type = signal_data.get("type", "WATCH")
    sector = signal_data.get("sector", "unknown sector")
    sources = signal_data.get("dataSources", [])
    if sources:
        top = sources[0]
        return f"{sig_type} signal in {sector}: {top.get('name', '')} at {top.get('value', '')}."
    return f"{sig_type} signal detected in {sector}."
