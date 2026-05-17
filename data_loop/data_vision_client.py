from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from io import BytesIO, TextIOWrapper
from typing import Any
from urllib.request import Request, urlopen
from zipfile import ZipFile


class BinanceDataVisionClient:
    base_url = "https://data.binance.vision/data/futures/um"

    def __init__(self, timeout_seconds: int = 20, user_agent: str = "TradingResearchLoop/0.3.0"):
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def klines(self, symbol: str, interval: str = "1h") -> list[dict[str, Any]]:
        day = _latest_daily_archive_day()
        url = f"{self.base_url}/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{day}.zip"
        return self._read_zip_csv(url)

    def funding_rates(self, symbol: str) -> list[dict[str, Any]]:
        month = _latest_monthly_archive_month()
        url = f"{self.base_url}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip"
        return self._read_zip_csv(url)

    def metrics(self, symbol: str) -> list[dict[str, Any]]:
        day = _latest_daily_archive_day()
        url = f"{self.base_url}/daily/metrics/{symbol}/{symbol}-metrics-{day}.zip"
        return self._read_zip_csv(url)

    def _read_zip_csv(self, url: str) -> list[dict[str, Any]]:
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/zip"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read()
        with ZipFile(BytesIO(payload)) as archive:
            csv_names = [name for name in archive.namelist() if name.endswith(".csv")]
            if not csv_names:
                raise ValueError(f"archive has no CSV: {url}")
            with archive.open(csv_names[0]) as handle:
                reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
                return list(reader)


def _latest_daily_archive_day() -> str:
    # Daily archives normally appear after the full UTC day has closed.
    day = datetime.now(timezone.utc).date() - timedelta(days=2)
    return day.isoformat()


def _latest_monthly_archive_month() -> str:
    today = datetime.now(timezone.utc).date()
    first_this_month = today.replace(day=1)
    last_month = first_this_month - timedelta(days=1)
    return f"{last_month.year:04d}-{last_month.month:02d}"

