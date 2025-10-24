with schedule as (
    select
        team_matchups.owner_id,
        team_matchups.year,
        team_matchups.week                                  as "Week",
        opponent_teams.team_name                            as "Team_Name",
        opponent_teams.owner_name                           as "Owner",
        case
            when team_matchups.outcome = 'U'
                then ''
            when
                abs(team_matchups.score_for - opponent_matchups.score_for) < 10 and
                team_matchups.outcome = 'W'
                then
                    team_matchups.outcome || 'cw'
            when
                abs(team_matchups.score_for - opponent_matchups.score_for) < 10 and
                team_matchups.outcome = 'L'
                then
                    team_matchups.outcome || 'cl'
            else team_matchups.outcome
        end                                                                             as "Outcome",
        case
            when team_matchups.score_for = 0.0
                then ''
            when shotguns.is_shotgun
                then team_matchups.score_for::varchar || 'sg'
            else team_matchups.score_for::varchar
        end                                                                             as "Points_For",
        if(opponent_matchups.score_for = 0.0, '', opponent_matchups.score_for::varchar) as "Points_Against"
    from {{ ref('stg__team_matchups') }} as team_matchups
    inner join {{ ref('stg__team_matchups') }} as opponent_matchups
        on team_matchups.opponent_owner_matchup_id = opponent_matchups.owner_matchup_id
    inner join {{ ref('stg__teams') }} as opponent_teams
        on opponent_matchups.owner_year_id = opponent_teams.owner_year_id
    left join {{ ref('int_shotguns') }} as shotguns
        on team_matchups.owner_matchup_id = shotguns.owner_matchup_id
    where not team_matchups.is_playoff
    order by team_matchups.week
)

select *
from schedule
