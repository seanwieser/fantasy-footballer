with schedule as (
    select
        owner_id,
        year,
        week as "Week",
        opponent_team_name as "Team_Name",
        opponent_owner_name as "Owner",
        case
            when outcome = 'U' then ''
            when is_clutch and outcome = 'W' then outcome || 'cw'
            when is_clutch and outcome = 'L' then outcome || 'cl'
            else outcome
        end as "Outcome",
        case
            when score_for = 0.0 then ''
            when is_shotgun then score_for::varchar || 'sg'
            else score_for::varchar
        end as "Points_For",
        if(score_against = 0.0, '', score_against::varchar) as "Points_Against"
    from {{ ref("int__team_week_results") }}
    where not is_playoff
    order by week
)

select *
from schedule
