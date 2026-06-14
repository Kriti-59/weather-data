import argparse
from datetime import date, timedelta

from pipeline import run_pipeline


def date_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date = current_date + timedelta(days=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="Dallas")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)

    for requested_date in date_range(start_date, end_date):
        print(f"Backfilling {args.city} for {requested_date}")
        run_pipeline(args.city, str(requested_date), "backfill")


if __name__ == "__main__":
    main()

