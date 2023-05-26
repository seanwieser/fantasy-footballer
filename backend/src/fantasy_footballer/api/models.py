"""SQLAlchemy models for querying postgres database."""

# from api.database import Base
from sqlalchemy import ARRAY, Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB


class Player():
    """Definition of all fields of players table."""

    __tablename__ = 'players'

    name = Column(String)
    playerId = Column(Integer)
    posRank = Column(Integer)  # players positional rank
    eligibleSlots = Column[ARRAY(String)]  # example ['WR', 'WR/TE/RB']
    acquisitionType = Column(String)
    proTeam = Column(String)  # 'PIT' or 'LAR'
    onTeamId = Column(Integer)  # id of fantasy team
    position = Column(String)  # main position like 'TE' or 'QB'
    injuryStatus = Column(String)
    injured = Column(Boolean)
    total_points = Column(Integer)  # players total points during the season
    projected_total_points = Column(
        Integer)  # projected player points for the season
    percent_owned = Column(Integer)  # percentage player is rostered
    percent_started = Column(Integer)  # percentage player is started
    stats: Column(JSONB)  # holds each week stats, actual and projected points.


class Teams():
    """Definition of all fields of teams table."""

    __tablename__ = 'teams'

    team_id = Column(Integer, primary_key=True)

    team_abbrev = Column(String)
    team_name = Column(String)
    division_id = Column(String)
    division_name = Column(String)
    wins = Column(Integer)
    losses = Column(Integer)
    ties = Column(Integer)
    points_for = Column(Integer)  # total points for through out the season
    points_against = Column(
        Integer)  # total points against through out the season
    acquisitions = Column(Integer)  # number of acquisitions made by the team
    acquisition_budget_spent = Column(Integer)  # budget spent on acquisitions
    drops = Column(Integer)  # number of drops made by the team
    trades = Column(Integer)  # number of trades made by the team
    owner = Column(String)
    streak_type = Column(String)  # string of either WIN or LOSS
    streak_length = Column(Integer)  # how long the streak is for streak type
    standing = Column(Integer)  # standing before playoffs
    final_standing = Column(Integer)  # final standing at end of season
    draft_projected_rank = Column(Integer)  # projected rank after draft
    playoff_pct = Column(Integer)  # teams projected chance to make playoffs
    logo_url = Column(String)
    roster = Column(ARRAY(JSONB))

    # These 3 variables will have the same index and match on those indexes
    schedule: Column(ARRAY(JSONB))
    scores = Column(ARRAY(Integer))
    outcomes = Column(ARRAY(JSONB))
