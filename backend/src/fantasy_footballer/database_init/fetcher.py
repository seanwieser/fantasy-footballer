"""Module to fetch data from espn_api."""

import json
import os
import pickle

import psycopg2
from espn_api.football import League, Team
from psycopg2 import Error

LEAGUE_ID = os.getenv('LEAGUE_ID')
SWID = os.getenv('SWID')
ESPN_S2 = os.getenv('ESPN_S2')

DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


def extract_teams(year: int) -> list[Team]:
    """Return team object from pickle file."""
    # league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID)
    with open(f'data/league_{year}.pkl', 'rb') as inp:
        league: League = pickle.load(inp)
    return league.teams


def transform_teams(raw_teams: list[Team], year: int) -> list[dict]:
    """Team ingestion tranformations."""
    new_teams = []
    for team in raw_teams:
        team = team.__dict__
        team['year'] = year
        team['roster'] = [
            player.__dict__['playerId'] for player in team['roster']
        ]
        for week_num in range(len(team["schedule"])):
            opponent = team["schedule"][week_num].__dict__
            team["schedule"][week_num] = {
                "team_id":
                opponent["team_id"],
                "score_for":
                round(team["scores"][week_num], 4),
                "score_against":
                round(team["scores"][week_num] + team["mov"][week_num], 4),
                "outcome":
                team["outcomes"][week_num]
            }
        team = {
            k: v
            for k, v in team.items()
            if k not in ('scores', 'outcomes', 'mov', 'logo_url')
        }
        team.update(
            {k: round(v, 4)
             for k, v in team.items() if isinstance(v, float)})
        new_teams.append(team)
    return new_teams


def etl_team_data(year: int) -> list[dict]:
    """Ingest API Team data to database Team schema."""
    teams = extract_teams(year)
    return transform_teams(teams, year)


if __name__ == '__main__':
    for file_year in [2018, 2019, 2020, 2021, 2022, 2023]:
        data = etl_team_data(file_year)
        with open(f'data/league_{file_year}.json.csv', 'w',
                  encoding='utf-8') as f:
            for line in data:
                json.dump(line, f)
                f.write('\n')
