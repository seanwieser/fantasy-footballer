with results as (
    select
        twr.owner_id,
        twr.owner_name,
        twr.opponent_owner_id,
        twr.opponent_owner_name,
        twr.outcome,
        twr.score_for,
        twr.score_against,
        twr.year,
        twr.week,
        coalesce(twr.is_playoff, false) as is_playoff,
        -- A true playoff meeting = both owners in the championship (winners) bracket. Toilet-bowl and
        -- consolation meetings are NOT counted as playoff meetings (kept separate, like the records).
        coalesce(ptw.is_meaningful and ptw.bracket = 'winners', false) as is_championship_meeting,
        coalesce(ptw.is_meaningful and ptw.bracket = 'toilet_bowl', false) as is_toilet_meeting,
        twr.year * 100 + twr.week as sort_key,
        twr.score_for - twr.score_against as margin_signed,
        twr.score_for + twr.score_against as combined,
        coalesce(luck.is_lucky_win, false) as is_lucky_win,
        coalesce(luck.is_unlucky_loss, false) as is_unlucky_loss,
        round(twr.score_for, 1)::varchar || '-' || round(twr.score_against, 1)::varchar ||
        case when twr.score_for - twr.score_against >= 0 then ' (+' else ' (' end ||
        round(twr.score_for - twr.score_against, 1)::varchar || ') (' ||
        twr.year::varchar || ' W' || twr.week::varchar || ')' as game_label
    from {{ ref("int__team_week_results") }} as twr
    left join {{ ref("int__all_play_records") }} as luck
        on twr.team_week_id = luck.team_week_id
    left join {{ ref("int__postseason_team_weeks") }} as ptw
        on twr.team_week_id = ptw.team_week_id
    where
        twr.outcome in ('W', 'L', 'T') and
        twr.opponent_owner_id is not null
),

-- Regular-season meetings only. Every rivalry comparison metric (record, points, margins, streaks,
-- clutch, shootout/slugfest) is computed from these, so regular-season and playoff stay COMPLETELY
-- separate — playoff meetings surface ONLY through the playoff_record W-L line below. This keeps the
-- 2-week-aggregate playoff scores (a different scale) from distorting the rivalry numbers and matches
-- the regular-season-only league-wide records.
reg_results as (
    select * from results
    where not is_playoff
),

-- Championship-bracket meetings → just the head-to-head W-L record (the only playoff-aware output).
-- Toilet-bowl / consolation meetings are excluded, so this is a true playoff rivalry record.
playoff_record as (
    select
        owner_id,
        opponent_owner_id,
        count_if(outcome = 'W')::int as playoff_wins,
        count_if(outcome = 'L')::int as playoff_losses,
        count_if(outcome = 'T')::int as playoff_ties,
        count(*)::int as playoff_games
    from results
    where is_championship_meeting
    group by owner_id, opponent_owner_id
),

-- Toilet-bowl meetings → their own head-to-head W-L record, kept separate from the playoff record.
toilet_record as (
    select
        owner_id,
        opponent_owner_id,
        count_if(outcome = 'W')::int as toilet_wins,
        count_if(outcome = 'L')::int as toilet_losses,
        count_if(outcome = 'T')::int as toilet_ties,
        count(*)::int as toilet_games
    from results
    where is_toilet_meeting
    group by owner_id, opponent_owner_id
),

-- Gaps-and-islands key over regular-season meetings: consecutive same-outcome meetings share a
-- streak_grp, so the streaks below are regular-season only.
islands as (
    select
        *,
        row_number() over (partition by owner_id, opponent_owner_id order by sort_key) -
        row_number() over (partition by owner_id, opponent_owner_id, outcome order by sort_key) as streak_grp
    from reg_results
),

pair_aggregates as (
    select
        owner_id::varchar || '_' || opponent_owner_id::varchar as owner_opponent_id,
        owner_id,
        max(owner_name) as owner_name,
        opponent_owner_id,
        max(opponent_owner_name) as opponent_owner_name,
        count_if(outcome = 'W')::int as reg_wins,
        count_if(outcome = 'L')::int as reg_losses,
        count_if(outcome = 'T')::int as reg_ties,
        count(*)::int as reg_games,
        sum(score_for)::double as reg_points_for,
        sum(score_against)::double as reg_points_against,
        avg(score_for)::double as avg_points_for,
        avg(margin_signed)::double as avg_margin,
        count_if(abs(margin_signed) < 10 and outcome = 'W')::int as clutch_wins,
        count_if(abs(margin_signed) < 10 and outcome = 'L')::int as clutch_losses,
        count_if(score_against < 100)::int as held_under_100,
        count_if(is_lucky_win)::int as lucky_wins,
        count_if(is_unlucky_loss)::int as unlucky_losses,
        max(margin_signed)::double as biggest_win_margin,
        arg_max(
            round(score_for, 1)::varchar || '-' || round(score_against, 1)::varchar ||
            ' (+' || round(margin_signed, 1)::varchar || ') (' ||
            year::varchar || ' W' || week::varchar || ')',
            margin_signed
        ) as biggest_win_context,
        min(abs(margin_signed))::double as closest_margin,
        arg_min(
            round(score_for, 1)::varchar || '-' || round(score_against, 1)::varchar ||
            case when margin_signed >= 0 then ' (+' else ' (' end ||
            round(margin_signed, 1)::varchar || ') (' ||
            year::varchar || ' W' || week::varchar || ')',
            abs(margin_signed)
        ) as closest_context,
        arg_min(
            case when score_for > score_against then owner_id when score_against > score_for then opponent_owner_id end,
            abs(margin_signed)
        ) as closest_leader,
        max(combined)::double as shootout_combined,
        arg_max(
            round(combined, 0)::bigint::varchar || ' (' ||
            round(score_for, 1)::varchar || '-' || round(score_against, 1)::varchar || ') (' ||
            year::varchar || ' W' || week::varchar || ')',
            combined
        ) as shootout_context,
        arg_max(
            case when score_for > score_against then owner_id when score_against > score_for then opponent_owner_id end,
            combined
        ) as shootout_leader,
        min(combined)::double as slugfest_combined,
        arg_min(
            round(combined, 0)::bigint::varchar || ' (' ||
            round(score_for, 1)::varchar || '-' || round(score_against, 1)::varchar || ') (' ||
            year::varchar || ' W' || week::varchar || ')',
            combined
        ) as slugfest_context,
        arg_min(
            case when score_for > score_against then owner_id when score_against > score_for then opponent_owner_id end,
            combined
        ) as slugfest_leader,
        arg_max(outcome, sort_key) as current_outcome,
        arg_max(game_label, sort_key) as last_meeting_context,
        arg_max(streak_grp, sort_key) as final_grp
    from islands
    group by owner_id, opponent_owner_id
),

streak_runs as (
    select
        owner_id,
        opponent_owner_id,
        outcome,
        streak_grp,
        count(*)::int as run_length
    from islands
    group by owner_id, opponent_owner_id, outcome, streak_grp
),

longest_win as (
    select
        owner_id,
        opponent_owner_id,
        max(run_length)::int as longest_win_streak
    from streak_runs
    where outcome = 'W'
    group by owner_id, opponent_owner_id
),

-- Current streak = size of the most-recent island (the one holding the latest meeting).
current_run as (
    select
        islands.owner_id,
        islands.opponent_owner_id,
        count(*)::int as current_streak
    from islands
    inner join pair_aggregates
        on
            islands.owner_id = pair_aggregates.owner_id and
            islands.opponent_owner_id = pair_aggregates.opponent_owner_id and
            islands.streak_grp = pair_aggregates.final_grp
    group by islands.owner_id, islands.opponent_owner_id
)

select
    pair_aggregates.owner_opponent_id,
    pair_aggregates.owner_id,
    pair_aggregates.owner_name,
    pair_aggregates.opponent_owner_id,
    pair_aggregates.opponent_owner_name,
    pair_aggregates.reg_wins,
    pair_aggregates.reg_losses,
    pair_aggregates.reg_ties,
    pair_aggregates.reg_games,
    pair_aggregates.reg_points_for,
    pair_aggregates.reg_points_against,
    coalesce(playoff_record.playoff_wins, 0)::int as playoff_wins,
    coalesce(playoff_record.playoff_losses, 0)::int as playoff_losses,
    coalesce(playoff_record.playoff_ties, 0)::int as playoff_ties,
    coalesce(playoff_record.playoff_games, 0)::int as playoff_games,
    coalesce(toilet_record.toilet_wins, 0)::int as toilet_wins,
    coalesce(toilet_record.toilet_losses, 0)::int as toilet_losses,
    coalesce(toilet_record.toilet_ties, 0)::int as toilet_ties,
    coalesce(toilet_record.toilet_games, 0)::int as toilet_games,
    pair_aggregates.avg_points_for,
    pair_aggregates.avg_margin,
    pair_aggregates.clutch_wins,
    pair_aggregates.clutch_losses,
    pair_aggregates.held_under_100,
    pair_aggregates.lucky_wins,
    pair_aggregates.unlucky_losses,
    pair_aggregates.biggest_win_margin,
    pair_aggregates.biggest_win_context,
    pair_aggregates.closest_margin,
    pair_aggregates.closest_context,
    pair_aggregates.closest_leader,
    pair_aggregates.shootout_combined,
    pair_aggregates.shootout_context,
    pair_aggregates.shootout_leader,
    pair_aggregates.slugfest_combined,
    pair_aggregates.slugfest_context,
    pair_aggregates.slugfest_leader,
    pair_aggregates.current_outcome,
    pair_aggregates.last_meeting_context,
    current_run.current_streak,
    coalesce(longest_win.longest_win_streak, 0)::int as longest_win_streak
from pair_aggregates
inner join current_run
    on
        pair_aggregates.owner_id = current_run.owner_id and
        pair_aggregates.opponent_owner_id = current_run.opponent_owner_id
left join longest_win
    on
        pair_aggregates.owner_id = longest_win.owner_id and
        pair_aggregates.opponent_owner_id = longest_win.opponent_owner_id
left join playoff_record
    on
        pair_aggregates.owner_id = playoff_record.owner_id and
        pair_aggregates.opponent_owner_id = playoff_record.opponent_owner_id
left join toilet_record
    on
        pair_aggregates.owner_id = toilet_record.owner_id and
        pair_aggregates.opponent_owner_id = toilet_record.opponent_owner_id
