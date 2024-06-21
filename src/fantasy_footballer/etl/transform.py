from database.models import Team
from espn_api.football import League
from inflection import underscore


def transform_teams(raw_teams: list[Team], year: str) -> list[dict]:
    """Team ingestion transformations."""
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


def transform_players(league: League) -> list[dict]:
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
    for idx, pick in enumerate(league.draft):
        pick = pick.__dict__

        player = league.player_info(playerId=pick["playerId"])
        player = player.__dict__
        player["year"] = league.year
        #
        # for week in player["stats"].keys():
        #     stats[week] = {}
        #     stats[week]['points'] = player['stats'][week]['points']
        #     for field in player_stat_fields:
        #         if field in player['stats'][week]['breakdown'].keys():
        #             stats[week][field] = player['stats'][week]['breakdown'][field]
        player["stats"] = {}

        player = {underscore(k): v for k, v in player.items()}

        pick = {
            k: v
            for k, v in pick.items()
            if k in ["round_num", "round_pick", "bid_amount"]
        }
        players.append(player | pick)

    return players
