CREATE TABLE teams (
    team_id int PRIMARY KEY,

    team_abbrev text,
    team_name text,
    division_id text,
    division_name text,
    wins  integer,
    losses  integer,
    ties  integer,
    points_for  decimal,
    points_against  decimal,
    acquisitions  integer,
    acquisition_budget_spent  integer,
    drops  integer,
    trades  integer,
    owner text,
    streak_type text,
    streak_length  integer,
    standing  integer,
    final_standing  integer,
    draft_projected_rank  integer,
    playoff_pct  integer,
    roster int[],
    schedule: jsonb[]
);

INSERT INTO teams(team_id, team_abbrev, team_name) VALUES('1', 'nickname', 'fullname');