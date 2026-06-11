-- One row per owner-season-player who left points on the bench: the regular-season points the player
-- scored in weeks they belonged in the owner's optimal lineup but were benched (is_optimal and not
-- is_started). This is the player-level decomposition of start/sit loss — it credits a benched player
-- only for weeks starting them would have helped, so a genuinely good option sat repeatedly rises to
-- the top while a correctly-benched backup never appears. Powers the underutilized-player highlight.
with player_season as (
    select
        owner_map.owner_id,
        owner_map.owner_name,
        owner_map.owner_year_id,
        lineup.team_year_id,
        owner_map.year,
        lineup.player_id,
        max(lineup.player_name) as player_name,
        max(lineup.position) as position,
        count_if(lineup.is_optimal and not lineup.is_started)::int as weeks_benched_deserving,
        sum(lineup.points) filter (where lineup.is_optimal and not lineup.is_started) as points_left_on_bench
    from {{ ref("int__optimal_lineup_players") }} as lineup
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on lineup.team_year_id = owner_map.team_year_id
    where not lineup.is_playoff
    group by all
)

select
    owner_id,
    owner_name,
    owner_year_id,
    owner_year_id || '_' || player_id::varchar as owner_player_year_id,
    team_year_id,
    year,
    player_id::varchar || '_' || year::varchar as player_year_id,
    player_name,
    position,
    weeks_benched_deserving,
    round(points_left_on_bench, 2) as points_left_on_bench
from player_season
where points_left_on_bench > 0
