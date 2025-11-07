with schedule as (
    select
        owner_team_year_map.owner_id,
        team_weeks.year,
        team_weeks.week                                  as "Week",
        opponent_owner_team_year_map.team_name           as "Team_Name",
        opponent_owner_team_year_map.owner_name          as "Owner",
        case
            when team_weeks.outcome = 'U'
                then ''
            when
                abs(team_weeks.score_for - opponent_weeks.score_for) < 10 and
                team_weeks.outcome = 'W'
                then
                    team_weeks.outcome || 'cw'
            when
                abs(team_weeks.score_for - opponent_weeks.score_for) < 10 and
                team_weeks.outcome = 'L'
                then
                    team_weeks.outcome || 'cl'
            else team_weeks.outcome
        end                                                                       as "Outcome",
        case
            when team_weeks.score_for = 0.0
                then ''
            when shotguns.is_shotgun
                then team_weeks.score_for::varchar || 'sg'
            else team_weeks.score_for::varchar
        end                                                                       as "Points_For",
        if(opponent_weeks.score_for = 0.0, '', opponent_weeks.score_for::varchar) as "Points_Against"
    from {{ ref('stg__team_weeks') }} as team_weeks
    inner join {{ ref('stg__team_weeks') }} as opponent_weeks
        on team_weeks.opponent_team_week_id = opponent_weeks.team_week_id
    left join {{ ref("int__matchup_week_playoff_map") }} as matchup_week_playoff_map
        on
            team_weeks.year = matchup_week_playoff_map.year and
            team_weeks.week = matchup_week_playoff_map.week
    left join {{ ref('int__shotguns') }} as shotguns
        on team_weeks.team_week_id = shotguns.team_week_id
    left join {{ ref('int__owner_team_year_map') }} as owner_team_year_map
        on team_weeks.team_year_id = owner_team_year_map.team_year_id
    left join {{ ref('int__owner_team_year_map') }} as opponent_owner_team_year_map
        on opponent_weeks.team_year_id = opponent_owner_team_year_map.team_year_id
    where not matchup_week_playoff_map.is_playoff
    order by team_weeks.week
)

select *
from schedule
