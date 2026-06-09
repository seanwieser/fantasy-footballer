with results as (
    select
        twr.team_week_id,
        twr.team_year_id,
        twr.owner_id,
        twr.year,
        twr.week,
        twr.outcome,
        twr.score_for,
        twr.margin,
        twr.is_clutch,
        twr.is_shotgun,
        coalesce(luck.is_lucky_win, false) as is_lucky_win,
        coalesce(luck.is_unlucky_loss, false) as is_unlucky_loss
    from {{ ref("int__team_week_results") }} as twr
    left join {{ ref("int__lucky_records") }} as luck
        on twr.team_week_id = luck.team_week_id
    where not twr.is_playoff
),

-- League-wide season extremes, all keyed off the winner so every flag lines up 1:1 with a season
-- highlight: single highest/lowest score (Best-/Worst-week title) and smallest/largest margin of
-- victory (Tightest game / Biggest blowout). Computed over played weeks only so an unplayed future
-- week (score 0) never registers. Co-title ties flag every holder.
league_extremes as (
    select
        year,
        max(score_for) filter (where outcome != 'U') as league_best_score,
        min(score_for) filter (where outcome != 'U') as league_worst_score,
        min(margin) filter (where outcome = 'W') as tightest_margin,
        max(margin) filter (where outcome = 'W') as biggest_margin
    from results
    group by year
)

select
    results.team_week_id,
    results.team_year_id,
    results.owner_id,
    results.year,
    results.week,
    results.is_shotgun,
    results.is_lucky_win,
    results.is_unlucky_loss,
    results.is_clutch and results.outcome = 'W' as is_clutch_win,
    results.is_clutch and results.outcome = 'L' as is_clutch_loss,
    results.outcome != 'U' and results.score_for = league_extremes.league_best_score as is_best_week,
    results.outcome != 'U' and results.score_for = league_extremes.league_worst_score as is_worst_week,
    results.outcome = 'W' and results.margin = league_extremes.tightest_margin as is_tightest_game,
    results.outcome = 'W' and results.margin = league_extremes.biggest_margin as is_biggest_blowout
from results
inner join league_extremes on results.year = league_extremes.year
