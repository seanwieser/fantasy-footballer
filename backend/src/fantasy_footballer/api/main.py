"""Module that contains the backend API."""

from api import crud, models, schemas
from api.database import SessionLocal, engine
from api.models import Team
from api.schemas import Response, TeamSchema
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


# @app.get("/")
# def read_root(db: Session = Depends(get_db)):
#     """Root path"""
#     """Root of API."""
#     return crud.get_team_by_name(db=db, name='cmag')


@app.get("/teams/")
def read_teams(skip: int = 0, limit: int = 0, db: Session = Depends(get_db)):
    """Get list of all teams."""
    teams = crud.get_teams(db, skip=skip, limit=limit)
    return teams


@app.get("/teams/{name}/")
def read_team(name: str, db: Session = Depends(get_db)):
    """Get team by name endpoint."""
    team = crud.get_team_by_name(db=db, name=name)
    return team


@app.post("/teams/")
def create_team(team: dict, db: Session = Depends(get_db)):
    """Create team post."""
    # db_team = crud.get_team_by_id(db, id=team.team_id)
    # if db_team:
    #     raise HTTPException(status_code=400, detail="Team already registered")
    return crud.create_team(db=db, team=team)


# @app.get("/members/{year}")
# async def read_page(year: int) -> list[str]:
#     """Path parameter example."""
#     return fetch_members(year)
