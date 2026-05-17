from __future__ import annotations

import sqlite3

from research_loop.utils import content_hash, from_json, stable_json, to_json, utc_now

from .models import ExperimentSpec


class ExperimentRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def candidate_research_records(self, limit: int = 10) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM research_records
            WHERE status != 'archived'
              AND record_type IN ('strategy_idea', 'risk_warning')
              AND (
                  json_array_length(next_loop_targets_json) = 0
                  OR EXISTS (
                      SELECT 1
                      FROM json_each(next_loop_targets_json)
                      WHERE value = 'experiment_loop'
                  )
              )
            ORDER BY
                CAST(json_extract(scores_json, '$.priority') AS INTEGER) DESC,
                updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def insert_experiment_spec(self, spec: ExperimentSpec) -> bool:
        now = utc_now()
        spec_hash = content_hash(
            spec.source_record_id,
            spec.experiment_type,
            spec.thesis,
            spec.entry_rule,
            spec.exit_rule,
            stable_json(spec.data_needed),
        )
        experiment_id = f"exp_{spec_hash[:16]}"
        cursor = self.connection.execute(
            """
            INSERT INTO experiment_specs (
                experiment_id, source_record_id, thesis, experiment_type,
                market, asset, timeframes_json, data_needed_json,
                entry_rule, exit_rule, cost_model_json, success_metric,
                reject_if, status, scores_json, notes, content_hash,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_record_id, experiment_type) DO UPDATE SET
                thesis = excluded.thesis,
                market = excluded.market,
                asset = excluded.asset,
                timeframes_json = excluded.timeframes_json,
                data_needed_json = excluded.data_needed_json,
                entry_rule = excluded.entry_rule,
                exit_rule = excluded.exit_rule,
                cost_model_json = excluded.cost_model_json,
                success_metric = excluded.success_metric,
                reject_if = excluded.reject_if,
                status = excluded.status,
                scores_json = excluded.scores_json,
                notes = excluded.notes,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (
                experiment_id,
                spec.source_record_id,
                spec.thesis,
                spec.experiment_type,
                spec.market,
                spec.asset,
                to_json(spec.timeframes),
                to_json(spec.data_needed),
                spec.entry_rule,
                spec.exit_rule,
                to_json(spec.cost_model),
                spec.success_metric,
                spec.reject_if,
                spec.status,
                to_json(spec.scores),
                spec.notes,
                spec_hash,
                now,
                now,
            ),
        )
        row = self.connection.execute(
            """
            SELECT experiment_id
            FROM experiment_specs
            WHERE source_record_id = ? AND experiment_type = ?
            """,
            (spec.source_record_id, spec.experiment_type),
        ).fetchone()
        if row:
            self._sync_data_requirements(row["experiment_id"], spec.data_needed, now)
        return bool(cursor.rowcount)

    def recent_experiment_specs(self, limit: int = 20) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT *
            FROM experiment_specs
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def count_table(self, table: str) -> int:
        allowed = {"experiment_specs", "experiment_data_requirements"}
        if table not in allowed:
            raise ValueError(f"unsupported table: {table}")
        return int(self.connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])

    def _sync_data_requirements(self, experiment_id: str, data_needed: list[str], now: str) -> None:
        cleaned = _dedupe(data_needed)
        if cleaned:
            placeholders = ", ".join("?" for _ in cleaned)
            self.connection.execute(
                f"""
                UPDATE experiment_data_requirements
                SET status = 'obsolete', updated_at = ?
                WHERE experiment_id = ?
                  AND data_name NOT IN ({placeholders})
                """,
                (now, experiment_id, *cleaned),
            )
        else:
            self.connection.execute(
                """
                UPDATE experiment_data_requirements
                SET status = 'obsolete', updated_at = ?
                WHERE experiment_id = ?
                """,
                (now, experiment_id),
            )
        for data_name in cleaned:
            requirement_hash = content_hash(experiment_id, data_name)
            self.connection.execute(
                """
                INSERT INTO experiment_data_requirements (
                    requirement_id, experiment_id, data_name, status, created_at, updated_at
                )
                VALUES (?, ?, ?, 'needed', ?, ?)
                ON CONFLICT(experiment_id, data_name) DO UPDATE SET
                    status = CASE
                        WHEN experiment_data_requirements.status = 'obsolete' THEN 'needed'
                        ELSE experiment_data_requirements.status
                    END,
                    updated_at = excluded.updated_at
                """,
                (f"req_{requirement_hash[:16]}", experiment_id, data_name, now, now),
            )


def experiment_payload(row: sqlite3.Row) -> dict:
    return {
        "experiment_id": row["experiment_id"],
        "source_record_id": row["source_record_id"],
        "thesis": row["thesis"],
        "experiment_type": row["experiment_type"],
        "market": row["market"],
        "asset": row["asset"],
        "timeframes": from_json(row["timeframes_json"], []),
        "data_needed": from_json(row["data_needed_json"], []),
        "entry_rule": row["entry_rule"],
        "exit_rule": row["exit_rule"],
        "cost_model": from_json(row["cost_model_json"], []),
        "success_metric": row["success_metric"],
        "reject_if": row["reject_if"],
        "status": row["status"],
        "scores": from_json(row["scores_json"], {}),
        "notes": row["notes"],
    }


def _dedupe(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        item = str(value).strip()
        key = item.lower()
        if not item or key in seen:
            continue
        cleaned.append(item)
        seen.add(key)
    return cleaned

