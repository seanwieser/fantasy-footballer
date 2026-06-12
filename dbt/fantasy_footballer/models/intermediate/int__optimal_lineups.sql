-- Team-week totals: points the owner actually started vs the best legal lineup they could have set
-- that week. Thin aggregation of the per-player flags in int__optimal_lineup_players;
-- `greatest(optimal, actual)` guards rare eligibility edge cases so optimal is never below actual.
select
    team_year_id,
    team_week_id,
    year,
    week,
    coalesce(sum(points) filter (where is_started), 0) as actual_points,
    greatest(
        coalesce(sum(points) filter (where is_optimal), 0),
        coalesce(sum(points) filter (where is_started), 0)
    ) as optimal_points
from {{ ref("int__optimal_lineup_players") }}
-- Regular season only: this league's playoff games run on a different scoring scale, so they never
-- enter any season comparison metric (see CLAUDE.md). Postseason surfaces only in the spotlight view.
where not is_playoff
group by all
