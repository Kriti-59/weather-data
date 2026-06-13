import argparse
import json
import uuid
from datetime import datetime

from db import get_connection, initialize_database
from weather_api import fetch_weather
from weather_codes import describe_weather_code

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
    current = api_payload["current"]
    daily = api_payload["daily"]

    weather_code = int(current["weather_code"])
    condition = describe_weather_code(weather_code)

    row = {
        "city": city,
        "source": SOURCE,
        "observation_date": daily["time"][0],
        "observation_timestamp": current["time"],
        "temperature_f": current["temperature_2m"],
        "high_temperature_f": daily["temperature_2m_max"][0],
        "low_temperature_f": daily["temperature_2m_min"][0],
        "humidity_percent": current["relative_humidity_2m"],
        "wind_speed_mph": current["wind_speed_10m"],
        "precipitation_inches": daily["precipitation_sum"][0],
        "weather_condition": condition,
        "weather_code": weather_code,
        "batch_id": batch_id,
    }

    connection.execute(
        """
        INSERT INTO weather_observations (
            city,
            source,
            observation_date,
            observation_timestamp,
            temperature_f,
            high_temperature_f,
            low_temperature_f,
            humidity_percent,
            wind_speed_mph,
            precipitation_inches,
            weather_condition,
            weather_code,
            batch_id
        )
        VALUES (
            :city,
            :source,
            :observation_date,
            :observation_timestamp,
            :temperature_f,
            :high_temperature_f,
            :low_temperature_f,
            :humidity_percent,
            :wind_speed_mph,
            :precipitation_inches,
            :weather_condition,
            :weather_code,
            :batch_id
        )
        ON CONFLICT(city, source, observation_timestamp)
        DO UPDATE SET
            observation_date = excluded.observation_date,
            temperature_f = excluded.temperature_f,
            high_temperature_f = excluded.high_temperature_f,
            low_temperature_f = excluded.low_temperature_f,
            humidity_percent = excluded.humidity_percent,
            wind_speed_mph = excluded.wind_speed_mph,
            precipitation_inches = excluded.precipitation_inches,
            weather_condition = excluded.weather_condition,
            weather_code = excluded.weather_code,
            batch_id = excluded.batch_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        row,
    )

    return 1


def run_pipeline(city, requested_date, run_type):
    initialize_database()
    batch_id = str(uuid.uuid4())

    with get_connection() as connection:
        try:
            insert_pipeline_run(connection, batch_id, run_type, city, requested_date)

            api_result = fetch_weather(city)
            insert_raw_event(connection, batch_id, city, requested_date, api_result)

            rows_loaded = upsert_weather_observation(
                connection,
                batch_id,
                city,
                api_result["payload"],
            )

            finish_pipeline_run(connection, batch_id, "SUCCESS", rows_loaded)
            connection.commit()

            print(f"Pipeline succeeded. Batch ID: {batch_id}")
            print(f"Rows loaded: {rows_loaded}")
            return batch_id

        except Exception as error:
            finish_pipeline_run(connection, batch_id, "FAILED", 0, str(error))
            connection.commit()
            raise



parser = argparse.ArgumentParser()
parser.add_argument("--city", default="Dallas")
parser.add_argument("--date", default="today")
parser.add_argument("--run-type", default="daily")
args = parser.parse_args()

run_pipeline(args.city, args.date, args.run_type)


