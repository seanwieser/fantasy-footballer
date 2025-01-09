select
    teams.owner_id,
    teams.owner_name,
    schedules.year,
    schedules.week
from {{ ref("stg_s001__team_schedules") }}  as schedules
inner join {{ ref("stg_s001__teams") }}     as teams
    on schedules.team_id = teams.team_id
where
    schedules.score_for < 100 and
    schedules.outcome != 'U'
