"""Extract data from ESPN API, transform with model transformer, and write to jsonl files."""

import datetime
import os
import sys

import click
import pickle

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from backend.io_utils import DATA_PATH_TEMPLATE, PICKLE_PATH_TEMPLATE, write_data
from backend.models import Base
from espn_api.football import League, Team

LEAGUE_ID = os.getenv("LEAGUE_ID")
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
START_YEAR = 2018


def extract_year(league_id: str, espn_s2: str, swid: str, year: int, refetch: bool) -> list[Team] | None:
    """Extract data from ESPN API and return League object."""
    league = None
    pickle_file = PICKLE_PATH_TEMPLATE.substitute(year=year)
    if not refetch:
        with open(pickle_file, "rb") as f:
            league = pickle.load(f)
        print(f"League {year} unpickled")
        return league

    try:
        league = League(league_id=int(league_id), year=year, espn_s2=espn_s2, swid=swid)
        with open(pickle_file, "wb") as f:
            pickle.dump(league, f)
        print(f"League {year} pickled")
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"Error fetching or pickling league {year}: {err}")
    return league


def extract_transform_write_data(tables: list[str] = None, years: list[int] = None, refetch: bool = False) -> None:
    """Fetch all data for all years and models in Base."""
    years_to_fetch = years or range(START_YEAR, datetime.datetime.now().year + 1)
    for year in years_to_fetch:
        league = extract_year(LEAGUE_ID, ESPN_S2, SWID, year, refetch)
        if league:
            table_classes_to_fetch = [mapper.class_ for mapper in Base.registry.mappers]
            if tables:
                table_classes_to_fetch = [cls for cls in table_classes_to_fetch if cls.__tablename__ in tables]
            for cls in table_classes_to_fetch:
                transformed_data = cls.transform(league)
                write_data(transformed_data, cls.__tablename__, year)
                print(f"Data written for {cls.__tablename__} for year {year}")


@click.command()
@click.option("--tables", type=str, default=None)
@click.option("--years", type=str, default=None)
@click.option("--refetch", is_flag=True)
def main(tables: str = None, years: str = None, refetch: bool = False):
    """Fetch data"""
    if tables:
        tables = tables.split(",")
    if years:
        years = [int(year) for year in years.split(",")]

    extract_transform_write_data(tables=tables, years=years, refetch=refetch)


if __name__ == '__main__':
    main()
