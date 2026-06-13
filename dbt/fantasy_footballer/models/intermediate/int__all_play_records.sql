with reg_team_weeks as (
    select
        team_week_id,
        team_year_id,
        year,
        week,
        score_for,
        outcome
    from {{ ref("int__team_week_results") }}
    where not is_playoff and outcome != 'U'
),

-- Score every team against the whole league that week: an all-play record is what your
-- W-L would have been if you'd played every other team, not just your scheduled opponent.
all_play as (
    select
        team_weeks.team_week_id,
        team_weeks.team_year_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.score_for,
        team_weeks.outcome,
        count(*) filter (where opponent_weeks.score_for < team_weeks.score_for)::int as all_play_wins,
        count(*) filter (where opponent_weeks.score_for > team_weeks.score_for)::int as all_play_losses,
        count(*) filter (where opponent_weeks.score_for = team_weeks.score_for)::int as all_play_ties
    from reg_team_weeks as team_weeks
    inner join reg_team_weeks as opponent_weeks
        on
            team_weeks.year = opponent_weeks.year and
            team_weeks.week = opponent_weeks.week and
            team_weeks.team_week_id != opponent_weeks.team_week_id
    group by all
),

-- all_play_win_pct is the single continuous luck primitive: the share of the league you outscored
-- that week. The discrete lucky-win / unlucky-loss chips are just a threshold on it (you won a week
-- you'd have lost to most of the league, or vice versa) — the same standing, quantized.
scored as (
    select
        *,
        all_play_wins + all_play_losses + all_play_ties as all_play_games,
        (all_play_wins + 0.5 * all_play_ties)
        / nullif(all_play_wins + all_play_losses + all_play_ties, 0) as all_play_win_pct
    from all_play
)

select
    team_week_id,
    team_year_id,
    year,
    week,
    score_for,
    outcome,
    all_play_wins,
    all_play_losses,
    all_play_ties,
    all_play_games,
    all_play_win_pct,
    outcome = 'W' and all_play_win_pct < 0.5 as is_lucky_win,
    outcome = 'L' and all_play_win_pct > 0.5 as is_unlucky_loss
from scored
