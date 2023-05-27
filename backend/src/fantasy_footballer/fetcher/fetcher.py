"""Module to fetch data from espn_api."""

import os
import pickle

from espn_api.football import League, Team

LEAGUE_ID = os.getenv('LEAGUE_ID')
SWID = os.getenv('SWID')
ESPN_S2 = os.getenv('ESPN_S2')


def extract_team_data(teams: list[Team]) -> dict:
    """Ingest API Team data to database Team schema."""
    extracted_teams = []
    for team in teams:
        team = team.__dict__
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
        extracted_teams.append(team)
    return extracted_teams


if __name__ == '__main__':
    YEAR = 2018
    # league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID)
    with open(f'league_{YEAR}.pkl', 'rb') as inp:
        league = pickle.load(inp)

    print(extract_team_data(league.teams)[0])

    # teams = extract_team_data(league.teams)[0]
    # for k, v in teams.items():
    #     print(k, v)
