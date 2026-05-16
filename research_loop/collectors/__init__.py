from .base import Collector, CollectorError
from .reddit import RedditCollector
from .rss import RSSCollector

__all__ = ["Collector", "CollectorError", "RSSCollector", "RedditCollector"]
