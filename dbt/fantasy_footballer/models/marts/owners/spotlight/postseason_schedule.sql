with postseason_games as (
    select * from {{ ref("int__postseason_team_weeks") }}
),

with_opponent_score as (
    select
        games.team_year_id,
        games.team_week_id,
        games.opponent_team_year_id,
        games.year,
        games.week,
        games.postseason_week_num,
        games.score_for,
        opponents.score_for as score_against,
        games.outcome,
        games.is_championship_game,
        games.is_third_place_game,
        games.is_toilet_game
    from postseason_games as games
    left join postseason_games as opponents
        on
            games.opponent_team_year_id = opponents.team_year_id and
            games.year = opponents.year and
            games.postseason_week_num = opponents.postseason_week_num
    where games.is_meaningful
)

select
    owner_map.owner_id,
    owner_map.owner_name,
    with_opponent_score.team_week_id,
    with_opponent_score.year,
    with_opponent_score.week,
    with_opponent_score.postseason_week_num as round_num,
    case
        when with_opponent_score.is_championship_game then 'Championship'
        when with_opponent_score.is_third_place_game then '3rd Place Game'
        -- The Toilet Bowl spans multiple rounds, so carry the round number to disambiguate.
        when with_opponent_score.is_toilet_game then 'TB Round ' || with_opponent_score.postseason_week_num::varchar
        else 'Round ' || with_opponent_score.postseason_week_num::varchar
    end as round_label,
    opponent_map.owner_name as opponent_owner_name,
    opponent_map.team_name as opponent_team_name,
    with_opponent_score.outcome,
    round(with_opponent_score.score_for, 2) as score_for,
    round(with_opponent_score.score_against, 2) as score_against
from with_opponent_score
inner join {{ ref("int__owner_team_year_map") }} as owner_map
    on with_opponent_score.team_year_id = owner_map.team_year_id
left join {{ ref("int__owner_team_year_map") }} as opponent_map
    on with_opponent_score.opponent_team_year_id = opponent_map.team_year_id
order by
    with_opponent_score.year,
    with_opponent_score.postseason_week_num
