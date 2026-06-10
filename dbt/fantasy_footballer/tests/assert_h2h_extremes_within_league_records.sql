-- A rivalry's single-game extremes are, by definition, a subset of all regular-season games, so they
-- must fall within the league-wide regular-season extremes computed in int__matchup_margins. If an
-- int__owner_head_to_head extreme exceeds the league record, an out-of-universe game has leaked in —
-- e.g. a playoff meeting (2-week-aggregate score on a different scale) being mixed into the rivalry
-- numbers, the exact bug this guards against.
-- Ties are included in the league bounds (int__matchup_margins keeps them) so a tie game in the H2H
-- side can't trip a false positive.
with league as (
    select
        max(combined) as max_combined,
        min(combined) as min_combined,
        max(margin) as max_margin
    from {{ ref("int__matchup_margins") }}
),

h2h as (
    select
        owner_opponent_id,
        shootout_combined,
        slugfest_combined,
        biggest_win_margin
    from {{ ref("int__owner_head_to_head") }}
)

select h2h.*
from h2h
cross join league
where
    h2h.shootout_combined > league.max_combined or
    h2h.slugfest_combined < league.min_combined or
    h2h.biggest_win_margin > league.max_margin
