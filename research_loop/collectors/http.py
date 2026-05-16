from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .base import CollectorError


def fetch_text(url: str, timeout_seconds: int, user_agent: str) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        raise CollectorError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise CollectorError(f"network error while fetching {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise CollectorError(f"timeout while fetching {url}") from exc
