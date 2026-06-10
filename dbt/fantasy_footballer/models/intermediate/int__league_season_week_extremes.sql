with results as (
    select
        year,
        outcome,
        score_for,
        margin
    from {{ ref("int__team_week_results") }}
    where not is_playoff
)

select
    year,
    max(score_for) filter (where outcome != 'U') as league_best_score,
    min(score_for) filter (where outcome != 'U') as league_worst_score,
    min(margin) filter (where outcome = 'W') as tightest_margin,
    max(margin) filter (where outcome = 'W') as biggest_margin
from results
group by year
