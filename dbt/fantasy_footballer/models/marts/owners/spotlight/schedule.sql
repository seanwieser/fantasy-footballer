with schedule as (
    select
        team_schedules.owner_id,
        team_schedules.year,
        team_schedules.week                       as "Week",
        opponent_teams.team_name                  as "Opponent",
        nullif(team_schedules.outcome, 'U')       as "Outcome",
        nullif(team_schedules.score_for, 0.0)     as "Points For",
        nullif(opponent_schedules.score_for, 0.0) as "Points Against"
    from {{ ref('stg_s001__team_schedules') }} team_schedules
    join {{ ref('stg_s001__team_schedules') }} opponent_schedules
    on team_schedules.opponent_team_schedule_id=opponent_schedules.team_schedule_id
    join {{ ref('stg_s001__teams') }} opponent_teams
    on opponent_teams.team_id = opponent_schedules.team_id
    where not team_schedules.is_playoff
    order by team_schedules.week
)
select *
from schedule