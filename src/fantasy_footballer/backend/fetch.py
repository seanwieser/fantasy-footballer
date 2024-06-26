"""Extract data from ESPN API, transform with model transformer, and write to jsonl files."""

import datetime
import os

from backend.io_utils import DATA_PATH_TEMPLATE, write_data
from backend.models import Base
from espn_api.football import League, Team

LEAGUE_ID = os.getenv("LEAGUE_ID")
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
START_YEAR = 2018


def extract_year(
    league_id: str, espn_s2: str, swid: str, year: int
) -> list[Team] | None:  # pylint: disable=unsupported-binary-operation
    """Extract data from ESPN API and return League object."""
    league = None
    try:
        league = League(league_id=int(league_id),
                        year=year,
                        espn_s2=espn_s2,
                        swid=swid)
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"Error fetching league {year}: {err}")
    return league


def fetch_all_data():
    """Fetch all data for all years and models in Base."""
    for year in range(START_YEAR, datetime.datetime.now().year + 1):
        league = extract_year(LEAGUE_ID, ESPN_S2, SWID, year)
        if league:
            for mapper in Base.registry.mappers:
                cls = mapper.class_
                transformed_data = cls.transform(league)
                write_data(transformed_data,
                           cls.__tablename__,
                           year,
                           root_path="../..")
                print(f"Data written for {cls.__tablename__} for year {year}")


if __name__ == '__main__':
    fetch_all_data()
