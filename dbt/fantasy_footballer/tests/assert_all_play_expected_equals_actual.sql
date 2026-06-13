-- All-play is zero-sum within a season: every weekly pairwise comparison hands one team a win and the
-- other a loss, so the league's total expected wins must equal its total actual wins each season, and
-- total schedule luck must net to zero. A nonzero diff means int__all_play_records double-counted or
-- dropped a pairwise comparison (the same self-join bug class as assert_league_reg_season_zero_sum).
-- Expected wins are summed doubles, so compared at a 0.1 tolerance.
with by_year as (
    select
        year,
        sum(expected_wins) as expected_wins,
        sum(actual_wins) as actual_wins,
        sum(schedule_luck) as schedule_luck
    from {{ ref("int__owner_season_all_play") }}
    group by year
)

select
    year,
    expected_wins,
    actual_wins,
    schedule_luck
from by_year
where
    abs(expected_wins - actual_wins) > 0.1 or
    abs(schedule_luck) > 0.1
