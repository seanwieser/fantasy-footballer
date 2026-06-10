-- The derived margin / combined columns must stay defined as winner_score ∓ loser_score. A cheap guard
-- so a future edit can't silently break the FF-013 `combined` column (or `margin`) that the shootout /
-- slugfest and blowout records ride on. Scores are doubles, so compared at a 0.01 tolerance.
select
    team_week_id,
    winner_score,
    loser_score,
    margin,
    combined
from {{ ref("int__matchup_margins") }}
where
    abs(margin - (winner_score - loser_score)) > 0.01 or
    abs(combined - (winner_score + loser_score)) > 0.01
