-- FF-011 invariant: a team's Best-/Worst-week season title (int__season_titles) must line up 1:1 with
-- whether any of its weeks carries the is_best_week / is_worst_week spotlight chip
-- (int__team_week_highlights). Both now derive from int__league_season_week_extremes, so this should
-- always hold — the test fails loudly if a future change makes them drift. Returns the offending rows.
with titles as (
    select
        team_year_id,
        is_matchup_title,
        is_bad_matchup_title
    from {{ ref("int__season_titles") }}
),

chips as (
    select
        team_year_id,
        bool_or(is_best_week) as has_best_week,
        bool_or(is_worst_week) as has_worst_week
    from {{ ref("int__team_week_highlights") }}
    group by team_year_id
)

select
    titles.team_year_id,
    titles.is_matchup_title,
    titles.is_bad_matchup_title,
    chips.has_best_week,
    chips.has_worst_week
from titles
left join chips on titles.team_year_id = chips.team_year_id
where
    titles.is_matchup_title != coalesce(chips.has_best_week, false) or
    titles.is_bad_matchup_title != coalesce(chips.has_worst_week, false)
