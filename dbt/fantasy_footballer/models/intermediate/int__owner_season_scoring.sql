with reg_season_weeks as (
    select
        team_weeks.team_year_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.score_for
    from {{ ref("stg__team_weeks") }} as team_weeks
    inner join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where
        team_weeks.outcome != 'U' and
        not matchup_week_playoff_map.is_playoff
),

season_scoring as (
    select
        team_year_id,
        year,
        count(week)::int as games_played,
        sum(score_for)::double as reg_points_total,
        (sum(score_for) / count(week))::double as reg_points_per_game,
        max(score_for)::double as best_week_score,
        min(score_for)::double as worst_week_score
    from reg_season_weeks
    group by all
),

owner_season_scoring as (
    select
        owner_team_year_map.owner_id,
        owner_team_year_map.owner_name,
        owner_team_year_map.owner_year_id,
        owner_team_year_map.team_year_id,
        owner_team_year_map.year,
        season_scoring.games_played,
        season_scoring.reg_points_total,
        season_scoring.reg_points_per_game,
        season_scoring.best_week_score,
        season_scoring.worst_week_score,
        team_postseason.made_playoffs
    from {{ ref("int__owner_team_year_map") }} as owner_team_year_map
    inner join season_scoring
        on owner_team_year_map.team_year_id = season_scoring.team_year_id
    inner join {{ ref("int__team_postseason") }} as team_postseason
        on owner_team_year_map.team_year_id = team_postseason.team_year_id
)

select *
from owner_season_scoring
