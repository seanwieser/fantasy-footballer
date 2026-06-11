-- Metric metadata (key -> section/category/label/type/sort/format/tooltip) lives in a seed.
with metric_meta as (
    select * from {{ ref("all_time_record_metrics") }}
),

-- Chronological list of years each owner held a season title, keyed to its `_count` metric.
-- Powers the "years won" subtitle on season-award cards (subtitle_kind = 'years').
title_years as (
    select
        owner_id,
        metric_key || '_count' as metric_key,
        string_agg(year::varchar, ', ' order by year) as years_won
    from {{ ref("int__season_titles_long") }}
    where is_title_holder
    group by owner_id, metric_key
    union all
    -- Snub / lucky-in occurrences aren't titles, so list their years straight from the wide table.
    select
        owner_id,
        'snub_total_count' as metric_key,
        string_agg(year::varchar, ', ' order by year) as years_won
    from {{ ref("int__season_titles") }}
    where is_snubbed
    group by owner_id
    union all
    select
        owner_id,
        'luck_in_total_count' as metric_key,
        string_agg(year::varchar, ', ' order by year) as years_won
    from {{ ref("int__season_titles") }}
    where is_lucked_in
    group by owner_id
    union all
    -- Championship years for the "Most championships" card's years-won subtitle.
    select
        owner_map.owner_id,
        'most_championships' as metric_key,
        string_agg(postseason.year::varchar, ', ' order by postseason.year) as years_won
    from {{ ref("int__team_postseason") }} as postseason
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on postseason.team_year_id = owner_map.team_year_id
    where postseason.is_champion
    group by owner_map.owner_id
),

-- Career roll-ups (one row per owner) — all aggregation lives in the intermediate
career as (
    select * from {{ ref("int__owner_career_summary") }}
),

-- Career postseason roll-up (championships, playoff appearances, toilet bowls, finishes).
postseason as (
    select * from {{ ref("int__owner_postseason_summary") }}
),

-- Tennis-style title counts (one column per title, unpivoted to tidy rows)
title_count_candidates as (
    unpivot (  --noqa: LT02
        select
            owner_id,
            owner_name,
            scoring_title_count,
            non_scoring_title_count,
            matchup_title_count,
            bad_matchup_title_count,
            non_playoff_scoring_title_count,
            playoff_non_scoring_title_count,
            clutch_winning_title_count,
            clutch_losing_title_count,
            lucky_winner_title_count,
            unlucky_loser_title_count,
            shotgun_title_count,
            no_shotgun_season_count
        from career
    )
    on  --noqa: LT02
        scoring_title_count, non_scoring_title_count, matchup_title_count, bad_matchup_title_count,  --noqa: LT02
        non_playoff_scoring_title_count, playoff_non_scoring_title_count, clutch_winning_title_count,  --noqa: LT02
        clutch_losing_title_count, lucky_winner_title_count, unlucky_loser_title_count,  --noqa: LT02
        shotgun_title_count, no_shotgun_season_count  --noqa: LT02
    into name metric_key value metric_value
),

title_count_shaped as (
    select
        owner_id,
        owner_name,
        metric_key,
        metric_value::double as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from title_count_candidates
),

-- Career cumulative counts
career_count_candidates as (
    select
        career.owner_id,
        career.owner_name,
        'lucky_wins_total_count' as metric_key,
        career.lucky_wins_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    union all
    select
        career.owner_id,
        career.owner_name,
        'unlucky_losses_total_count' as metric_key,
        career.unlucky_losses_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.shotgun_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    cross join (values ('most_shotgun_total_count')) as directions (metric_key)
    union all
    select
        career.owner_id,
        career.owner_name,
        'snub_total_count' as metric_key,
        career.snub_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    union all
    select
        career.owner_id,
        career.owner_name,
        'luck_in_total_count' as metric_key,
        career.luck_in_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
),

-- Career totals (points, PPG, clutch %)
career_total_candidates as (
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.points_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    cross join (values ('most_points_total')) as directions (metric_key)
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.points_per_game as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    cross join (values ('most_points_ppg'), ('least_points_ppg')) as directions (metric_key)
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.clutch_win_pct as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        career.clutch_wins_total::int::varchar || '-' || career.clutch_losses_total::int::varchar || ' record'
            as detail
    from career
    cross join (values ('best_clutch_pct'), ('worst_clutch_pct')) as directions (metric_key)
    where career.clutch_win_pct is not null
    union all
    select
        career.owner_id,
        career.owner_name,
        'least_shotgun_per_season' as metric_key,
        career.shotgun_total / nullif(career.seasons_played, 0) as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
),

-- Single-extreme records sourced at owner-season grain
season_scoring_records as (
    select
        titles.owner_id,
        titles.owner_name,
        directions.metric_key,
        titles.reg_points_total as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    cross join (values ('highest_scoring_season'), ('lowest_scoring_season')) as directions (metric_key)
    union all
    select
        titles.owner_id,
        titles.owner_name,
        directions.metric_key,
        titles.reg_points_per_game as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    cross join (values ('highest_scoring_season_ppg'), ('lowest_scoring_season_ppg')) as directions (metric_key)
),

playoff_scoring_records as (
    select
        titles.owner_id,
        titles.owner_name,
        'best_non_playoff_scoring_amount' as metric_key,
        titles.reg_points_total as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    where not titles.made_playoffs
    union all
    select
        titles.owner_id,
        titles.owner_name,
        'worst_playoff_non_scoring_amount' as metric_key,
        titles.reg_points_total as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    where titles.made_playoffs
),

-- Biggest snub / lucky-in: ranked by how many teams you out/under-scored across the cutoff,
-- tiebroken by points (so the higher scorer wins a tie). Only snubbed/lucked-in seasons qualify.
snub_records as (
    select
        titles.owner_id,
        titles.owner_name,
        'biggest_snub' as metric_key,
        titles.playoff_teams_outscored::double as metric_value,
        -- Higher points-for is the bigger snub when teams-outscored ties.
        titles.reg_points_total as tiebreak,
        titles.year::varchar as season_or_week,
        'playoff teams outscored · ' || round(titles.reg_points_total, 0)::bigint::varchar || ' PF' as detail
    from {{ ref("int__season_titles") }} as titles
    where titles.is_snubbed
    union all
    select
        titles.owner_id,
        titles.owner_name,
        'biggest_luck_in' as metric_key,
        titles.nonplayoff_teams_outscoring::double as metric_value,
        -- Fewer points-for is the luckier sneak-in when teams-outscored-by ties.
        -titles.reg_points_total as tiebreak,
        titles.year::varchar as season_or_week,
        'higher scorers left out · ' || round(titles.reg_points_total, 0)::bigint::varchar || ' PF' as detail
    from {{ ref("int__season_titles") }} as titles
    where titles.is_lucked_in
),

clutch_season_records as (
    select
        titles.owner_id,
        titles.owner_name,
        'clutchest_season' as metric_key,
        titles.clutch_wins::double as metric_value,
        titles.clutch_wins::double / nullif(titles.clutch_wins + titles.clutch_losses, 0) as tiebreak,
        titles.year::varchar as season_or_week,
        titles.clutch_wins::varchar || '-' || titles.clutch_losses::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    where titles.clutch_wins + titles.clutch_losses > 0
    union all
    select
        titles.owner_id,
        titles.owner_name,
        'unclutchest_season' as metric_key,
        titles.clutch_losses::double as metric_value,
        -titles.clutch_wins::double / nullif(titles.clutch_wins + titles.clutch_losses, 0) as tiebreak,
        titles.year::varchar as season_or_week,
        titles.clutch_wins::varchar || '-' || titles.clutch_losses::varchar as detail
    from {{ ref("int__season_titles") }} as titles
    where titles.clutch_wins + titles.clutch_losses > 0
),

shotgun_season_records as (
    select
        titles.owner_id,
        titles.owner_name,
        'highest_shotgun_season_record' as metric_key,
        titles.shotgun_count::double as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__season_titles") }} as titles
),

-- Single-extreme records sourced at week / game grain (regular season)
matchup_week_records as (
    select
        owner_map.owner_id,
        owner_map.owner_name,
        directions.metric_key,
        lucky.score_for as metric_value,
        0::double as tiebreak,
        lucky.year::varchar || ' W' || lucky.week::varchar as season_or_week,
        null::varchar as detail
    from {{ ref("int__lucky_records") }} as lucky
    inner join {{ ref("int__owner_team_year_map") }} as owner_map on lucky.team_year_id = owner_map.team_year_id
    cross join (values ('best_matchup_amount'), ('worst_matchup_amount')) as directions (metric_key)
),

-- Single-extreme game records ranked on one number: the victory margin (tightest game / biggest
-- blowout) or the combined score (shootout / slugfest). The winner/loser join and the composed
-- "def. X, score" detail are identical for all four, so the direction key just picks which number
-- is ranked. (season_highlights.matchup_candidates is the per-season single-winner counterpart.)
matchup_game_records as (
    select
        winner.owner_id,
        winner.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'highest_shootouts' then margins.combined
            when 'lowest_slugfests' then margins.combined
            else margins.margin
        end as metric_value,
        0::double as tiebreak,
        margins.year::varchar || ' W' || margins.week::varchar as season_or_week,
        'def. ' || loser.owner_name || ', ' ||
        round(margins.winner_score, 2)::varchar || '-' || round(margins.loser_score, 2)::varchar as detail
    from {{ ref("int__matchup_margins") }} as margins
    inner join {{ ref("int__owner_team_year_map") }} as winner
        on margins.winner_team_year_id = winner.team_year_id
    inner join {{ ref("int__owner_team_year_map") }} as loser
        on margins.loser_team_year_id = loser.team_year_id
    cross join (
        values
        ('tightest_matchups'), ('biggest_blowouts'), ('highest_shootouts'), ('lowest_slugfests')
    ) as directions (metric_key)
    where not margins.is_tie
),

-- Career roster-move leaders (acquisitions / trades) — owner-grain totals from the career roll-up.
transaction_records as (
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'most_acquisitions_career' then career.acquisitions_total
            else career.trades_total
        end::double as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from career
    cross join (values ('most_acquisitions_career'), ('most_trades_career')) as directions (metric_key)
),

-- Career postseason-result leaders (championships / runner-ups / playoff appearances / toilet bowls).
postseason_records as (
    select
        postseason.owner_id,
        postseason.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'most_championships' then postseason.championships
            when 'most_last_place_finishes' then postseason.last_place_finishes
            when 'most_runner_ups' then postseason.runner_ups
            when 'most_playoff_appearances' then postseason.playoff_appearances
            else postseason.toilet_bowl_appearances
        end::double as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week,
        null::varchar as detail
    from postseason
    cross join (
        values
        ('most_championships'),
        ('most_last_place_finishes'),
        ('most_runner_ups'),
        ('most_playoff_appearances'),
        ('most_toilet_bowls')
    ) as directions (metric_key)
),

-- Career W-L leaderboards, ranked by total wins (tiebreak: win %). The W-L record headlines the card
-- (via the display override below) with win % as the subtitle. Playoff = championship bracket; toilet
-- bowl is kept separate — same split as int__owner_postseason_summary.
postseason_game_records as (
    select
        postseason.owner_id,
        postseason.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'career_playoff_record' then postseason.playoff_wins
            else postseason.toilet_bowl_wins
        end::double as metric_value,
        case directions.metric_key
            when 'career_playoff_record'
                then
                    postseason.playoff_wins::double /
                    nullif(postseason.playoff_wins + postseason.playoff_losses, 0)
            else
                postseason.toilet_bowl_wins::double /
                nullif(postseason.toilet_bowl_wins + postseason.toilet_bowl_losses, 0)
        end as tiebreak,
        case directions.metric_key
            when 'career_playoff_record'
                then round(
                    postseason.playoff_wins::double /
                    nullif(postseason.playoff_wins + postseason.playoff_losses, 0) * 100, 0
                )::bigint::varchar || '%'
            else round(
                postseason.toilet_bowl_wins::double /
                nullif(postseason.toilet_bowl_wins + postseason.toilet_bowl_losses, 0) * 100, 0
            )::bigint::varchar || '%'
        end as season_or_week,
        case directions.metric_key
            when 'career_playoff_record'
                then postseason.playoff_wins::varchar || '-' || postseason.playoff_losses::varchar
            else postseason.toilet_bowl_wins::varchar || '-' || postseason.toilet_bowl_losses::varchar
        end as detail
    from postseason
    cross join (
        values ('career_playoff_record'), ('career_toilet_bowl_record')
    ) as directions (metric_key)
),

candidates as (
    select * from title_count_shaped
    union all
    select * from career_count_candidates
    union all
    select * from career_total_candidates
    union all
    select * from season_scoring_records
    union all
    select * from playoff_scoring_records
    union all
    select * from snub_records
    union all
    select * from clutch_season_records
    union all
    select * from shotgun_season_records
    union all
    select * from matchup_week_records
    union all
    select * from matchup_game_records
    union all
    select * from transaction_records
    union all
    select * from postseason_records
    union all
    select * from postseason_game_records
),

ranked as (
    select
        meta.section,
        meta.category,
        candidates.metric_key,
        meta.metric_label,
        meta.metric_type,
        meta.description,
        meta.subtitle_kind,
        meta.display_order,
        meta.value_format,
        meta.result_n,
        candidates.owner_id,
        candidates.owner_name,
        candidates.metric_value,
        candidates.season_or_week,
        candidates.detail,
        title_years.years_won,
        rank() over (
            partition by candidates.metric_key
            order by candidates.metric_value * meta.sort_sign desc, candidates.tiebreak desc
        ) as metric_rank
    from candidates
    inner join metric_meta as meta on candidates.metric_key = meta.metric_key
    left join title_years
        on
            candidates.owner_id = title_years.owner_id and
            candidates.metric_key = title_years.metric_key
)

select
    section,
    category,
    metric_key,
    metric_label,
    metric_type,
    description,
    subtitle_kind::varchar as subtitle_kind,
    years_won::varchar as years_won,
    display_order::int as display_order,
    owner_id,
    owner_name,
    coalesce(
        -- These metrics headline the W-L record itself, not the raw win/loss count (win % is the subtitle).
        case
            when metric_key in (
                'clutchest_season', 'unclutchest_season', 'career_playoff_record', 'career_toilet_bowl_record'
            ) then detail
        end,
        {{ format_metric_value("metric_value", "value_format") }}
    ) as display_value,
    season_or_week,
    case
        when metric_key in (
            'clutchest_season', 'unclutchest_season', 'career_playoff_record', 'career_toilet_bowl_record'
        ) then null
        else detail
    end as detail,
    metric_rank::int as rank
from ranked
where
    metric_rank <= result_n and
    -- Suppress 0-count rows: a zero means the owner never progressed onto the board at all,
    -- so a sparse count metric never floods its card with empty placeholders.
    (metric_type != 'count' or metric_value > 0)
order by display_order, rank
