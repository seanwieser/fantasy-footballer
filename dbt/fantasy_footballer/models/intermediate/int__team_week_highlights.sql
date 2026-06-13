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
    left join {{ ref("int__all_play_records") }} as luck
        on twr.team_week_id = luck.team_week_id
    where not twr.is_playoff
),

-- League-wide season extremes (single source of truth: int__league_season_week_extremes): single
-- highest/lowest score (Best-/Worst-week title) and smallest/largest margin of victory (Tightest
-- game / Biggest blowout). Sharing the model with int__season_titles keeps each chip flag below
-- aligned 1:1 with its matching season title.
league_extremes as (
    select * from {{ ref("int__league_season_week_extremes") }}
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
