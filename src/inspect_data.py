import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_table(connection, label, sql):
    cursor = connection.execute(sql)
    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    print(f"\n[{label}] {len(rows)} rows")
    print("  " + " | ".join(column_names))
    print("  " + "-" * 80)
    for row in rows:
        print("  " + " | ".join(str(v) for v in row))


with get_connection() as connection:

    print_section("PIPELINE RUNS")
    print_table(connection, "pipeline_runs", """
        SELECT batch_id, run_type, city, requested_date, status, started_at, rows_loaded
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT 10
    """)

    print_section("WEATHER OBSERVATIONS")
    print_table(connection, "weather_observations", """
        SELECT city, observation_date, high_temperature_f, low_temperature_f,
               precipitation_inches, weather_condition, batch_id
        FROM weather_observations
        ORDER BY observation_date DESC
        LIMIT 10
    """)

    print_section("MONTHLY SUMMARY")
    print_table(connection, "monthly_weather_summary", """
        SELECT * FROM monthly_weather_summary
    """)

    print_section("CITY DIMENSION")
    print_table(connection, "city_weather_dimension", """
        SELECT * FROM city_weather_dimension
    """)

    print_section("DATA QUALITY — latest 10 results")
    print_table(connection, "data_quality_results", """
        SELECT batch_id, check_name, status, failed_count, checked_at
        FROM data_quality_results
        ORDER BY checked_at DESC
        LIMIT 10
    """)

    print_section("RAW EVENTS — latest 5")
    print_table(connection, "raw_weather_events", """
        SELECT raw_event_id, city, requested_date, ingestion_timestamp, batch_id
        FROM raw_weather_events
        ORDER BY ingestion_timestamp DESC
        LIMIT 5
    """)