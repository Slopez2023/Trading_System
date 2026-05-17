from __future__ import annotations

import json

import pytest

from research_loop.db import connect, init_db
from research_loop.models import Source
from research_loop.repository import Repository
from research_loop.source_config import SourceConfigError, load_source_config, write_source_config


def test_load_source_config_validates_and_preserves_candidate_status(tmp_path) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "sources": [
                    {
                        "source_id": "cme_candidate",
                        "source_type": "manual",
                        "name": "CME candidate",
                        "url": "https://www.cmegroup.com/rss.html",
                        "category": "exchange",
                        "status": "candidate",
                        "markets": ["futures"],
                        "topics": ["exchange notices"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    sources = load_source_config(path)

    assert len(sources) == 1
    assert sources[0].status == "candidate"
    assert sources[0].metadata["category"] == "exchange"


def test_load_source_config_rejects_bad_source_type(tmp_path) -> None:
    path = tmp_path / "sources.json"
    path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "bad",
                        "source_type": "telegram",
                        "name": "Bad",
                        "url": "https://example.com",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SourceConfigError):
        load_source_config(path)


def test_write_source_config_round_trips_repository_sources(tmp_path) -> None:
    db_path = tmp_path / "research.sqlite3"
    export_path = tmp_path / "sources.json"
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        repo.upsert_source(
            Source(
                source_id="test_rss",
                source_type="rss",
                name="Test RSS",
                url="https://example.com/feed.xml",
                markets=["stocks"],
                topics=["news"],
                metadata={"category": "news"},
            )
        )
        connection.commit()
        write_source_config(export_path, repo.list_all_source_objects())

    sources = load_source_config(export_path)

    assert len(sources) == 1
    assert sources[0].source_id == "test_rss"
    assert sources[0].metadata["category"] == "news"
