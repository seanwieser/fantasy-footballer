-- Metric metadata (key -> section/label/format/sort/order/tooltip) lives in the h2h_metrics seed.
with metric_meta as (
    select * from {{ ref("h2h_metrics") }}
),

career as (
    select * from {{ ref("int__owner_career_summary") }}
),

postseason as (
    select * from {{ ref("int__owner_postseason_summary") }}
),

owner_map as (
    select * from {{ ref("int__owner_team_year_map") }}
),

-- Career W-L-T = the owner's head-to-head record summed across every opponent (regular season).
record as (
    select
        owner_id,
        max(owner_name) as owner_name,
        sum(reg_wins)::int as wins,
        sum(reg_losses)::int as losses,
        sum(reg_ties)::int as ties,
        (sum(reg_wins) + sum(reg_losses) + sum(reg_ties))::int as games
    from {{ ref("int__owner_head_to_head") }}
    group by owner_id
),

record_pct as (
    select
        *,
        (wins + 0.5 * ties) / nullif(games, 0) * 100 as win_pct
    from record
),

-- Career points-for/against and single-season / single-week extremes.
season_scoring as (
    select
        owner_id,
        max(owner_name) as owner_name,
        sum(reg_points_total) as points_for,
        sum(reg_points_against) as points_against,
        max(reg_points_total) as highest_season,
        arg_max(year, reg_points_total) as highest_season_year
    from {{ ref("int__owner_season_scoring") }}
    group by owner_id
),

-- Owner's single best/worst regular-season week + the when-context (same filter as season scoring).
week_extremes as (
    select
        owner_id,
        max(owner_name) as owner_name,
        max(score_for) as best_week,
        min(score_for) as worst_week,
        arg_max(year::varchar || ' W' || week::varchar, score_for) as best_week_when,
        arg_min(year::varchar || ' W' || week::varchar, score_for) as worst_week_when
    from {{ ref("int__team_week_results") }}
    where not is_playoff and outcome != 'U'
    group by owner_id
),

-- Largest regular-season margin of victory the owner has handed out + that game's matchup score.
blowout as (
    select
        owner_map.owner_id,
        max(owner_map.owner_name) as owner_name,
        max(margins.margin) as max_margin,
        arg_max(
            round(margins.winner_score, 2)::varchar || '-' || round(margins.loser_score, 2)::varchar,
            margins.margin
        ) as max_margin_score
    from {{ ref("int__matchup_margins") }} as margins
    inner join owner_map on margins.winner_team_year_id = owner_map.team_year_id
    where not margins.is_tie
    group by owner_map.owner_id
),

-- One candidate row per owner per metric: metric_value drives the leader highlight + sort,
-- override_display carries a prebuilt string for non-numeric metrics (records, best finish).
candidates as (
    select
        owner_id,
        owner_name,
        'career_record' as metric_key,
        win_pct as metric_value,
        wins::varchar || '-' || losses::varchar ||
        case when ties > 0 then '-' || ties::varchar else '' end as override_display
    from record_pct
    union all
    select
        owner_id,
        owner_name,
        'career_win_pct' as metric_key,
        win_pct as metric_value,
        null::varchar as override_display
    from record_pct
    union all
    select
        owner_id,
        owner_name,
        'seasons_played' as metric_key,
        seasons_played::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'career_points' as metric_key,
        points_total as metric_value,
        round(points_total, 0)::bigint::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'career_ppg' as metric_key,
        points_per_game as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'scoring_titles' as metric_key,
        scoring_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'bottom_scorer_titles' as metric_key,
        non_scoring_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'best_week_titles' as metric_key,
        matchup_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'worst_week_titles' as metric_key,
        bad_matchup_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'snub_total' as metric_key,
        snub_total::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'snub_titles' as metric_key,
        non_playoff_scoring_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'luck_in_total' as metric_key,
        luck_in_total::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'lucky_in_titles' as metric_key,
        playoff_non_scoring_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'lucky_wins_total' as metric_key,
        lucky_wins_total as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'unlucky_losses_total' as metric_key,
        unlucky_losses_total as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'lucky_winner_titles' as metric_key,
        lucky_winner_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'unlucky_loser_titles' as metric_key,
        unlucky_loser_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'shotgun_total' as metric_key,
        shotgun_total as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'shotgun_titles' as metric_key,
        shotgun_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'sober_seasons' as metric_key,
        no_shotgun_season_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'clutch_win_pct' as metric_key,
        clutch_win_pct as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'clutch_record' as metric_key,
        clutch_win_pct as metric_value,
        clutch_wins_total::int::varchar || '-' || clutch_losses_total::int::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'clutch_winning_titles' as metric_key,
        clutch_winning_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'clutch_losing_titles' as metric_key,
        clutch_losing_title_count::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'career_points_against' as metric_key,
        points_against as metric_value,
        round(points_against, 0)::bigint::varchar as override_display
    from season_scoring
    union all
    select
        owner_id,
        owner_name,
        'career_point_differential' as metric_key,
        points_for - points_against as metric_value,
        round(points_for - points_against, 0)::bigint::varchar as override_display
    from season_scoring
    union all
    select
        owner_id,
        owner_name,
        'highest_scoring_season' as metric_key,
        highest_season as metric_value,
        round(highest_season, 2)::varchar || ' (' || highest_season_year::varchar || ')' as override_display
    from season_scoring
    union all
    select
        owner_id,
        owner_name,
        'best_week_ever' as metric_key,
        best_week as metric_value,
        round(best_week, 2)::varchar || ' (' || best_week_when || ')' as override_display
    from week_extremes
    union all
    select
        owner_id,
        owner_name,
        'worst_week_ever' as metric_key,
        worst_week as metric_value,
        round(worst_week, 2)::varchar || ' (' || worst_week_when || ')' as override_display
    from week_extremes
    union all
    select
        owner_id,
        owner_name,
        'biggest_blowout' as metric_key,
        max_margin as metric_value,
        round(max_margin, 2)::varchar || ' (' || max_margin_score || ')' as override_display
    from blowout
    union all
    select
        owner_id,
        owner_name,
        'championships' as metric_key,
        championships::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'runner_ups' as metric_key,
        runner_ups::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'title_game_appearances' as metric_key,
        (championships + runner_ups)::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'third_place_finishes' as metric_key,
        third_places::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'playoff_appearances' as metric_key,
        playoff_appearances::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'playoff_game_record' as metric_key,
        playoff_wins::double / nullif(playoff_wins + playoff_losses, 0) * 100 as metric_value,
        playoff_wins::varchar || '-' || playoff_losses::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'toilet_bowl_appearances' as metric_key,
        toilet_bowl_appearances::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'toilet_bowl_record' as metric_key,
        toilet_bowl_wins::double / nullif(toilet_bowl_wins + toilet_bowl_losses, 0) * 100 as metric_value,
        toilet_bowl_wins::varchar || '-' || toilet_bowl_losses::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'second_to_last_finishes' as metric_key,
        second_to_last_finishes::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'last_place_finishes' as metric_key,
        last_place_finishes::double as metric_value,
        null::varchar as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'best_finish' as metric_key,
        best_finish::double as metric_value,
        best_finish::varchar || case
            when best_finish % 100 in (11, 12, 13) then 'th'
            when best_finish % 10 = 1 then 'st'
            when best_finish % 10 = 2 then 'nd'
            when best_finish % 10 = 3 then 'rd'
            else 'th'
        end as override_display
    from postseason
    union all
    select
        owner_id,
        owner_name,
        'career_acquisitions' as metric_key,
        acquisitions_total::double as metric_value,
        null::varchar as override_display
    from career
    union all
    select
        owner_id,
        owner_name,
        'career_trades' as metric_key,
        trades_total::double as metric_value,
        null::varchar as override_display
    from career
),

joined as (
    select
        meta.section,
        candidates.metric_key,
        meta.metric_label,
        meta.value_format,
        meta.sort_sign,
        meta.description,
        meta.display_order,
        meta.tier,
        candidates.owner_id,
        candidates.owner_name,
        candidates.metric_value,
        candidates.override_display
    from candidates
    inner join metric_meta as meta on candidates.metric_key = meta.metric_key
)

select
    section,
    metric_key,
    metric_label,
    value_format,
    sort_sign::int as sort_sign,
    description,
    display_order::int as display_order,
    tier,
    owner_id,
    owner_name,
    metric_value::double as metric_value,
    coalesce(
        override_display,
        {{ format_metric_value("metric_value", "value_format") }}
    ) as display_value
from joined
order by display_order, metric_value * sort_sign desc
