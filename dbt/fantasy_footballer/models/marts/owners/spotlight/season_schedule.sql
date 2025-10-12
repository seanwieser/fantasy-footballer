with schedule as (
    select
        team_schedules.owner_id,
        team_schedules.year,
        team_schedules.week                                 as "Week",
        opponent_teams.team_name                            as "Team Name",
        opponent_teams.owner_name                           as "Owner",
        case
            when team_schedules.outcome = 'U'
                then ''
            when
                abs(team_schedules.score_for - opponent_schedules.score_for) < 10 and
                team_schedules.outcome = 'W'
                then
                    team_schedules.outcome || 'cw'
            when
                abs(team_schedules.score_for - opponent_schedules.score_for) < 10 and
                team_schedules.outcome = 'L'
                then
                    team_schedules.outcome || 'cl'
            else team_schedules.outcome
        end                                                                                 as "Outcome",
        case
            when team_schedules.score_for = 0.0
                then ''
            when shotguns.is_shotgun
                then team_schedules.score_for::varchar || 'sg'
            else team_schedules.score_for::varchar
        end                                                                                 as "Points For",
        if(opponent_schedules.score_for = 0.0, '', opponent_schedules.score_for::varchar)   as "Points Against"
    from {{ ref('stg_s001__team_schedules') }} as team_schedules
    inner join {{ ref('stg_s001__team_schedules') }} as opponent_schedules
        on team_schedules.opponent_team_schedule_id = opponent_schedules.team_schedule_id
    inner join {{ ref('stg_s001__teams') }} as opponent_teams
        on opponent_schedules.team_id = opponent_teams.team_id
    left join {{ ref('int_shotguns') }} as shotguns
        on team_schedules.team_schedule_id = shotguns.team_schedule_id
    where not team_schedules.is_playoff
    order by team_schedules.week
)

select *
from schedule
