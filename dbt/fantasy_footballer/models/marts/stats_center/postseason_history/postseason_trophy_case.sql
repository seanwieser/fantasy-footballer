-- Per-owner career trophy case for the Postseason History page. Thin display wrap of the
-- int__owner_postseason_summary roll-up, ordered so the most-decorated owners surface first.
select
    owner_id,
    owner_name,
    playoff_appearances,
    championships,
    runner_ups,
    third_places,
    toilet_bowl_appearances,
    last_place_finishes,
    second_to_last_finishes,
    best_finish,
    playoff_wins,
    playoff_losses,
    toilet_bowl_wins,
    toilet_bowl_losses
from {{ ref("int__owner_postseason_summary") }}
order by championships desc, runner_ups desc, third_places desc, playoff_appearances desc
