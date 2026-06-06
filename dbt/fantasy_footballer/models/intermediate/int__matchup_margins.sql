with reg_season_team_weeks as (
    select
        team_weeks.team_week_id,
        team_weeks.team_year_id,
        team_weeks.opponent_team_week_id,
        team_weeks.opponent_team_year_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.score_for,
        team_weeks.outcome
    from {{ ref("stg__team_weeks") }} as team_weeks
    inner join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where
        team_weeks.outcome != 'U' and
        not matchup_week_playoff_map.is_playoff
),

-- Collapse the two per-team rows of each game into a single row. Keep the winner's row; for
-- ties (no winner) keep the lower team_year_id deterministically.
games as (
    select
        team_weeks.year,
        team_weeks.week,
        team_weeks.team_week_id,
        team_weeks.team_year_id as winner_team_year_id,
        team_weeks.opponent_team_year_id as loser_team_year_id,
        team_weeks.score_for as winner_score,
        opponent_weeks.score_for as loser_score,
        abs(team_weeks.score_for - opponent_weeks.score_for) as margin,
        team_weeks.outcome = 'T' as is_tie
    from reg_season_team_weeks as team_weeks
    inner join reg_season_team_weeks as opponent_weeks
        on team_weeks.opponent_team_week_id = opponent_weeks.team_week_id
    where
        team_weeks.outcome = 'W'
        or (team_weeks.outcome = 'T' and team_weeks.team_year_id < team_weeks.opponent_team_year_id)
)

select
    year,
    week,
    team_week_id,
    winner_team_year_id,
    loser_team_year_id,
    winner_score,
    loser_score,
    margin,
    is_tie
from games
