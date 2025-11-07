with matchup_players_unnested as (
    select
        year,
        matchup_week,
        is_playoff,
        matchup_type,
        unnest(matchup_lineup) as player_id
    from {{ ref("base_s001__matchups") }}
    where score_for > 0 -- Future matchup weeks are not valuable
)

select *
from matchup_players_unnested
