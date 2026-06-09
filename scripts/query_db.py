"""
Read-only DuckDB query helper for humans and agents.

Runs an ad-hoc SQL query against the local DuckDB warehouse and prints the result,
without booting the full app. Read-only: the connection is opened read_only so this
can never mutate the warehouse.

Usage:
    poetry run python3 scripts/query_db.py "select * from main_marts.current_standings limit 5"
    poetry run python3 scripts/query_db.py --format csv "select year from main_base.base_s001__teams"
    echo "select 1 as x" | poetry run python3 scripts/query_db.py -

Or via the Makefile entry point:
    make query SQL="select * from main_intermediate.int__owner_season_scoring limit 10"

Schemas (DuckDB catalog is `main`): main_marts.*, main_intermediate.*, main_staging.*,
main_base.*, main_seed_data.*.
"""

import argparse
import sys

import duckdb
import pandas as pd

DB_PATH = "resources/fantasy_footballer.duckdb"


def run_query(sql: str, output_format: str = "table") -> None:
    """Execute sql read-only against the warehouse and print the result in output_format."""
    try:
        with duckdb.connect(DB_PATH, read_only=True) as conn:
            results_df = conn.sql(sql).fetchdf()
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(sql, file=sys.stderr)
        raise e

    if output_format == "csv":
        print(results_df.to_csv(index=False), end="")
    elif output_format == "json":
        print(results_df.to_json(orient="records", indent=2))
    else:
        with pd.option_context(
            "display.max_rows", None,
            "display.max_columns", None,
            "display.width", None,
            "display.max_colwidth", 60,
        ):
            print(results_df.to_string(index=False))
        sys.stdout.flush()
        print(f"\n[{len(results_df)} row(s)]", file=sys.stderr)


def main() -> None:
    """Parse CLI args and run the query. SQL of '-' reads the query from stdin."""
    parser = argparse.ArgumentParser(
        description="Run a read-only SQL query against the local DuckDB warehouse.",
    )
    parser.add_argument(
        "sql",
        help="The SQL query to run. Pass '-' to read the query from stdin.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format (default: table).",
    )
    args = parser.parse_args()

    sql = sys.stdin.read() if args.sql == "-" else args.sql
    if not sql.strip():
        parser.error("No SQL query provided.")

    run_query(sql, args.format)


if __name__ == "__main__":
    main()
