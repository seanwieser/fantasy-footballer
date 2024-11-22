with team_schedules_unnested as (
    select
        owner_id,
        team_id,
        year,
        unnest(schedule_raw) as schedule_flat
    from {{ ref("stg_s001__teams") }}
),

team_schedules_expanded as (
    select
        owner_id,
        team_id,
        year,
        unnest(schedule_flat) -- noqa
    from team_schedules_unnested
),

team_schedules_with_opponent_ids as (
    select
        schedules.owner_id,
        schedules.team_id,
        schedules.year,
        schedules.week,
        schedules.score_for,
        schedules.outcome,
        opponents.team_id as opponent_team_id,
        schedules.team_id || '_' || schedules.week as team_schedule_id,
        opponents.team_id || '_' || opponents.week as opponent_team_schedule_id,
        (schedules.year < 2021 and schedules.week >= 14) or
        (schedules.year >= 2021 and schedules.week >= 15) as is_playoff
    from team_schedules_expanded as schedules
    inner join {{ ref("stg_s001__teams") }} as opponents
        on schedules.opponent = opponents.team_name and schedules.year = opponents.year
)

select *
from team_schedules_with_opponent_ids
