from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BinanceUSDMClient:
    base_url = "https://fapi.binance.com"

    def __init__(self, timeout_seconds: int = 20, user_agent: str = "TradingResearchLoop/0.3.0"):
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def klines(self, symbol: str, interval: str = "1h", limit: int = 500) -> list[Any]:
        return self._get_json("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})

    def funding_rates(self, symbol: str, limit: int = 1000) -> list[dict[str, Any]]:
        return self._get_json("/fapi/v1/fundingRate", {"symbol": symbol, "limit": limit})

    def open_interest_hist(self, symbol: str, period: str = "1h", limit: int = 500) -> list[dict[str, Any]]:
        return self._get_json("/futures/data/openInterestHist", {"symbol": symbol, "period": period, "limit": limit})

    def _get_json(self, path: str, params: dict[str, Any]) -> Any:
        query = urlencode(params)
        request = Request(
            f"{self.base_url}{path}?{query}",
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        time.sleep(0.15)
        return json.loads(payload)

