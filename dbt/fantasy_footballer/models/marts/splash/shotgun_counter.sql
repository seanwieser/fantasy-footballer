with shotgun_counter as (
    select
        teams.owner_name                                                           as "Owner",
        count(*)                                                                   as "Count",
        list_aggr(list_sort(array_agg(schedules.week), 'ASC'), 'string_agg', ', ') as "Weeks"
    from {{ ref("stg_s001__team_schedules") }} as schedules
    inner join {{ ref("stg_s001__teams") }} as teams
        on schedules.team_id = teams.team_id
    cross join {{ ref("current_year") }} as current_year
    where
        schedules.year = current_year.this and
        schedules.score_for < 100 and
        schedules.outcome != 'U'
    group by teams.owner_name
    order by "Count" desc
)

select *
from shotgun_counter
