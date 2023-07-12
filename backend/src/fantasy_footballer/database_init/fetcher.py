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


def extract_year(year: int) -> list[Team]:
    """Return team object from pickle file."""
    # league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID)
    with open(f'../../../league_{year}.pkl', 'rb') as inp:
        league: League = pickle.load(inp)
    return league


def transform_teams(raw_teams: list[Team], year: str) -> list[dict]:
    """Team ingestion tranformations."""
    new_teams = []
    for team in raw_teams:
        team = team.__dict__
        team["year"] = year
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


def extract_transform_players(league: League, year: str) -> list[dict]:
    """Player ingestion extraction and transformations."""
    player_stat_fields = [
        'teamWin', 'receivingReceptions', 'receivingYards', 'receivingTargets',
        'receivingTouchdowns', 'rushingAttempts', 'rushingYards',
        'rushingTouchdowns', 'receiving2PtConversions',
        'rushing2PtConversions', 'passingAttempts', 'passingCompletions',
        'passingIncompletions', 'passingYards', 'passingTouchdowns',
        'passingCompletionPercentage', 'passingTimesSacked', 'fumbles',
        'lostFumbles', 'turnovers', 'madeFieldGoalsFrom40To49',
        'attemptedFieldGoalsFrom40To49', 'madeFieldGoalsFromUnder40',
        'attemptedFieldGoalsFromUnder40', 'madeFieldGoals',
        'attemptedFieldGoals', 'madeExtraPoints', 'attemptedExtraPoints',
        'pointsScored'
    ]

    players = []
    for pick in league.draft:
        pick = pick.__dict__

        player = league.player_info(playerId=pick["playerId"])
        player = player.__dict__
        player["year"] = year
        stats = {}

        for week in player["stats"].keys():
            stats[week] = {}
            stats[week]['points'] = player['stats'][week]['points']
            for field in player_stat_fields:
                if field in player['stats'][week]['breakdown'].keys():
                    stats[week][field] = player['stats'][week]['breakdown'][
                        field]
        player["stats"] = stats

        pick = {
            k: v
            for k, v in pick.items()
            if k in ["round_num", "round_pick", "bid_amount"]
        }
        players.append(player | pick)
        print(player['name'])
    return players


def write_data(data: list[dict], kind: str, year: str) -> None:
    """Write jsonl format to specific location dependning on kind."""
    with open(f'data/{kind}/{kind}_{year}.json.csv', 'w',
              encoding='utf-8') as out_file:
        for line in data:
            json.dump(line, out_file)
            out_file.write('\n')


if __name__ == '__main__':
    for file_year in [2022]:  #, 2019, 2020, 2021, 2022, 2023]:
        lg = extract_year(file_year)

        transformed_teams = transform_teams(lg.teams, file_year)
        write_data(transformed_teams, 'teams', file_year)

        transformed_players = extract_transform_players(lg, file_year)
        write_data(transformed_players, 'players', file_year)
