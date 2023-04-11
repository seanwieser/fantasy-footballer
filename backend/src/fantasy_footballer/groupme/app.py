"""Source code main file to be called by containerized run file."""
import os

import requests
from espn_api.football import League

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
LEAGUE_ID = os.getenv('LEAGUE_ID')
SWID = os.getenv('SWID')
ESPN_S2 = os.getenv('ESPN_S2')


def _get_groupme_endpoint(collection: str = '') -> str:
    access_token = f'?token={ACCESS_TOKEN}'
    base_url = 'https://api.groupme.com/v3/'
    return base_url + collection + access_token


def run_app():
    """Python app's top level method."""
    league = League(league_id=LEAGUE_ID, year=2022, espn_s2=ESPN_S2, swid=SWID)
    if league:
        pass

    endpoint = _get_groupme_endpoint('groups/93229120/messages')
    req = requests.get(endpoint, timeout=120)

    print(req.status_code)
    print(req.json()['response'])
