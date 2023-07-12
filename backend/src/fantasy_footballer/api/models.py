"""SQLAlchemy models for querying postgres database."""

# from api.database import Base
from sqlalchemy import ARRAY, Boolean, Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


class Player(Base):
    """Definition of all fields of players table."""

    __tablename__ = 'players'

    player_id = Column(String, primary_key=True)

    name = Column(String)
    year = Column(String)
    pos_rank = Column(Integer)
    eligible_slots = Column(ARRAY(String))
    acquisition_type = Column(String)
    pro_team = Column(String)
    on_team_id = Column(Integer)
    position = Column(String)
    injury_status = Column(String)
    injured = Column(Boolean)
    total_points = Column(Float)
    projected_total_points = Column(Float)
    percent_owned = Column(Float)
    percent_started = Column(Float)
    stats = Column(JSONB)


class Team(Base):
    """Definition of all fields of teams table."""

    __tablename__ = 'teams'

    team_id = Column(String, primary_key=True)

    year = Column(String)
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
    roster = Column(Integer)  # relationship("Player", back_populates="teams")
    schedule = Column(ARRAY(JSONB))
