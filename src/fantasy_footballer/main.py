"""Source code main file to be called by containerized run file."""
import json
import os

import requests
from espn_api.football import League


def _get_groupme_endpoint(collection: str = '') -> str:
    access_token = '?token=' + os.getenv('ACCESS_TOKEN')
    base_url = 'https://api.groupme.com/v3/'
    return base_url + collection + access_token


if __name__ == '__main__':
    with open('../../resources/league_sw_onethree.json',
              encoding='utf-8') as league_file:
        creds = json.loads(league_file.read())
    league = League(league_id=creds['league_id'],
                    year=2022,
                    espn_s2=creds['espn_s2'],
                    swid=creds['swid'])

    r = requests.get(_get_groupme_endpoint('groups/93229120/messages'))
    print(r.status_code)
    print(r.json()['response'])

#
