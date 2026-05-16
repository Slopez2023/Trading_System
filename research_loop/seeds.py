from __future__ import annotations

from .models import Source


DEFAULT_SOURCES = [
    Source(
        source_id="reddit_algotrading_new",
        source_type="reddit",
        name="r/algotrading new",
        url="https://www.reddit.com/r/algotrading/new.json?limit=25",
        markets=["stocks", "crypto", "futures", "forex"],
        topics=["quant", "backtesting", "strategy design"],
        check_frequency_minutes=120,
        quality_score=0.68,
        noise_score=0.45,
    ),
    Source(
        source_id="reddit_options_new",
        source_type="reddit",
        name="r/options new",
        url="https://www.reddit.com/r/options/new.json?limit=25",
        markets=["options", "stocks"],
        topics=["volatility", "positioning", "risk"],
        check_frequency_minutes=120,
        quality_score=0.55,
        noise_score=0.62,
    ),
    Source(
        source_id="reddit_cryptocurrency_new",
        source_type="reddit",
        name="r/CryptoCurrency new",
        url="https://www.reddit.com/r/CryptoCurrency/new.json?limit=25",
        markets=["crypto"],
        topics=["sentiment", "narratives", "exchange behavior"],
        check_frequency_minutes=120,
        quality_score=0.48,
        noise_score=0.72,
    ),
    Source(
        source_id="arxiv_qfin",
        source_type="rss",
        name="arXiv q-fin",
        url="https://export.arxiv.org/rss/q-fin",
        markets=["stocks", "futures", "forex", "crypto"],
        topics=["papers", "quant research", "market microstructure"],
        check_frequency_minutes=1440,
        quality_score=0.74,
        noise_score=0.35,
    ),
    Source(
        source_id="sec_press_releases",
        source_type="rss",
        name="SEC press releases",
        url="https://www.sec.gov/news/pressreleases.rss",
        markets=["stocks", "options"],
        topics=["regulation", "enforcement", "market structure"],
        check_frequency_minutes=360,
        quality_score=0.7,
        noise_score=0.25,
    ),
]
