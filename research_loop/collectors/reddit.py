from __future__ import annotations

import json

from research_loop.config import Settings
from research_loop.models import RawItem, Source

from .base import Collector, CollectorError
from .http import fetch_text


class RedditCollector(Collector):
    source_type = "reddit"

    def __init__(self, settings: Settings):
        self.settings = settings

    def collect(self, source: Source) -> list[RawItem]:
        payload = fetch_text(
            source.url,
            timeout_seconds=self.settings.request_timeout_seconds,
            user_agent=self.settings.user_agent,
        )
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise CollectorError(f"invalid Reddit JSON from {source.url}") from exc

        children = data.get("data", {}).get("children", [])
        raw_items: list[RawItem] = []
        for child in children[:50]:
            post = child.get("data", {})
            title = post.get("title", "")
            selftext = post.get("selftext", "")
            permalink = post.get("permalink", "")
            url = f"https://www.reddit.com{permalink}" if permalink else post.get("url", "")
            if not title and not selftext:
                continue
            raw_items.append(
                RawItem(
                    source_id=source.source_id,
                    source_type=source.source_type,
                    url=url,
                    author=post.get("author", ""),
                    published_at=str(post.get("created_utc", "")),
                    title=title,
                    text=selftext,
                    metadata={
                        "collector": "reddit",
                        "subreddit": post.get("subreddit", ""),
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "upvote_ratio": post.get("upvote_ratio"),
                    },
                )
            )
        return raw_items
