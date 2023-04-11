"""Source code main file to be called by containerized run file."""
import os

import requests

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')


def _get_groupme_endpoint(collection: str = '') -> str:
    access_token = f'?token={ACCESS_TOKEN}'
    base_url = 'https://api.groupme.com/v3/'
    return base_url + collection + access_token


def run_app():
    """Python app's top level method."""
    endpoint = _get_groupme_endpoint('groups/93229120/messages')
    req = requests.get(endpoint, timeout=120)

    print(req.status_code)
    print(req.json()['response'])
