"""Module to fetch data from espn_api."""

import json
import os.path
from string import Template

from etl.extract import extract_year
from etl.transform import transform_players, transform_teams

LEAGUE_ID = os.getenv('LEAGUE_ID')
ESPN_S2 = os.getenv('ESPN_S2')
SWID = os.getenv('SWID')
DATA_PATH_TEMPLATE = Template(
    "./data/${table_name}/${table_name}_${year}.jsonl")


def write_data(data: list[dict], kind: str, year: str) -> None:
    """Write jsonl format to specific location depending on kind."""
    with open(f'../../data/{kind}/{kind}_{year}.jsonl', 'w',
              encoding='utf-8') as out_file:
        for line in data:
            json.dump(line, out_file)
            out_file.write('\n')


def etl_pipeline(years, full_refresh=True) -> None:
    for year in years:
        if not full_refresh or not os.path.isfile(
                DATA_PATH_TEMPLATE.substitute(table_name="players",
                                              year=year)):
            lg = extract_year(LEAGUE_ID, ESPN_S2, SWID, year)
            print(lg.previousSeasons)
            # if lg:
            #     transformed_players = transform_players(lg)
            #     write_data(transformed_players, "players", year)
            # print(f"Finished fetching data for {year} players.")
