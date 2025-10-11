with played_weeks_w_lowest as (
    select
        owner_id,
        team_id,
        team_schedule_id,
        year,
        week,
        score_for,
        min(score_for) over (partition by year, week) as week_min_score_for
    from {{ ref('stg_s001__team_schedules') }}
    where outcome != 'U' and not is_playoff
)

select
    played_weeks_w_lowest.owner_id,
    played_weeks_w_lowest.team_id,
    played_weeks_w_lowest.team_schedule_id,
    owner_names.owner_name,
    played_weeks_w_lowest.year,
    played_weeks_w_lowest.week,
    played_weeks_w_lowest.score_for < 100 or
    played_weeks_w_lowest.score_for = played_weeks_w_lowest.week_min_score_for as is_shotgun
from played_weeks_w_lowest
inner join {{ ref("owner_names") }} as owner_names
    on played_weeks_w_lowest.owner_id = owner_names.owner_id
