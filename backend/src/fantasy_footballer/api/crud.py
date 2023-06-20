"""CRUD commands to postgres database."""

from fantasy_footballer.api.models import Team
from fantasy_footballer.api.schemas import TeamSchema
from sqlalchemy.orm import Session


def create_team(db: Session, team: dict):
    """Add Team row to database."""
    db_team = Team(**team)
    db.add(db_team)
    db.commit()
    return db_team


def get_teams(db: Session):
    """Query for teams from database."""
    return db.query(Team).all()


def get_team_by_id(db: Session, team_id: int):
    """Query specific Team given team_id."""
    return db.query(Team).filter(Team.team_id == team_id).first()


def get_leaderboard_by_year(db: Session, year: str):
    """Query database for data within a given year."""
    leaderboard = db.query(Team).where(Team.year == year).all()
    return leaderboard


def get_team_by_name(db: Session, name: int):
    """Query specific Team given name."""
    return db.query(Team).filter(Team.team_name == name
                                 or Team.team_abbrev == name).first()


def get_teams_by_year(db: Session, year: str):
    """Query specific Team given name."""
    return db.query(Team).filter(Team.year == year).all()


# def get_player(db: Session, skip: int = 0, limit: int = 100):
#     """Get player with options to skip and limit results."""
#     return db.query(Player).offset(skip).limit(limit).all()

# def get_player_by_id(db: Session, player_id: int):
#     """Get player given a player_id."""
#     return db.query(Player).filter(Player.playerId == player_id).first()
