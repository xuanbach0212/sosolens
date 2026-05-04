import os
from anthropic import AsyncAnthropic

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


async def explain_signal(signal_data: dict) -> str:
    """Stub explanation generator using Claude Haiku. Issue #15 will write the real prompt."""
    sector = signal_data.get("sector", "unknown sector")
    sig_type = signal_data.get("type", "WATCH")
    return f"{sig_type} signal detected in {sector}. Detailed AI explanation pending implementation."
