-- Team-season postseason status: which bracket the team entered, whether they made the
-- (winners) playoffs, and final placement reconstructed from bracket progression. ESPN
-- final_standing is carried through to validate the reconstruction for places 1-3
-- (see tests/assert_postseason_placements_match_espn.sql).
with team_brackets as (
    select distinct
        team_year_id,
        bracket
    from {{ ref("int__postseason_team_weeks") }}
),

placements as (
    select
        team_year_id,
        bool_or(is_championship_game and outcome = 'W') as is_champion,
        bool_or(is_championship_game and outcome = 'L') as is_runner_up,
        bool_or(is_third_place_game and outcome = 'W') as is_third,
        bool_or(is_toilet_game and postseason_week_num = 1 and outcome = 'L') as lost_toilet_wk1,
        bool_or(is_toilet_game and postseason_week_num = 2 and outcome = 'L') as lost_toilet_wk2,
        bool_or(is_toilet_game and postseason_week_num = 2 and outcome = 'W') as won_toilet_wk2
    from {{ ref("int__postseason_team_weeks") }}
    group by team_year_id
),

team_postseason as (
    select
        teams.team_id,
        teams.team_year_id,
        teams.year,
        teams.standing as seed,
        team_brackets.bracket,
        teams.final_standing,
        team_brackets.bracket = 'winners' as made_playoffs,
        coalesce(placements.is_champion, false) as is_champion,
        coalesce(placements.is_runner_up, false) as is_runner_up,
        coalesce(placements.is_third, false) as is_third,
        coalesce(placements.lost_toilet_wk1 and placements.won_toilet_wk2, false) as is_second_to_last,
        coalesce(placements.lost_toilet_wk1 and placements.lost_toilet_wk2, false) as is_last
    from {{ ref("base_s001__teams") }} as teams
    inner join team_brackets
        on teams.team_year_id = team_brackets.team_year_id
    left join placements
        on teams.team_year_id = placements.team_year_id
)

select
    team_id,
    team_year_id,
    year,
    seed,
    bracket,
    made_playoffs,
    is_champion,
    is_runner_up,
    is_third,
    is_second_to_last,
    is_last,
    case
        when is_champion then 1
        when is_runner_up then 2
        when is_third then 3
        when is_second_to_last then 11
        when is_last then 12
    end as reconstructed_place,
    final_standing
from team_postseason
