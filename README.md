# Weather Data Pipeline

An end-to-end data engineering pipeline built with Python and SQLite that ingests daily weather observations, stores raw API responses, transforms and validates clean data, and produces analytics-ready outputs.

**Data source:** [Open-Meteo](https://open-meteo.com/) — free weather API  
**Current coverage:** Dallas, TX  
**Pipeline cadence:** On-demand or scheduled daily runs

---

## What this pipeline does

Every run is assigned a unique batch ID that flows through every table; raw events,
curated observations, quality results, and run logs all reference the same ID. Any
row in the database can be traced back to the exact run that produced it.

Raw API responses are saved exactly as received before any transformation.
If something breaks downstream, the original data is always there to reprocess from.

The curated table uses upsert logic so running the pipeline twice on the same day
updates the existing row rather than creating a duplicate. The pipeline is safe to
re-run at any time without corrupting the data.

Every run is recorded with a start time, finish time, status, and error message.
Failed runs are logged with the exact error so they can be investigated and re-run.

---

## Database

The pipeline uses a SQLite database with four tables. Every table includes a `batch_id` column that links back to the run that created it.

**`pipeline_runs`** records every execution with start time, finish time, status, and error message. A run starts as `RUNNING` and ends as `SUCCESS` or `FAILED`.

**`raw_weather_events`** stores the full API response exactly as received, before any transformation. Never modified after insert.

**`weather_observations`** is the clean curated table. One row per city per day. The primary key on `(city, source, observation_date)` prevents duplicate rows.

**`data_quality_results`** stores every quality check result per batch — pass or fail, with a count of failing rows and a description of what went wrong.

See [`data/er_diagram.png`](data/er_diagram.png) for the full entity relationship diagram.

### Analytics views

Three views sit on top of `weather_observations` for downstream consumers:

| View | Grain | Description |
|---|---|---|
| `daily_weather_summary` | One row per city per day | Clean daily observations with computed average temperature |
| `monthly_weather_summary` | One row per city per month | Aggregated temperature, precipitation, and observation count |
| `city_weather_dimension` | One row per city | Record highs, record lows, total precipitation, and date range |

---

## How to run


**Run the pipeline**

```bash
python3 src/pipeline.py --city Dallas --date today
```

The database is created automatically on the first run.

**Backfill historical data**

```bash
python3 src/backfill.py --city Dallas --start-date 2026-05-10 --end-date 2026-06-13
```

**Export to CSV**

```bash
python3 src/export_csv.py
```

**Run tests**

```bash
pytest tests/ -v
```

---

## Data engineering concepts demonstrated

| Concept | Where |
|---|---|
| Raw data retention | `raw_weather_events` stores original API response untouched |
| Idempotency | Upsert logic on `(city, source, observation_date)` prevents duplicates |
| Backfill | CLI tool reprocesses any city and date range safely |
| Data quality | Automated checks for nulls, range violations, and duplicates |
| Schema evolution | Contract tests verify curated schema stability across API changes |
| Traceability | `batch_id` links every row across all four tables |
| Reliability | `pipeline_runs` logs every execution with full error details |
| Analytics layer | Views serve stable aggregates to downstream consumers |

---

## Incident report

During development, the pipeline silently inserted null temperature rows for dates
outside the API's historical window. The quality checks caught the failure, the raw
layer preserved the original response for investigation, and a null check was added
to skip invalid rows before insert. Full details in [`docs/incident_report.md`](docs/incident_report.md).


---

## Project structure

```text
weather-data-pipeline/
├── src/
│   ├── db.py                  # Database connection and initialization
│   ├── weather_api.py         # Open-Meteo API fetch
│   ├── pipeline.py            # Main pipeline — fetch, transform, quality, audit
│   ├── quality_checks.py      # Data quality checks
│   ├── backfill.py            # Historical reprocessing by city and date range
│   └── export_csv.py          # Export curated tables to CSV
├── tests/
│   ├── test_idempotency.py    # Proves duplicate runs do not create duplicate rows
│   └── test_schema_contracts.py # Proves curated schema stays stable across API changes
├── docs/
│   ├── data_contract.md       # Guaranteed fields and SLA for weather_observations
│   └── incident_report.md     # Real pipeline failure, root cause, fix, and regression test
├── data/
│   └── er_diagram.png         # Entity relationship diagram
├── schema.sql                 # Table and view definitions
└── README.md
```

---
