from db import get_connection, initialize_database


QUALITY_CHECKS = [
    {
        "name": "temperature_not_null",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE temperature_f IS NULL
        """,
        "failure_message": "Temperature is missing.",
    },
    {
        "name": "humidity_between_0_and_100",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE humidity_percent < 0
               OR humidity_percent > 100
               OR humidity_percent IS NULL
        """,
        "failure_message": "Humidity is outside valid range.",
    },
    {
        "name": "wind_speed_not_negative",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE wind_speed_mph < 0
        """,
        "failure_message": "Wind speed cannot be negative.",
    },
    {
        "name": "no_duplicate_observations",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT city, source, observation_timestamp, COUNT(*) AS row_count
                FROM weather_observations
                GROUP BY city, source, observation_timestamp
                HAVING COUNT(*) > 1
            )
        """,
        "failure_message": "Duplicate clean observations found.",
    },
]


def run_quality_checks(batch_id):
    initialize_database()
    failures = []

    with get_connection() as connection:
        for check in QUALITY_CHECKS:
            cursor = connection.execute(check["sql"])
            failed_count = cursor.fetchone()[0]
            status = "PASS" if failed_count == 0 else "FAIL"
            details = "OK" if status == "PASS" else check["failure_message"]

            connection.execute(
                """
                INSERT INTO data_quality_results (
                    batch_id,
                    check_name,
                    status,
                    failed_count,
                    details
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (batch_id, check["name"], status, failed_count, details),
            )

            print(f"{check['name']}: {status}")

            if status == "FAIL":
                failures.append(check["name"])

        connection.commit()

    return failures
