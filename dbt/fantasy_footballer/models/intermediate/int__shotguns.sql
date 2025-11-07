with played_weeks_w_lowest as (
    select
        team_weeks.team_id,
        team_weeks.team_year_id,
        team_weeks.team_week_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.score_for,
        min(team_weeks.score_for) over (partition by team_weeks.year, team_weeks.week) as week_min_score_for
    from {{ ref("stg__team_weeks") }} as team_weeks
    left join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    where
        team_weeks.outcome != 'U' and
        not matchup_week_playoff_map.is_playoff
)

select
    team_id,
    team_year_id,
    team_week_id,
    year,
    week,
    score_for < 100 or score_for = week_min_score_for as is_shotgun
from played_weeks_w_lowest
