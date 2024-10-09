"""SQLAlchemy models for querying postgres database."""
from string import Template

from espn_api.football import League
from inflection import underscore, titleize
from sqlalchemy import ARRAY, Boolean, Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
PLAYER_KEY = Template("${player_id}_${year}")
TEAM_KEY = Template("${first_name}_${last_name}_${year}")


class Player(Base):
    """Definition of all fields of players table."""

    __tablename__ = "players"

    player_key = Column(String, primary_key=True)
    player_id = Column(Integer)
    name = Column(String)
    year = Column(Integer)
    pos_rank = Column(Integer)
    eligible_slots = Column(ARRAY(String))
    acquisition_type = Column(ARRAY(String))
    pro_team = Column(String)
    on_team_id = Column(Integer)
    position = Column(String)
    injury_status = Column(String)
    injured = Column(Boolean)
    total_points = Column(Float)
    projected_total_points = Column(Float)
    percent_owned = Column(Float)
    percent_started = Column(Float)

    # stats: Mapped[list["PlayerStats"]] = relationship(back_populates="player")

    def to_dict(self):
        """Return dictionary of all columns in table."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def transform(cls, league: League) -> list[dict]:
        """Player ingestion extraction and transformations."""
        players = []
        all_player_ids = [player_id for player_id in league.player_map.keys() if isinstance(player_id, int)]
        for idx, player_id in enumerate(all_player_ids):
            player = league.player_info(playerId=player_id)
            if not player:
                continue

            player = {
                underscore(k): v
                for k, v in player.__dict__.items()
                if underscore(k) in cls.__table__.columns.keys()
            }
            player["player_key"] = PLAYER_KEY.substitute(player_id=player_id, year=league.year)
            player["year"] = league.year

            for key in ["injury_status", "pos_rank"]:
                if isinstance(player[key], list):
                    player[key] = None
                elif isinstance(player[key], str):
                    player[key] = player[key].replace("}", "").replace("{", "")

            players.append(player)
            if (idx + 1) % 20 == 0:
                print(f"Players {league.year}: {round(((idx + 1) / len(all_player_ids)) * 100, 2)}%")

        return players


class PlayerStats(Base):
    """Definition of all fields of player_stats table."""

    __tablename__ = "player_stats"

    player_week_stats_key = Column(String, primary_key=True)
    player_key = Column(String)

    player_id = Column(Integer)
    name = Column(String)
    year = Column(Integer)
    week = Column(Integer)

    team_win = Column(Integer)
    points = Column(Float)

    receiving_receptions = Column(Float)
    receiving_yards = Column(Float)
    receiving_targets = Column(Integer)
    receiving_touchdowns = Column(Integer)
    receiving2_pt_conversions = Column(Integer)

    rushing_attempts = Column(Integer)
    rushing_yards = Column(Float)
    rushing_touchdowns = Column(Integer)
    rushing2_pt_conversions = Column(Integer)

    passing_attempts = Column(Integer)
    passing_completions = Column(Integer)
    passing_incompletions = Column(Integer)
    passing_yards = Column(Float)
    passing_touchdowns = Column(Integer)
    passing_completion_percentage = Column(Float)
    passing_times_sacked = Column(Integer)

    fumbles = Column(Integer)
    lost_fumbles = Column(Integer)
    turnovers = Column(Integer)

    made_field_goals_from_40_to_49 = Column(Integer)
    attempted_field_goals_from_40_to_49 = Column(Integer)
    made_field_goals_from_under_40 = Column(Integer)
    attempted_field_goals_from_under_40 = Column(Integer)
    made_field_goals = Column(Integer)
    attempted_field_goals = Column(Integer)
    made_extra_points = Column(Integer)
    attempted_extra_points = Column(Integer)

    def to_dict(self):
        """Return dictionary of all columns in table."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def transform(cls, league: League) -> list[dict]:
        """Player Stats ingestion transformations."""
        all_player_stats = []
        all_player_ids = [player_id for player_id in league.player_map.keys() if isinstance(player_id, int)]
        for idx, player_id in enumerate(all_player_ids):
            player = league.player_info(playerId=player_id)
            if not player:
                continue

            player_stat = {
                "player_key": PLAYER_KEY.substitute(player_id=player_id, year=league.year),
                "year": league.year
            }
            player_stat = player_stat | {
                underscore(k): v
                for k, v in player.__dict__.items()
                if underscore(k) in cls.__table__.columns.keys()
            }

            for week, stat in player.__dict__.get("stats", {}).items():
                player_stat = player_stat | {k: v for k, v in stat.items() if k in cls.__table__.columns.keys()}
                player_stat["player_week_stats_key"] = f"{player_stat['player_key']}_{week}"
                player_stat["week"] = week
                for field, value in stat.get("breakdown", {}).items():
                    if underscore(field) in cls.__table__.columns.keys():
                        player_stat[underscore(field)] = value
                all_player_stats.append(player_stat)
            if (idx + 1) % 20 == 0:
                percent_complete = round(((idx + 1) / len(all_player_ids)) * 100, 2)
                print(f"Player Stats {league.year}: {percent_complete}%")
        return all_player_stats


class Team(Base):
    """Definition of all fields of teams table."""

    __tablename__ = "teams"

    team_key = Column(String, primary_key=True)
    team_id = Column(Integer)
    owner = Column(String)
    display_name = Column(String)

    year = Column(Integer)
    team_abbrev = Column(String)
    team_name = Column(String)
    division_id = Column(Integer)
    division_name = Column(String)
    wins = Column(Integer)
    losses = Column(Integer)
    ties = Column(Integer)
    points_for = Column(Float)
    points_against = Column(Float)
    acquisitions = Column(Integer)
    acquisition_budget_spent = Column(Integer)
    drops = Column(Integer)
    trades = Column(Integer)
    streak_type = Column(String)
    streak_length = Column(Integer)
    standing = Column(Integer)
    final_standing = Column(Integer)
    draft_projected_rank = Column(Integer)
    playoff_pct = Column(Integer)

    # roster = Column(ARRAY(String)) # TODO: Fix roster field. The value is at fetch time and not at per week

    def to_dict(self):
        """Return dictionary of all columns in table."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def transform(cls, league: League) -> list[dict]:
        """Team ingestion transformations."""
        new_teams = []
        for team in league.teams:
            team = team.__dict__

            first_name = underscore(team["owners"][0]["firstName"]).strip()
            last_name = underscore(team["owners"][0]["lastName"]).strip()
            team["owner"] = f"{first_name}_{last_name}"
            team["display_name"] = titleize(f"{first_name} {last_name}")
            team["team_key"] = TEAM_KEY.substitute(first_name=first_name, last_name=last_name, year=league.year)
            team["year"] = league.year
            # team["roster"] = [PLAYER_KEY.substitute(player_id=player.__dict__["playerId"], year=league.year) for player
            #                   in team["roster"]]

            team = {
                underscore(k): v
                for k, v in team.items()
                if underscore(k) in cls.__table__.columns.keys()
            }
            team.update({
                k: round(v, 4)
                for k, v in team.items() if isinstance(v, float)
            })
            new_teams.append(team)
        return new_teams


class TeamSchedules(Base):
    """Definition of all fields of team_schedules table."""

    __tablename__ = "team_schedules"

    team_schedule_week_key = Column(String, primary_key=True)
    team_key = Column(String)

    week = Column(Integer)
    year = Column(Integer)
    outcome = Column(String)
    score_for = Column(Float)
    opponent_schedule_week_key = Column(String)
    opponent_team_key = Column(String)

    # TODO: Add lineup field

    def to_dict(self):
        """Return dictionary of all columns in table."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def transform(cls, league: League) -> list[dict]:
        """Team ingestion transformations."""
        schedule_rows = []
        for team in league.teams:
            team = team.__dict__
            for week_num in range(len(team["schedule"])):
                schedule_row = dict()
                schedule_row["team_key"] = TEAM_KEY.substitute(
                    first_name=underscore(team["owners"][0]["firstName"]).strip(),
                    last_name=underscore(team["owners"][0]["lastName"]).strip(),
                    year=league.year
                )
                schedule_row["week"] = week_num + 1
                schedule_row["team_schedule_week_key"] = f"{schedule_row['team_key']}_{schedule_row['week']}"
                schedule_row["year"] = league.year
                schedule_row["outcome"] = team["outcomes"][week_num]
                schedule_row["score_for"] = round(team["scores"][week_num], 4)

                opponent = team["schedule"][week_num].__dict__
                schedule_row["opponent_team_key"] = TEAM_KEY.substitute(
                    first_name=underscore(opponent["owners"][0]["firstName"]).strip(),
                    last_name=underscore(opponent["owners"][0]["lastName"]).strip(),
                    year=league.year
                )
                schedule_row[
                    "opponent_schedule_week_key"] = f"{schedule_row['opponent_team_key']}_{schedule_row['week']}"
                schedule_rows.append(schedule_row)
        return schedule_rows
