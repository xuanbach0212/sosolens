import asyncio
import time
import os
from typing import Any

import httpx

SOSOVALUE_BASE = "https://openapi.sosovalue.com/openapi/v1"
MIN_INTERVAL_SECS = 6.0  # 10 req/min — observed SoSoValue free-tier burst limit is ~10/min


class SoSoValueClient:
    """
    Async HTTP client for the SoSoValue Data API.
    Auth: x-soso-api-key header (free tier: 20 req/min, 100K req/month).
    Rate limiting: enforces 3-second minimum between calls.
    Retry: 3 attempts with exponential backoff on 429/5xx.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ["SOSOVALUE_API_KEY"]
        self._client = httpx.AsyncClient(
            base_url=SOSOVALUE_BASE,
            headers={"x-soso-api-key": self._api_key},
            timeout=10.0,
        )
        self._last_call_at: float = 0.0
        self._backoff_until: float = 0.0  # shared: any 429 pushes all callers back
        self._rate_lock = asyncio.Lock()

    async def _claim_slot(self) -> None:
        """Serialize rate-limit slot acquisition. All callers share backoff state."""
        async with self._rate_lock:
            backoff = self._backoff_until - time.monotonic()
            if backoff > 0:
                await asyncio.sleep(backoff)
            elapsed = time.monotonic() - self._last_call_at
            if elapsed < MIN_INTERVAL_SECS:
                await asyncio.sleep(MIN_INTERVAL_SECS - elapsed)
            self._last_call_at = time.monotonic()

    async def _get(self, path: str, params: dict | None = None) -> Any:
        await self._claim_slot()

        for attempt in range(3):
            try:
                r = await self._client.get(path, params=params)
                if r.status_code == 429:
                    self._backoff_until = time.monotonic() + 65  # shared cooldown
                    await self._claim_slot()
                    continue
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status != 429 and status < 500:
                    raise
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Failed after 3 attempts: {path}")

    async def close(self) -> None:
        await self._client.aclose()

    async def get_etf_list(self, symbol: str, country_code: str = "US") -> Any:
        return await self._get("/etfs", params={"symbol": symbol, "country_code": country_code})

    async def get_etf_snapshot(self, ticker: str) -> Any:
        return await self._get(f"/etfs/{ticker}/market-snapshot")

    async def get_index_list(self) -> Any:
        return await self._get("/indices")

    async def get_index_snapshot(self, ticker: str) -> Any:
        return await self._get(f"/indices/{ticker}/market-snapshot")

    async def get_index_constituents(self, ticker: str) -> Any:
        return await self._get(f"/indices/{ticker}/constituents")

    async def get_macro_events(self) -> Any:
        return await self._get("/macro/events")

    async def get_btc_treasuries(self) -> Any:
        return await self._get("/btc-treasuries")

    async def get_btc_treasury_history(self, ticker: str) -> Any:
        return await self._get(f"/btc-treasuries/{ticker}/purchase-history")

    async def get_news(self) -> Any:
        return await self._get("/news/hot")

    async def get_fundraising(self) -> Any:
        return await self._get("/fundraising/recent")

    async def get_etf_history(self, etf_id: str, days: int = 7) -> Any:
        return await self._get("/etf/market/history", params={"etfId": etf_id, "days": days})

    async def get_etf_summary_history(self, symbol: str, country_code: str = "US", limit: int = 30) -> Any:
        return await self._get(
            "/etfs/summary-history",
            params={"symbol": symbol, "country_code": country_code, "limit": limit},
        )

    async def get_currency_snapshot(self, currency_id: str) -> Any:
        return await self._get(f"/currencies/{currency_id}/market-snapshot")


_client: "SoSoValueClient | None" = None


def get_client() -> "SoSoValueClient":
    global _client
    if _client is None:
        _client = SoSoValueClient()
    return _client
