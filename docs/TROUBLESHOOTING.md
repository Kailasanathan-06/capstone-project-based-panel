# Troubleshooting Guide

| Symptom | Resolution |
|---|---|
| numpy segfault `-1073741819` on `read_csv` | `pip install --only-binary=:all: --force-reinstall --no-deps numpy==2.2.1` |
| Port 8000 already in use | Change `PORT` in `config.yaml` or set `PORT` env var |
| "missing required packages" in setup_check | `python -m pip install -r requirements.txt` |
| No model metrics on AI page | Run `python scripts/train_ai.py`; engine uses rule fallback otherwise |
| Telemetry shows "Simulation mode is active" | Expected unless `zeek_logs_dir` points at real Zeek logs |
| Parquet export option disabled | Install `pyarrow` (optional feature) |
| Datasets page shows "missing" for a dataset | Click **Generate** on the card, or run `scripts/generate_dataset.py` |
| Big generate takes a while | 5 M rows is streamed in chunks; watch the progress bar; reduce count for faster runs |
| Upload rejected | Only CSV allowed; max 8 MB and 100,000 rows by default |
| CSRF error from a script | You must first GET `/api/state` and send its `csrf_token` |
| App runs but pages look unstyled | Refresh with cache cleared; static assets require the server to be running |
| `ImportError: duckdb` | SQLite conversion needs `duckdb`; it is optional and skipped if missing |
| Weird ├ characters in console | Legacy Windows console encoding; restart in a UTF-8 terminal or PowerShell Core |

## Getting More Diagnostic Detail

```bash
python scripts/setup_check.py   # environment / package health
python tests/run_all.py          # full unit + integration suite
```

## Filing a Bug

Include: OS + Python version, output of `python scripts/setup_check.py`,
the failing route/endpoint, and the exact error text (not a screenshot).