"""CRUD commands to postgres database."""

from fantasy_footballer.api.models import Player, Team
from fantasy_footballer.api.schemas import TeamSchema
from sqlalchemy.orm import Session


def create_team(db: Session, team: dict):
    """Add Team row to database."""
    db_team = Team(**team)
    db.add(db_team)
    db.commit()
    return db_team


def get_team_by_name_year(db: Session, name: str, year: str):
    """Query specific Team given team_id."""
    return db.query(Team).filter(Team.team_id == f"{name}_{year}").first()


def get_teams_by_year(db: Session, year: str):
    """Query specific Team given name."""
    return db.query(Team).filter(Team.year == year).all()


def get_players_by_year(db: Session, year: str):
    """Query for all players that match given year."""
    return db.query(Player).filter(Player.year == year).all()


def get_player_by_name_year(db: Session, name: str, year: str):
    """Query for single player that matches given name and year."""
    return db.query(Player).filter(Player.player_id == f"{name}_{year}"
                                   and Player.year == year).first()
