# Weather Data 

A end-to-end data engineering pipeline built with Python and SQLite that ingests real-time weather data, stores it across raw and curated layers, and tracks every run with full auditability.

**Data source:** [Open-Meteo](https://open-meteo.com/) — free weather API  
**Current coverage:** Dallas, TX  
**Pipeline cadence:** On-demand or scheduled daily runs

---

## What this pipeline does

Every run is assigned a unique batch ID that flows through every table — raw events, curated observations, and run logs all reference the same ID, so any row in the database can be traced back to the exact run that created it.

Raw API responses are saved exactly as received before any transformation happens.
If something breaks downstream, the original data is always there to reprocess from.

The curated table uses upsert logic so running the pipeline twice on the same day updates the existing row rather than creating a duplicate. The pipeline is safe to re-run at any time without corrupting the data.

Every run is recorded with a start time, finish time, status, and error message. Failed runs are logged with the exact error so they can be investigated and re-run.

---
