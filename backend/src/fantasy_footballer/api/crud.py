"""CRUD commands to postgres database."""

from api.models import Player
# from api.schemas import PlayerSchema
from sqlalchemy.orm import Session


def get_player(db: Session, skip: int = 0, limit: int = 100):
    """Get player with options to skip and limit results."""
    return db.query(Player).offset(skip).limit(limit).all()


def get_player_by_id(db: Session, player_id: int):
    """Get player given a player_id."""
    return db.query(Player).filter(Player.playerId == player_id).first()
