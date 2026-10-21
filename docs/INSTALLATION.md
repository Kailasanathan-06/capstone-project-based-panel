# Installation Guide

## 1. System Prerequisites

- Python 3.10 or newer (64-bit). Recommended: 3.13 (`python --version`)
- pip (bundled with Python)
- A web browser (Chrome / Edge / Firefox)
- Windows, Linux or macOS

## 2. Install Dependencies

From the project root:

```bash
python -m pip install -r requirements.txt
```

Key packages: Django 5.2, Django REST Framework, mysqlclient, pandas,
numpy (>=2.2.1), scikit-learn, reportlab, fpdf2, PyYAML, channels/daphne.
Optional but recommended: shap, xgboost (AI explainability / boosting),
pyarrow (Parquet export), duckdb (SQLite conversion).

> Windows numpy note: some machines ship a broken MINGW numpy that crashes
> with exit code `-1073741819` on `read_csv`. Fix with
> `pip install --only-binary=:all: --force-reinstall --no-deps numpy==2.2.1`.

## 3. Generate Datasets and Train the AI Model

```bash
python scripts/generate_dataset.py --tasks 10000
python scripts/train_ai.py
```

Six synthetic datasets are written to `datasets/` (seeded and reproducible)
and the Random Forest model to `models/risk_model.pkl`. All data is
synthetic; no API keys are required.

Run the environment checker to confirm everything is ready:

```bash
python scripts/setup_check.py
```

## 4. Set Up the Database and Start the Application

The server is a Django application (`securedt` project). After installing
dependencies:

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for the admin site
cp .env.example .env                # then edit with your settings
python manage.py collectstatic
python manage.py runserver 0.0.0.0:8000
```

Open http://127.0.0.1:8000 in your browser. Create a `config.yaml` next to
`config.py` to override any engine default (see `config.yaml.example`).

> MySQL is the default database; create `securetdb` first and set
> `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` in `.env`.

## 5. One-Command Launchers

- Windows: `run_windows.bat`
- Linux/macOS: `./run.sh` (chmod +x first)

## 6. Run the Tests

```bash
python tests/run_all.py
```

Expect 70+ unit tests, all 23 page routes, integration pipeline, and
performance checks to pass.

## 7. Troubleshooting

See `TROUBLESHOOTING.md` for the full symptom table.