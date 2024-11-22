select
	teams.owner_name                                                           as "Owner",
	count(*)                                                                   as "Count",
	list_aggr(list_sort(array_agg(schedules.week), 'ASC'), 'string_agg', ', ') as "Weeks"
from {{ ref("stg_s001__team_schedules") }} schedules
join {{ ref("stg_s001__teams") }} teams
on schedules.team_id == teams.team_id
where   schedules.year = {{ modules.datetime.datetime.now().year }}
    and schedules.score_for < 100
    and schedules.outcome != 'U'
group by "Owner"
order by "Count" desc