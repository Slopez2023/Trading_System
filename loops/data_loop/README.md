# Data Loop

Status: MVP.

The data loop turns experiment data requirements into local datasets.

```text
experiment_data_requirements -> data_jobs -> market_datasets
```

The first implementation is intentionally narrow: Binance USDT-M futures data for the BTC funding/open-interest experiment.

## Commands

```bash
python3 -m data_loop init-db
python3 -m data_loop plan-once
python3 -m data_loop collect-once
python3 -m data_loop list-jobs
python3 -m data_loop list-datasets
python3 -m data_loop stats
```

## Supported MVP Data

- `ohlcv`
- `volume`
- `funding_rates`
- `open_interest`

Default symbol:

```text
BTCUSDT
```

Default provider:

```text
binance_usdm
```

CSV files are written to:

```text
data/market/
```

