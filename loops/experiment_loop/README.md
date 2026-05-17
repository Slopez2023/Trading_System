# Experiment Planner Loop

Status: MVP.

The experiment planner loop turns selected research records into strict experiment specs.

```text
research_records -> experiment_specs -> data loop / backtest loop
```

It does not collect market data, write arbitrary backtest code, or trade.

## Commands

```bash
python3 -m experiment_loop init-db
python3 -m experiment_loop plan-once
python3 -m experiment_loop list-specs
python3 -m experiment_loop stats
```

## Output Contract

Primary table:

```text
experiment_specs
```

Important fields:

- `source_record_id`: research record that produced the spec
- `thesis`: testable claim
- `experiment_type`: `signal_backtest`, `event_study`, or `risk_model`
- `market` / `asset`
- `timeframes_json`
- `data_needed_json`
- `entry_rule`
- `exit_rule`
- `cost_model_json`
- `success_metric`
- `reject_if`
- `status`
- `scores_json`

Secondary table:

```text
experiment_data_requirements
```

This is the queue a future data loop can consume.

