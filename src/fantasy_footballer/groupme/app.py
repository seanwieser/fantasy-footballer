"""Source code main file to be called by containerized run file."""
import json
import os

import requests

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")


def _get_groupme_endpoint(collection: str = "") -> str:
    access_token = f"?token={ACCESS_TOKEN}"
    base_url = "https://api.groupme.com/v3/"
    return base_url + collection + access_token


def run_app():
    """Python app's top level method."""
    endpoint = _get_groupme_endpoint(f"groups/{GROUP_ID}/messages")
    req = requests.get(endpoint, timeout=120)

    print(req.status_code)

    with open(f"output_{GROUP_ID}.json", "w", encoding="utf-8") as f:
        json.dump(req.json()["response"], f)


if __name__ == "__main__":
    run_app()
