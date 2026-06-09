"""
Diagnostic: probe whether ESPN still exposes pre-2018 league data.

Reads LEAGUE_ID, ESPN_S2, SWID from the environment (same as the extractor in
backend/sources/s001/extract.py). For each season it tries the espn_api League() AND a raw
leagueHistory HTTP call, reporting what comes back. 2018 acts as a known-good control.

If the league was rebuilt in 2018, 2015-2017 live under a DIFFERENT league id — pass it with
--league-id to test that hypothesis without touching the default LEAGUE_ID.

Usage:
    poetry run python3 scripts/probe_espn_history.py
    poetry run python3 scripts/probe_espn_history.py --league-id 123456 --years 2015 2016 2017
"""

import argparse
import os

import requests
from espn_api.football import League

LEAGUE_HISTORY_URL = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"


def probe_espn_api(year, league_id, espn_s2, swid):
    """Try espn_api's League() for one season and summarize the result."""
    try:
        league = League(year=year, league_id=league_id, espn_s2=espn_s2, swid=swid)
        teams = getattr(league, "teams", [])
        name = getattr(getattr(league, "settings", None), "name", "?")
        return f"OK — {len(teams)} teams; league name={name!r}"
    except Exception as err:  # pylint: disable=broad-exception-caught
        return f"FAILED — {type(err).__name__}: {err}"


def probe_raw(year, league_id, espn_s2, swid):
    """Hit the raw leagueHistory endpoint for one season and summarize the response."""
    cookies = {"espn_s2": espn_s2, "SWID": swid} if espn_s2 and swid else {}
    try:
        resp = requests.get(
            LEAGUE_HISTORY_URL.format(league_id=league_id),
            params={"seasonId": year},
            cookies=cookies,
            timeout=30,
        )
        items = None
        try:
            data = resp.json()
            items = len(data) if isinstance(data, list) else 1
        except ValueError:
            items = "non-json"
        preview = resp.text[:100].replace("\n", " ")
        return f"HTTP {resp.status_code}; json_items={items}; preview={preview!r}"
    except Exception as err:  # pylint: disable=broad-exception-caught
        return f"FAILED — {type(err).__name__}: {err}"


def main():
    """Parse args and probe each requested season via both methods."""
    parser = argparse.ArgumentParser(description="Probe ESPN for historical league data.")
    parser.add_argument(
        "--league-id",
        type=int,
        default=None,
        help="Override LEAGUE_ID (to test an old/rebuilt league).",
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2015, 2016, 2017, 2018],
        help="Seasons to probe (2018 is a known-good control).",
    )
    args = parser.parse_args()

    league_id = args.league_id or int(os.environ["LEAGUE_ID"])
    espn_s2, swid = os.getenv("ESPN_S2"), os.getenv("SWID")
    print(f"Probing league_id={league_id} for years {args.years}\n")

    for year in args.years:
        print(f"[{year}]")
        print(f"  espn_api League(): {probe_espn_api(year, league_id, espn_s2, swid)}")
        print(f"  raw leagueHistory: {probe_raw(year, league_id, espn_s2, swid)}")
        print()


if __name__ == "__main__":
    main()
