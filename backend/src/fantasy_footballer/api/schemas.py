"""Pydantic schemas for FastAPI inputs and outputs."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar('T')


class PlayerSchema(BaseModel):
    """Schema containing all fields of a row in the Players table."""

    name: Optional[str] = None
    year: Optional[str] = None
    player_id: Optional[str] = None
    pos_rank: Optional[int] = None
    eligible_slots: Optional[list[str]] = None
    acquisition_type: Optional[str] = None
    pro_team: Optional[str] = None
    on_team_id: Optional[int] = None
    position: Optional[str] = None
    injury_status: Optional[str] = None
    injured: Optional[bool] = None
    total_points: Optional[float] = None
    projected_total_points: Optional[float] = None
    percent_owned: Optional[float] = None
    percent_started: Optional[float] = None
    stats: Optional[dict] = None

    class Config:
        """Subclass of PlayerSchema to envable orm mode."""

        orm_mode = True


class RequestPlayer(BaseModel):
    """Request class for the PlayerSchema."""

    parameter: PlayerSchema = Field(...)


class TeamSchema(BaseModel):
    """Definition of all fields of teams table."""

    team_id: str

    team_abbrev: Optional[str] | None = None
    year: Optional[str] | None = None
    team_name: Optional[str] | None = None
    division_id: Optional[str] | None = None
    division_name: Optional[str] | None = None
    wins: Optional[int] | None = None
    losses: Optional[int] | None = None
    ties: Optional[int] | None = None
    points_for: Optional[int] | None = None
    points_against: Optional[int] | None = None
    acquisitions: Optional[int] | None = None
    acquisition_budget_spent: Optional[int] | None = None
    drops: Optional[int] | None = None
    trades: Optional[int] | None = None
    owner: Optional[str] | None = None
    streak_type: Optional[str] | None = None
    streak_length: Optional[int] | None = None
    standing: Optional[int] | None = None
    final_standing: Optional[int] | None = None
    draft_projected_rank: Optional[int] | None = None
    playoff_pct: Optional[int] | None = None
    logo_url: Optional[str] | None = None
    roster: Optional[list[int]] | None = None
    schedule: Optional[list[dict]] | None = None

    class Config:
        """Subclass of TeamSchema to envable orm mode."""

        orm_mode = True


class Response(GenericModel, Generic[T]):
    """Generic response class."""

    code: str
    status: str
    message: str
    results: Optional[T]
