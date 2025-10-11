with played_weeks_w_lowest as (
    select
        team_id,
        team_schedule_id,
        year,
        week,
        score_for,
        min(score_for) over (partition by year, week) as week_min_score_for
    from {{ ref('stg_s001__team_schedules') }}
    where outcome != 'U'
)

select
    played_weeks_w_lowest.team_id,
    played_weeks_w_lowest.team_schedule_id,
    teams.owner_name,
    played_weeks_w_lowest.year,
    played_weeks_w_lowest.week,
    played_weeks_w_lowest.score_for < 100 or
    played_weeks_w_lowest.score_for = played_weeks_w_lowest.week_min_score_for as is_shotgun
from played_weeks_w_lowest
inner join {{ ref('stg_s001__teams') }} as teams
    on played_weeks_w_lowest.team_id = teams.team_id
