"""Module that contains the backend API."""

from fantasy_footballer.api import crud, models, schemas
from fantasy_footballer.api.database import SessionLocal, engine
from fantasy_footballer.api.models import Team
from fantasy_footballer.api.schemas import PlayerSchema, Response, TeamSchema
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

app = FastAPI()


def get_db():
    """Yield db."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/teams/by_name_year/", response_model=TeamSchema)
def read_team_by_name_year(name: str = "",
                           year: str = "",
                           db: Session = Depends(get_db)):
    """Get fantasy team by name and year endpoint."""
    team = crud.get_team_by_name_year(db=db, name=name, year=year)
    return team


@app.get("/teams/by_year/{year}/", response_model=list[TeamSchema])
def read_teams_by_year(year: str, db: Session = Depends(get_db)):
    """Get all fantasy teams for a particular year."""
    teams = crud.get_teams_by_year(db=db, year=year)
    return teams


@app.get("/players/by_year/{year}/", response_model=list[PlayerSchema])
def read_players_by_year(year: str, db: Session = Depends(get_db)):
    """Get all players for a particular year."""
    player = crud.get_players_by_year(db=db, year=year)
    return player


@app.get("/players/by_name_year/", response_model=PlayerSchema)
def read_player_by_name_year(name: str = "",
                             year: str = "",
                             db: Session = Depends(get_db)):
    """Get player data by name and year."""
    player = crud.get_player_by_name_year(db=db, name=name, year=year)
    return player


@app.get("/players/by_name_year_week/")
def read_player_by_name_year_week(name: str = "",
                                  year: str = "",
                                  week: str = "",
                                  db: Session = Depends(get_db)):
    """Get player data by name, year, and week."""
    player = crud.get_player_by_name_year(db=db, name=name, year=year)
    return player.stats[week]
