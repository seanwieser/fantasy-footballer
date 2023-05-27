"""Initial population of database."""

# import pickle

# from api.crud import create_team
# from espn_api.football import League, Team
# from fetcher.fetcher import extract_team_data

# def get_raw_data(year: int):
#     with open(f'league_{year}', 'rb') as raw_data:
#         league = pickle.load(raw_data)
#     return league

# def fill_teams_table(teams: list[Team]):
#     transformed_teams = extract_team_data(teams)
#     for team in transformed_teams:
#         create_team(team=team)

# if __name__ == '__main__':
#     league: League = get_raw_data(year=2018)
#     fill_teams_table(league.teams)
