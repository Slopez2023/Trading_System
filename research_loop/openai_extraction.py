from __future__ import annotations

import json
import sqlite3
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .extraction import ExtractionResult
from .models import ResearchRecord
from .utils import from_json


HttpPost = Callable[[str, dict[str, Any], dict[str, str], int], dict[str, Any]]


class OpenAIExtractionError(RuntimeError):
    pass


RESEARCH_RECORD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
        "records": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "record_type": {
                        "type": "string",
                        "enum": [
                            "strategy_idea",
                            "market_observation",
                            "market_theme",
                            "anomaly",
                            "risk_warning",
                            "data_source",
                            "research_question",
                            "asset_watchlist",
                            "event_catalyst",
                            "source_candidate",
                            "contradiction",
                        ],
                    },
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "details": {"type": "string"},
                    "markets": {"type": "array", "items": {"type": "string"}},
                    "assets": {"type": "array", "items": {"type": "string"}},
                    "timeframes": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "required_data": {"type": "array", "items": {"type": "string"}},
                    "risks": {"type": "array", "items": {"type": "string"}},
                    "scores": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "priority": {"type": "integer", "minimum": 0, "maximum": 100},
                            "novelty": {"type": "integer", "minimum": 0, "maximum": 100},
                            "testability": {"type": "integer", "minimum": 0, "maximum": 100},
                            "data_availability": {"type": "integer", "minimum": 0, "maximum": 100},
                            "urgency": {"type": "integer", "minimum": 0, "maximum": 100},
                            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                            "source_quality": {"type": "integer", "minimum": 0, "maximum": 100},
                        },
                        "required": [
                            "priority",
                            "novelty",
                            "testability",
                            "data_availability",
                            "urgency",
                            "confidence",
                            "source_quality",
                        ],
                    },
                    "next_loop_targets": {"type": "array", "items": {"type": "string"}},
                    "evidence_summary": {"type": "string"},
                    "evidence_relationship": {"type": "string"},
                },
                "required": [
                    "record_type",
                    "title",
                    "summary",
                    "details",
                    "markets",
                    "assets",
                    "timeframes",
                    "tags",
                    "required_data",
                    "risks",
                    "scores",
                    "next_loop_targets",
                    "evidence_summary",
                    "evidence_relationship",
                ],
            },
        },
    },
    "required": ["relevance_score", "records"],
}


class OpenAIResearchExtractor:
    def __init__(self, settings: Settings, http_post: HttpPost | None = None):
        self.settings = settings
        self.http_post = http_post or _post_json

    def extract(self, raw_item: sqlite3.Row) -> ExtractionResult:
        if not self.settings.openai_api_key:
            raise OpenAIExtractionError("OPENAI_API_KEY is required for OpenAI extraction")

        if self._use_chat_completions:
            url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
            payload = self._chat_payload(raw_item)
        else:
            url = f"{self.settings.openai_base_url.rstrip('/')}/responses"
            payload = self._responses_payload(raw_item)
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        last_error: OpenAIExtractionError | None = None
        for _ in range(2):
            response = self.http_post(
                url,
                payload,
                headers,
                self.settings.request_timeout_seconds,
            )
            try:
                parsed = _parse_chat_json(response) if self._use_chat_completions else _parse_response_json(response)
                break
            except OpenAIExtractionError as exc:
                last_error = exc
        else:
            raise last_error or OpenAIExtractionError("OpenAI extraction failed")
        return _result_from_payload(parsed)

    @property
    def _use_chat_completions(self) -> bool:
        return "openrouter.ai" in self.settings.openai_base_url

    def _responses_payload(self, raw_item: sqlite3.Row) -> dict[str, Any]:
        text = self._prompt(raw_item)
        return {
            "model": self.settings.openai_model,
            "input": [{"role": "user", "content": text}],
            "max_output_tokens": self.settings.max_output_tokens,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "research_extraction",
                    "strict": True,
                    "schema": RESEARCH_RECORD_SCHEMA,
                }
            },
        }

    def _chat_payload(self, raw_item: sqlite3.Row) -> dict[str, Any]:
        return {
            "model": self.settings.openai_model,
            "messages": [{"role": "user", "content": self._prompt(raw_item)}],
            "temperature": 0.1,
            "max_tokens": self.settings.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "research_extraction",
                    "strict": True,
                    "schema": RESEARCH_RECORD_SCHEMA,
                },
            },
        }

    def _prompt(self, raw_item: sqlite3.Row) -> str:
        source_markets = from_json(raw_item["source_markets_json"], [])
        source_topics = from_json(raw_item["source_topics_json"], [])
        return f"""
You are extracting source-backed trading research records.

Rules:
- Return JSON only.
- Do not claim profitability.
- Preserve uncertainty.
- A single raw item may produce multiple records.
- Prefer testable strategy hypotheses when present.
- If a strategy idea contains risk terms, create the strategy idea and include risks. Add a separate risk_warning only if the risk is important on its own.
- Every record must link back to the source via evidence_summary.
- Score priority, testability, confidence, novelty, data_availability, urgency, and source_quality as 0-100 integers.
- Use this score guide: 80-100 strong/high priority, 60-79 useful, 40-59 weak or needs review, 0-39 low value.
- A clearly testable strategy idea with named data should usually have priority 60-90, not single digits.

Raw item:
- source_id: {raw_item["source_id"]}
- source_type: {raw_item["source_type"]}
- url: {raw_item["url"]}
- title: {raw_item["title"]}
- text: {raw_item["text"]}
- source_markets: {source_markets}
- source_topics: {source_topics}
""".strip()


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout_seconds: int) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise OpenAIExtractionError(f"OpenAI HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise OpenAIExtractionError(f"OpenAI network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OpenAIExtractionError("OpenAI request timed out") from exc
    except json.JSONDecodeError as exc:
        raise OpenAIExtractionError("OpenAI response was not valid JSON") from exc


def _parse_response_json(response: dict[str, Any]) -> dict[str, Any]:
    if isinstance(response.get("output_text"), str):
        return _loads_object(response["output_text"])

    for item in response.get("output", []):
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                return _loads_object(content["text"])

    raise OpenAIExtractionError("OpenAI response did not contain output text")


def _parse_chat_json(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenAIExtractionError("chat response did not contain choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise OpenAIExtractionError("chat response did not contain message content")
    return _loads_object(content)


def _loads_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise OpenAIExtractionError("model output was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise OpenAIExtractionError("model output JSON must be an object")
    return parsed


def _result_from_payload(payload: dict[str, Any]) -> ExtractionResult:
    relevance_score = float(payload.get("relevance_score", 0))
    records_payload = payload.get("records", [])
    if not isinstance(records_payload, list):
        raise OpenAIExtractionError("records must be a list")

    records: list[ResearchRecord] = []
    for item in records_payload:
        if not isinstance(item, dict):
            raise OpenAIExtractionError("each record must be an object")
        records.append(
            ResearchRecord(
                record_type=_required_str(item, "record_type"),
                title=_required_str(item, "title"),
                summary=_required_str(item, "summary"),
                details=_required_str(item, "details"),
                markets=_str_list(item.get("markets")),
                assets=_str_list(item.get("assets")),
                timeframes=_str_list(item.get("timeframes")),
                tags=_str_list(item.get("tags")),
                required_data=_str_list(item.get("required_data")),
                risks=_str_list(item.get("risks")),
                scores=_scores(item.get("scores")),
                next_loop_targets=_str_list(item.get("next_loop_targets")),
                evidence_summary=_required_str(item, "evidence_summary"),
                evidence_relationship=_required_str(item, "evidence_relationship"),
            )
        )
    relevance_score = max(0.0, min(relevance_score, 1.0))
    if records and relevance_score == 0:
        confidence_values = [record.scores.get("confidence", 50) for record in records]
        avg_confidence = sum(confidence_values) / len(confidence_values)
        relevance_score = max(0.5, min(avg_confidence / 100, 0.95))
    return ExtractionResult(relevance_score=relevance_score, records=records)


def _required_str(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str):
        raise OpenAIExtractionError(f"{key} must be a string")
    return value[:2000]


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item)[:200] for item in value if item is not None][:20]


def _scores(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {"priority": 0, "confidence": 0}
    scores: dict[str, int] = {}
    for key, raw in value.items():
        try:
            scores[str(key)] = max(0, min(int(raw), 100))
        except (TypeError, ValueError):
            continue
    return scores
