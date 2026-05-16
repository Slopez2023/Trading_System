from __future__ import annotations

from pathlib import Path

from .collectors import Collector, CollectorError, RedditCollector, RSSCollector
from .config import Settings
from .db import connect, init_db
from .extraction import LocalResearchExtractor, ResearchExtractor
from .openai_extraction import OpenAIExtractionError, OpenAIResearchExtractor
from .repository import Repository
from .seeds import DEFAULT_SOURCES
from datetime import datetime, timezone

from .utils import from_json, slugify, utc_now


def seed_sources(db_path: Path) -> int:
    init_db(db_path)
    with connect(db_path) as connection:
        repo = Repository(connection)
        for source in DEFAULT_SOURCES:
            repo.upsert_source(source)
        connection.commit()
    return len(DEFAULT_SOURCES)


def collect_once(settings: Settings) -> dict[str, int]:
    init_db(settings.db_path)
    collectors = _collectors(settings)
    inserted = 0
    errors = 0
    checked = 0
    skipped = 0
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        active_count = len(repo.list_active_sources())
        due_sources = repo.list_due_sources()
        skipped = active_count - len(due_sources)
        for source in due_sources:
            collector = collectors.get(source.source_type)
            if collector is None:
                continue
            checked += 1
            try:
                raw_items = collector.collect(source)
            except CollectorError as exc:
                errors += 1
                repo.mark_source_failed(source.source_id, str(exc))
                continue
            inserted += repo.insert_raw_items(raw_items)
            repo.mark_source_checked(source.source_id)
        connection.commit()
    return {"sources_checked": checked, "sources_skipped": skipped, "raw_items_inserted": inserted, "errors": errors}


def extract_once(settings: Settings, limit: int = 50) -> dict[str, int]:
    init_db(settings.db_path)
    extractor = _extractor(settings)
    processed = 0
    records_created = 0
    ignored = 0
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        for raw_item in repo.claim_pending_raw_items(limit=limit):
            try:
                result = extractor.extract(raw_item)
            except Exception as exc:
                repo.mark_raw_item_failed(raw_item["raw_item_id"], str(exc))
                processed += 1
                continue
            if not result.records:
                repo.mark_raw_item_processed(raw_item["raw_item_id"], "ignored", result.relevance_score)
                ignored += 1
                processed += 1
                continue
            created_for_item = 0
            for record in result.records:
                if repo.insert_research_record(record, raw_item["raw_item_id"]):
                    records_created += 1
                    created_for_item += 1
            repo.mark_raw_item_processed(raw_item["raw_item_id"], "extracted", result.relevance_score)
            processed += 1
        connection.commit()
    return {"raw_items_processed": processed, "records_created": records_created, "ignored": ignored}


def run_once(settings: Settings, extract_limit: int = 50) -> dict[str, int]:
    collection = collect_once(settings)
    extraction = extract_once(settings, limit=extract_limit)
    return {**collection, **extraction}


def write_digest(settings: Settings, limit: int = 25) -> Path:
    settings.digest_dir.mkdir(parents=True, exist_ok=True)
    init_db(settings.db_path)
    with connect(settings.db_path) as connection:
        repo = Repository(connection)
        rows = repo.recent_research_records(limit=limit)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = settings.digest_dir / f"research_digest_{timestamp}_{slugify(str(limit))}.md"
    lines = [f"# Research Digest - {utc_now()}", ""]
    if not rows:
        lines.append("No research records yet.")
    for row in rows:
        scores = from_json(row["scores_json"], {})
        markets = ", ".join(from_json(row["markets_json"], [])) or "unknown"
        tags = ", ".join(from_json(row["tags_json"], [])[:8]) or "none"
        next_loops = ", ".join(from_json(row["next_loop_targets_json"], [])) or "none"
        lines.extend(
            [
                f"## {row['title']}",
                "",
                f"- Type: {row['record_type']}",
                f"- Status: {row['status']}",
                f"- Priority: {scores.get('priority', 'n/a')}",
                f"- Markets: {markets}",
                f"- Tags: {tags}",
                f"- Next loops: {next_loops}",
                f"- Summary: {row['summary']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _collectors(settings: Settings) -> dict[str, Collector]:
    return {
        "rss": RSSCollector(settings),
        "reddit": RedditCollector(settings),
    }


def _extractor(settings: Settings) -> ResearchExtractor:
    provider = settings.extractor_provider.lower()
    if provider == "openai":
        return OpenAIResearchExtractor(settings)
    if provider == "hybrid":
        return HybridResearchExtractor(settings)
    return LocalResearchExtractor()


class HybridResearchExtractor:
    def __init__(self, settings: Settings):
        self.openai = OpenAIResearchExtractor(settings)
        self.local = LocalResearchExtractor()

    def extract(self, raw_item):
        try:
            return self.openai.extract(raw_item)
        except OpenAIExtractionError as exc:
            print(f"[extract] OpenAI failed; falling back to local: {exc}")
            return self.local.extract(raw_item)
