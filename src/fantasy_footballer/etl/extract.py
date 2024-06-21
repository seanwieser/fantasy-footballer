"""Module to fetch data from espn_api."""

from espn_api.football import League, Team


def extract_year(league_id: str, espn_s2: str, swid: str,
                 year: int) -> list[Team] | None:
    """Return team object from pickle file."""
    league = None
    try:
        league = League(league_id=int(league_id),
                        year=year,
                        espn_s2=espn_s2,
                        swid=swid)
    except Exception as e:
        print(f"Error fetching league {year}: {e}")
    return league
