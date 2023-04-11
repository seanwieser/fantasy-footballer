"""Module to fetch data from espn_api."""

import os

from espn_api.football import League

LEAGUE_ID = os.getenv('LEAGUE_ID')
SWID = os.getenv('SWID')
ESPN_S2 = os.getenv('ESPN_S2')


def fetch_members(year: int) -> list[str]:
    """Use espn_api to get league information then returns members given a year."""
    league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID)
    return [team.owner for team in league.teams]
