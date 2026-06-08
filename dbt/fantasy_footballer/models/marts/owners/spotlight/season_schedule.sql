-- Thin mart: weekly schedule display columns joined to the precomputed week-grain highlight flags
-- (all the "what happened this week" logic lives in int__team_week_highlights).
select
    twr.owner_id,
    twr.year,
    twr.week,
    twr.opponent_team_name,
    twr.opponent_owner_name,
    case when twr.outcome = 'U' then '' else twr.outcome end as outcome,
    twr.score_for,
    twr.score_against,
    highlights.is_clutch_win,
    highlights.is_clutch_loss,
    highlights.is_shotgun,
    highlights.is_lucky_win,
    highlights.is_unlucky_loss,
    highlights.is_best_week,
    highlights.is_worst_week,
    highlights.is_tightest_game,
    highlights.is_biggest_blowout
from {{ ref("int__team_week_results") }} as twr
inner join {{ ref("int__team_week_highlights") }} as highlights
    on twr.team_week_id = highlights.team_week_id
where not twr.is_playoff
