"""SQLAlchemy models for querying postgres database."""

# from api.database import Base
from sqlalchemy import ARRAY, Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB


class Player():
    """Definition of all fields of players table."""

    __tablename__ = 'players'

    name = Column(String)
    playerId = Column(Integer)
    posRank = Column(Integer)
    eligibleSlots = Column[ARRAY(String)]
    acquisitionType = Column(String)
    proTeam = Column(String)
    onTeamId = Column(Integer)
    position = Column(String)
    injuryStatus = Column(String)
    injured = Column(Boolean)
    total_points = Column(Integer)
    projected_total_points = Column(Integer)
    percent_owned = Column(Integer)
    percent_started = Column(Integer)
    stats: Column(JSONB)


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
    points_for = Column(Integer)
    points_against = Column(Integer)
    acquisitions = Column(Integer)
    acquisition_budget_spent = Column(Integer)
    drops = Column(Integer)
    trades = Column(Integer)
    owner = Column(String)
    streak_type = Column(String)
    streak_length = Column(Integer)
    standing = Column(Integer)
    final_standing = Column(Integer)
    draft_projected_rank = Column(Integer)
    playoff_pct = Column(Integer)
    logo_url = Column(String)
    roster = Column(ARRAY(JSONB))

    # These 3 variables will have the same index and match on those indexes
    schedule: Column(ARRAY(JSONB))
    scores = Column(ARRAY(Integer))
    outcomes = Column(ARRAY(JSONB))
