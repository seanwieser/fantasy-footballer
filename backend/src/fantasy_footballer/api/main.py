"""Module that contains the backend API."""

from fantasy_footballer.api import crud, models, schemas
from fantasy_footballer.api.database import SessionLocal, engine
from fantasy_footballer.api.models import Team
from fantasy_footballer.api.schemas import Response, TeamSchema
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


@app.get("/teams/", response_model=list[TeamSchema])
def read_teams(db: Session = Depends(get_db)):
    """Get list of all teams."""
    teams = crud.get_teams(db)
    return teams


@app.get("/teams/name/{name}/", response_model=TeamSchema)
def read_team(name: str, db: Session = Depends(get_db)):
    """Get team by name endpoint."""
    team = crud.get_team_by_name(db=db, name=name)
    return team


@app.get("/teams/year/{year}/", response_model=list[TeamSchema])
def read_team_by_year(year: str, db: Session = Depends(get_db)):
    """Get team data for a particular year."""
    teams = crud.get_teams_by_year(db=db, year=year)
    return teams


@app.get("/teams/leaderboard/{year}/")
def read_leaderboard_by_year(year: str, db: Session = Depends(get_db)):
    """Get ranking of owners for a particular year."""
    teams = crud.get_leaderboard_by_year(db=db, year=year)
    return teams
