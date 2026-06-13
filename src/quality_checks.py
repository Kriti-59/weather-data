from db import get_connection, initialize_database


QUALITY_CHECKS = [
    {
        "name": "high_temperature_not_null",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE high_temperature_f IS NULL
        """,
        "failure_message": "High temperature is missing.",
    },
    {
        "name": "low_temperature_not_null",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE low_temperature_f IS NULL
        """,
        "failure_message": "Low temperature is missing.",
    },
    {
        "name": "low_temp_below_high_temp",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE low_temperature_f >= high_temperature_f
        """,
        "failure_message": "Low temperature is not below high temperature.",
    },
    {
        "name": "precipitation_not_negative",
        "sql": """
            SELECT COUNT(*)
            FROM weather_observations
            WHERE precipitation_inches < 0
        """,
        "failure_message": "Precipitation cannot be negative.",
    },
    {
        "name": "no_duplicate_observations",
        "sql": """
            SELECT COUNT(*)
            FROM (
                SELECT city, source, observation_date, COUNT(*) AS row_count
                FROM weather_observations
                GROUP BY city, source, observation_date
                HAVING COUNT(*) > 1
            )
        """,
        "failure_message": "Duplicate observations found.",
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
