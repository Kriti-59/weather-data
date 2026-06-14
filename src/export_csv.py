import csv
from pathlib import Path

from db import get_connection


ROOT_DIR = Path(__file__).resolve().parents[1]

EXPORTS = [
    ("weather_observations", ROOT_DIR / "data" / "weather_observations.csv"),
    ("monthly_weather_summary", ROOT_DIR / "data" / "monthly_weather_summary.csv"),
    ("city_weather_dimension", ROOT_DIR / "data" / "city_weather_dimension.csv"),
]


def export_all():
    for table_name, output_path in EXPORTS:

        # Create the output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read all rows from the table or view
        with get_connection() as connection:
            cursor = connection.execute(f"SELECT * FROM {table_name}")
            column_names = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

        # Write to CSV — column names become the header row
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(column_names)
            writer.writerows(rows)

        print(f"Exported {len(rows)} rows → {output_path}")


if __name__ == "__main__":
    export_all()