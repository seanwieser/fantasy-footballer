with schedule as (
    select
        team_schedules.owner_id,
        team_schedules.year,
        team_schedules.week,
        opponent_teams.team_name as opponent,
        nullif(team_schedules.outcome, 'U') as outcome,
        nullif(team_schedules.score_for, 0.0) as "Points For",
        nullif(opponent_schedules.score_for, 0.0) as "Points Against"
    from {{ ref('stg_s001__team_schedules') }} as team_schedules
    inner join {{ ref('stg_s001__team_schedules') }} as opponent_schedules
        on team_schedules.opponent_team_schedule_id = opponent_schedules.team_schedule_id
    inner join {{ ref('stg_s001__teams') }} as opponent_teams
        on opponent_schedules.team_id = opponent_teams.team_id
    where not team_schedules.is_playoff
    order by team_schedules.week
)

select *
from schedule
