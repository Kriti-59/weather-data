import argparse
import json
import uuid
from datetime import date, datetime, UTC

from db import get_connection, initialize_database
from weather_api import fetch_weather
from weather_codes import describe_weather_code
from quality_checks import run_quality_checks


SOURCE = "Open-Meteo"


def utc_now_text():
    return datetime.utcnow().isoformat(timespec="seconds")


def insert_pipeline_run(connection, batch_id, run_type, city, requested_date):
    connection.execute(
        """
        INSERT INTO pipeline_runs (
            batch_id, run_type, city, requested_date, status, started_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (batch_id, run_type, city, requested_date, "RUNNING", utc_now_text()),
    )


def finish_pipeline_run(connection, batch_id, status, rows_loaded=0, error_message=None):
    connection.execute(
        """
        UPDATE pipeline_runs
        SET status = ?,
            finished_at = ?,
            rows_loaded = ?,
            error_message = ?
        WHERE batch_id = ?
        """,
        (status, utc_now_text(), rows_loaded, error_message, batch_id),
    )


def insert_raw_event(connection, batch_id, city, requested_date, api_result):
    connection.execute(
        """
        INSERT INTO raw_weather_events (
            batch_id,
            source,
            city,
            requested_date,
            ingestion_timestamp,
            raw_payload
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            batch_id,
            SOURCE,
            city,
            requested_date,
            utc_now_text(),
            json.dumps(api_result, sort_keys=True),
        ),
    )


def upsert_weather_observation(connection, batch_id, city, api_payload):
    daily = api_payload["daily"]

    row = {
        "city": city,
        "source": SOURCE,
        "observation_date": daily["time"][0],
        "high_temperature_f": daily["temperature_2m_max"][0],
        "low_temperature_f": daily["temperature_2m_min"][0],
        "precipitation_inches": daily["precipitation_sum"][0],
        "weather_code": daily["weather_code"][0],
        "weather_condition": describe_weather_code(daily["weather_code"][0]),
        "batch_id": batch_id,
    }
    connection.execute(
        """
        INSERT INTO weather_observations (
            city,
            source,
            observation_date,
            high_temperature_f,
            low_temperature_f,
            precipitation_inches,
            weather_code,
            weather_condition,
            batch_id
        )
        VALUES (
            :city,
            :source,
            :observation_date,
            :high_temperature_f,
            :low_temperature_f,
            :precipitation_inches,
            :weather_code,
            :weather_condition,
            :batch_id
        )
        ON CONFLICT(city, source, observation_date)
        DO UPDATE SET
            observation_date = excluded.observation_date,
            high_temperature_f = excluded.high_temperature_f,
            low_temperature_f = excluded.low_temperature_f,
            precipitation_inches = excluded.precipitation_inches,
            weather_code = excluded.weather_code,
            weather_condition = excluded.weather_condition,
            batch_id = excluded.batch_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        row,
    )

    return 1


def run_pipeline(city, requested_date, run_type):
    if requested_date == "today":
        requested_date = str(date.today())

    initialize_database()
    batch_id = str(uuid.uuid4())

    with get_connection() as connection:
        try:
            insert_pipeline_run(connection, batch_id, run_type, city, requested_date)

            api_result = fetch_weather(city, requested_date)
            insert_raw_event(connection, batch_id, city, requested_date, api_result)

            rows_loaded = upsert_weather_observation(
                connection,
                batch_id,
                city,
                api_result["payload"],
            )

            connection.commit()

            failures = run_quality_checks(batch_id)
            if failures:
                finish_pipeline_run(
                    connection,
                    batch_id,
                    "FAILED",
                    rows_loaded,
                    "Quality checks failed: " + ", ".join(failures),
                )
                connection.commit()
                return batch_id
                
            finish_pipeline_run(connection, batch_id, "SUCCESS", rows_loaded)
            connection.commit()

            print(f"Pipeline succeeded. Batch ID: {batch_id}")
            print(f"Rows loaded: {rows_loaded}")
            return batch_id

        except Exception as error:
            finish_pipeline_run(connection, batch_id, "FAILED", 0, str(error))
            connection.commit()
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Dallas")
    parser.add_argument("--date", default="today")
    parser.add_argument("--run-type", default="daily")
    args = parser.parse_args()

    run_pipeline(args.city, args.date, args.run_type)

if __name__ == "__main__":
    main()