"""Script to truncate dbt seeds so that they are not committed to VCS."""

import csv
import os

DBT_SEEDS_PATH="./resources/dbt_seeds/"

def delete_csv_rows():
    """Truncate CSV files in the specified directory."""
    csv_files = [f for f in os.listdir(DBT_SEEDS_PATH) if f.endswith('.csv')]

    print(f"Found {len(csv_files)} CSV file(s)")

    for filename in csv_files:
        filepath = os.path.join(DBT_SEEDS_PATH, filename)

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            print(f"Truncated file: {filename}")
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"✗ {filename}: Error - {e}")


if __name__ == "__main__":
    delete_csv_rows()
