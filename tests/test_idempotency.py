import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import pytest
from unittest.mock import patch
from pipeline import run_pipeline

from pathlib import Path

TEST_DB_PATH = Path("data/test_weather.db")


@pytest.fixture(autouse=True)
def clean_test_db():
    """Create a fresh test database before each test and remove it after."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    with patch("db.DATABASE_PATH", TEST_DB_PATH):
        yield
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


MOCK_API_RESPONSE = {
    "request_url": "https://api.open-meteo.com/v1/forecast?...",
    "payload": {
        "daily": {
            "time": ["2026-06-10"],
            "temperature_2m_max": [93.1],
            "temperature_2m_min": [77.0],
            "precipitation_sum": [0.142],
            "weather_code": [81],
        }
    }
}


def count_rows(table):
    conn = sqlite3.connect(TEST_DB_PATH)
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return count


def test_running_pipeline_twice_does_not_duplicate_or_update_observations():
    """Running a pipeline again for the same data should skip the second run and not create duplicate rows."""

    with patch("db.DATABASE_PATH", TEST_DB_PATH), \
         patch("pipeline.fetch_weather", return_value=MOCK_API_RESPONSE):

        run_pipeline("Dallas", "2026-06-10", "daily")
        count_after_first_run = count_rows("weather_observations")

        batch_id = run_pipeline("Dallas", "2026-06-10", "daily")
        count_after_second_run = count_rows("weather_observations")

    assert count_after_first_run == 1
    assert count_after_second_run == 1

    conn = sqlite3.connect(TEST_DB_PATH)
    status = conn.execute(
        "SELECT status FROM pipeline_runs WHERE batch_id = ?", (batch_id,)
    ).fetchone()[0]
    conn.close()

    assert status == "SKIPPED"


def test_pipeline_runs_table_records_every_execution():
    """pipeline_runs should have one row per execution, even for the same city and date."""
    
    with patch("db.DATABASE_PATH", TEST_DB_PATH), \
         patch("pipeline.fetch_weather", return_value=MOCK_API_RESPONSE):
        
        run_pipeline("Dallas", "2026-06-10", "daily")
        run_pipeline("Dallas", "2026-06-10", "daily")

    assert count_rows("pipeline_runs") == 2, "Should have 2 pipeline run records"


def test_backfill_does_not_duplicate_or_update_existing_observations():
    """Running a backfill again for the same data should skip the second run and not create duplicate rows."""    
    with patch("db.DATABASE_PATH", TEST_DB_PATH), \
         patch("pipeline.fetch_weather", return_value=MOCK_API_RESPONSE):
        
        run_pipeline("Dallas", "2026-06-10", "backfill")
        count_after_first_backfill = count_rows("weather_observations")

        run_pipeline("Dallas", "2026-06-10", "backfill")
        count_after_second_backfill = count_rows("weather_observations")

    assert count_after_first_backfill == 1
    assert count_after_second_backfill == 1, "Backfill should not create duplicate rows"