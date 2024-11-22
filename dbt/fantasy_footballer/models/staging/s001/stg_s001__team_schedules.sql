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
		unnest(schedule_flat),
	from team_schedules_unnested
),
team_schedules_with_opponent_ids as (
	select
		schedules.team_id || '_' || schedules.week as team_schedule_id,
		schedules.owner_id                         as owner_id,
		schedules.team_id                          as team_id,
		schedules.year                             as year,
		schedules.week                             as week,
		schedules.score_for                        as score_for,
		schedules.outcome                          as outcome,
		opponents.team_id                          as opponent_team_id,
		opponents.team_id || '_' || week           as opponent_team_schedule_id,
		(schedules.year < 2021 and schedules.week >= 14) or (schedules.year >= 2021 and schedules.week >= 15) as is_playoff
	from team_schedules_expanded schedules
	join {{ ref("stg_s001__teams") }} opponents
	on opponents.team_name = schedules.opponent and opponents.year = schedules.year
)
select *
from team_schedules_with_opponent_ids