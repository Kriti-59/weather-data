# Incident Report

**Date:** May 2026  
**Severity:** Low  
**Status:** Resolved  

---

## What happened

During a backfill run for Dallas from May 10 to June 13, the pipeline
silently loaded rows with `NULL` values for `high_temperature_f` and
`low_temperature_f`. The Open-Meteo forecast API returns `null` for dates
outside its historical window, but the pipeline had no guard against this
and inserted the rows anyway.

The quality checks caught the issue — `high_temperature_not_null` and
`low_temperature_not_null` both failed and marked those runs as `FAILED`
in `pipeline_runs`. However, the null rows had already been written to
`weather_observations` before the checks ran.

---

## Detection

Automated quality checks in `quality_checks.py` flagged the issue on
every affected batch. The `data_quality_results` table recorded `FAIL`
status for `high_temperature_not_null` and `low_temperature_not_null`.

---

## Blast radius

- `weather_observations` contained null temperature rows for dates before
  May 10, 2026
- `monthly_weather_summary` and `daily_weather_summary` views returned
  incomplete aggregates for those dates
- Raw data in `raw_weather_events` was intact — the original API response
  was preserved and showed `null` values confirming the API was the source

---

## Root cause

The `upsert_weather_observation` function did not validate required fields
before inserting. It assumed the API always returns valid temperature data.
The Open-Meteo forecast API returns `null` for dates outside its ~35 day
historical window.

---

## Fix

Added a null check at the top of `upsert_weather_observation` before
building the row:

```python
high_temp = daily["temperature_2m_max"][0]
low_temp = daily["temperature_2m_min"][0]

if high_temp is None or low_temp is None:
    print(f"Skipping — API returned null data for this date")
    return 0
```

Deleted `weather.db` and re-ran the backfill from May 10 which is the earliest
date with valid data. All 35 rows loaded cleanly.

---

## Why raw retention mattered

Because `raw_weather_events` stored the original API response untouched,
it was possible to confirm the API returned `null` and that no data was
lost in transformation. Without the raw layer, the root cause would have
been harder to verify.

---

## Known limitations of the fix

The current fix skips rows where required fields are null and logs
`rows_loaded = 0` in `pipeline_runs`. This means affected dates are
silently absent from `weather_observations` with no placeholder to
indicate data was expected but unavailable.

In a production system, better approaches would include:

**Retry with a fallback source** — if the forecast API returns null,
automatically try an archive endpoint or secondary source before skipping.

**Pending status** — insert a placeholder row with a `status` column set
to `PENDING` so downstream consumers know data is expected but not yet
available, and a separate process retries later.

**Availability check before ingestion** — validate that the API has data
for the requested date range before running the full pipeline, failing
fast with a clear message rather than processing nulls silently.

The current fix is acceptable for this project because the data genuinely
does not exist in the API for dates outside its historical window which is not a transient error. The raw layer preserves the original null response
for auditability, and the regression test documents the behavior.


