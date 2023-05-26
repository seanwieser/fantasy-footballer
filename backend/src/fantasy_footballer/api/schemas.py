"""Pydantic schemas for FastAPI inputs and outputs."""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generic import GenericModel

T = TypeVar('T')


class PlayerSchema(BaseModel):
    """Schema containing all fields of a row in the Players table."""

    name: Optional[str] = None
    playerId: Optional[int] = None
    posRank: Optional[int] = None  # players positional rank
    eligibleSlots = Optional[List[str]]  # example ['WR', 'WR/TE/RB']
    acquisitionType: Optional[str] = None
    proTeam: Optional[str] = None  # 'PIT' or 'LAR'
    onTeamId: Optional[int] = None  # id of fantasy team
    position: Optional[str] = None  # main position like 'TE' or 'QB'
    injuryStatus: Optional[str] = None
    injured: Optional[bool] = None
    total_points: Optional[
        int] = None  # players total points during the season
    projected_total_points: Optional[
        int] = None  # projected player points for the season
    percent_owned: Optional[int] = None  # percentage player is rostered
    percent_started: Optional[int] = None  # percentage player is started
    stats: Optional[
        dict] = None  # holds each week stats, actual and projected points.

    class Config:
        """Subclass of PlayerSchema to envable orm mode."""

        orm_mode = True


class RequestPlayer(BaseModel):
    """Request class for the PlayerSchema."""

    parameter: PlayerSchema = Field(...)


class Response(GenericModel, Generic[T]):
    """Generic response class."""

    code: str
    status: str
    message: str
    results: Optional[T]
