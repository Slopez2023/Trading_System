from __future__ import annotations

from datetime import datetime, timedelta, timezone

from research_loop.db import connect, init_db
from research_loop.models import Source
from research_loop.repository import Repository


def test_due_sources_respect_check_frequency(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(
            Source(
                source_id="rss_source",
                source_type="rss",
                name="RSS",
                url="https://example.com/feed.xml",
                check_frequency_minutes=60,
            )
        )
        assert [source.source_id for source in repo.list_due_sources()] == ["rss_source"]

        repo.mark_source_checked("rss_source")
        assert repo.list_due_sources() == []

        old_time = (datetime.now(timezone.utc) - timedelta(minutes=61)).replace(microsecond=0).isoformat()
        connection.execute(
            "UPDATE sources SET last_checked_at = ? WHERE source_id = ?",
            (old_time, "rss_source"),
        )
        assert [source.source_id for source in repo.list_due_sources()] == ["rss_source"]
