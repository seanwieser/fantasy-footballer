-- Per-owner career trophy case for the Postseason History page. Thin display wrap of the
-- int__owner_postseason_summary roll-up, ordered so the most-decorated owners surface first.
-- `last_year` (the owner's most recent season) lets each card link to their owner-spotlight.
with tenure as (
    select
        owner_id,
        max(year) as last_year
    from {{ ref("int__owner_team_year_map") }}
    group by owner_id
)

select
    summary.owner_id,
    summary.owner_name,
    summary.playoff_appearances,
    summary.championships,
    summary.runner_ups,
    summary.third_places,
    summary.toilet_bowl_appearances,
    summary.last_place_finishes,
    summary.second_to_last_finishes,
    summary.best_finish,
    summary.playoff_wins,
    summary.playoff_losses,
    summary.toilet_bowl_wins,
    summary.toilet_bowl_losses,
    tenure.last_year::int as last_year
from {{ ref("int__owner_postseason_summary") }} as summary
inner join tenure
    on summary.owner_id = tenure.owner_id
order by
    summary.championships desc, summary.runner_ups desc, summary.third_places desc,
    summary.playoff_appearances desc
