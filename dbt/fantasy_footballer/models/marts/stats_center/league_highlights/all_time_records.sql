{% set top_n = 3 %}

with metric_meta (
    metric_key, section, category, metric_label, metric_type, sort_sign, result_n, value_format
) as (
    values
    ('scoring_title_count', 'Scoring', 'Season', 'Scoring titles', 'count', 1, {{ top_n }}, 'int'),
    ('non_scoring_title_count', 'Scoring', 'Season', 'Wooden-spoon titles', 'count', 1, {{ top_n }}, 'int'),
    ('most_points_total', 'Scoring', 'Season', 'Most career points', 'total', 1, {{ top_n }}, 'points'),
    ('least_points_total', 'Scoring', 'Season', 'Fewest career points', 'total', -1, {{ top_n }}, 'points'),
    ('most_points_ppg', 'Scoring', 'Season', 'Highest career PPG', 'total', 1, {{ top_n }}, 'points'),
    ('least_points_ppg', 'Scoring', 'Season', 'Lowest career PPG', 'total', -1, {{ top_n }}, 'points'),
    ('highest_scoring_season', 'Scoring', 'Season', 'Highest-scoring season', 'record', 1, 1, 'points'),
    ('lowest_scoring_season', 'Scoring', 'Season', 'Lowest-scoring season', 'record', -1, 1, 'points'),
    ('highest_scoring_season_ppg', 'Scoring', 'Season', 'Highest-scoring season (PPG)', 'record', 1, 1, 'points'),
    ('lowest_scoring_season_ppg', 'Scoring', 'Season', 'Lowest-scoring season (PPG)', 'record', -1, 1, 'points'),
    ('matchup_title_count', 'Scoring', 'Matchup', 'Best-week titles', 'count', 1, {{ top_n }}, 'int'),
    ('bad_matchup_title_count', 'Scoring', 'Matchup', 'Worst-week titles', 'count', 1, {{ top_n }}, 'int'),
    ('best_matchup_amount', 'Scoring', 'Matchup', 'Highest single-week score', 'record', 1, 1, 'points'),
    ('worst_matchup_amount', 'Scoring', 'Matchup', 'Lowest single-week score', 'record', -1, 1, 'points'),
    ('non_playoff_scoring_title_count', 'Scoring', 'Playoff', 'Snub titles', 'count', 1, {{ top_n }}, 'int'),
    ('playoff_non_scoring_title_count', 'Scoring', 'Playoff', 'Lucky-in titles', 'count', 1, {{ top_n }}, 'int'),
    ('best_non_playoff_scoring_amount', 'Scoring', 'Playoff', 'Highest playoff miss', 'record', 1, 1, 'points'),
    ('worst_playoff_non_scoring_amount', 'Scoring', 'Playoff', 'Lowest playoff team', 'record', -1, 1, 'points'),
    ('clutch_winning_title_count', 'Clutch', 'Clutch', 'Clutch-winning titles', 'count', 1, {{ top_n }}, 'int'),
    ('clutch_losing_title_count', 'Clutch', 'Clutch', 'Clutch-losing titles', 'count', 1, {{ top_n }}, 'int'),
    ('best_clutch_pct', 'Clutch', 'Clutch', 'Best career clutch win %', 'total', 1, {{ top_n }}, 'pct'),
    ('worst_clutch_pct', 'Clutch', 'Clutch', 'Worst career clutch win %', 'total', -1, {{ top_n }}, 'pct'),
    ('clutchest_season', 'Clutch', 'Clutch', 'Clutchest season', 'record', 1, 1, 'int'),
    ('unclutchest_season', 'Clutch', 'Clutch', 'Least clutch season', 'record', 1, 1, 'int'),
    ('lucky_winner_title_count', 'Matchups', 'Luck', 'Lucky-winner titles', 'count', 1, {{ top_n }}, 'int'),
    ('unlucky_loser_title_count', 'Matchups', 'Luck', 'Unlucky-loser titles', 'count', 1, {{ top_n }}, 'int'),
    ('lucky_wins_total_count', 'Matchups', 'Luck', 'Most career lucky wins', 'count', 1, {{ top_n }}, 'int'),
    ('unlucky_losses_total_count', 'Matchups', 'Luck', 'Most career unlucky losses', 'count', 1, {{ top_n }}, 'int'),
    ('luckiest_win_amount', 'Matchups', 'Luck', 'Luckiest win', 'record', 1, 1, 'int'),
    ('unluckiest_loss_amount', 'Matchups', 'Luck', 'Unluckiest loss', 'record', -1, 1, 'int'),
    ('tightest_matchups', 'Matchups', 'Margins', 'Tightest games', 'record', -1, {{ top_n }}, 'points'),
    ('biggest_blowouts', 'Matchups', 'Margins', 'Biggest blowouts', 'record', 1, {{ top_n }}, 'points'),
    ('shotgun_title_count', 'Shotgun', 'Shotgun', 'Shotgun titles', 'count', 1, {{ top_n }}, 'int'),
    ('no_shotgun_season_count', 'Shotgun', 'Shotgun', 'Clean seasons (no shotguns)', 'count', 1, {{ top_n }}, 'int'),
    ('most_shotgun_total_count', 'Shotgun', 'Shotgun', 'Most career shotguns', 'count', 1, {{ top_n }}, 'int'),
    ('least_shotgun_total_count', 'Shotgun', 'Shotgun', 'Fewest career shotguns', 'count', -1, {{ top_n }}, 'int'),
    ('highest_shotgun_season_record', 'Shotgun', 'Shotgun', 'Most shotguns in a season', 'record', 1, 1, 'int')
),

-- Career roll-ups (one row per owner) — all aggregation lives in the intermediate
career as (
    select * from {{ ref("int__owner_career_summary") }}
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
        null::varchar as season_or_week
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
        null::varchar as season_or_week
    from career
    union all
    select
        career.owner_id,
        career.owner_name,
        'unlucky_losses_total_count' as metric_key,
        career.unlucky_losses_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week
    from career
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.shotgun_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week
    from career
    cross join (values ('most_shotgun_total_count'), ('least_shotgun_total_count')) as directions (metric_key)
),

-- Career totals (points, PPG, clutch %)
career_total_candidates as (
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.points_total as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week
    from career
    cross join (values ('most_points_total'), ('least_points_total')) as directions (metric_key)
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.points_per_game as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week
    from career
    cross join (values ('most_points_ppg'), ('least_points_ppg')) as directions (metric_key)
    union all
    select
        career.owner_id,
        career.owner_name,
        directions.metric_key,
        career.clutch_win_pct as metric_value,
        0::double as tiebreak,
        null::varchar as season_or_week
    from career
    cross join (values ('best_clutch_pct'), ('worst_clutch_pct')) as directions (metric_key)
    where career.clutch_win_pct is not null
),

-- Single-extreme records sourced at owner-season grain
season_scoring_records as (
    select
        titles.owner_id,
        titles.owner_name,
        directions.metric_key,
        titles.reg_points_total as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week
    from {{ ref("int__season_titles") }} as titles
    cross join (values ('highest_scoring_season'), ('lowest_scoring_season')) as directions (metric_key)
    union all
    select
        titles.owner_id,
        titles.owner_name,
        directions.metric_key,
        titles.reg_points_per_game as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week
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
        titles.year::varchar as season_or_week
    from {{ ref("int__season_titles") }} as titles
    where not titles.made_playoffs
    union all
    select
        titles.owner_id,
        titles.owner_name,
        'worst_playoff_non_scoring_amount' as metric_key,
        titles.reg_points_total as metric_value,
        0::double as tiebreak,
        titles.year::varchar as season_or_week
    from {{ ref("int__season_titles") }} as titles
    where titles.made_playoffs
),

clutch_season_records as (
    select
        titles.owner_id,
        titles.owner_name,
        'clutchest_season' as metric_key,
        titles.clutch_wins::double as metric_value,
        titles.clutch_wins::double / nullif(titles.clutch_wins + titles.clutch_losses, 0) as tiebreak,
        titles.year::varchar || ' (' || titles.clutch_wins::varchar || '-' || titles.clutch_losses::varchar || ')'
            as season_or_week
    from {{ ref("int__season_titles") }} as titles
    where titles.clutch_wins + titles.clutch_losses > 0
    union all
    select
        titles.owner_id,
        titles.owner_name,
        'unclutchest_season' as metric_key,
        titles.clutch_losses::double as metric_value,
        -titles.clutch_wins::double / nullif(titles.clutch_wins + titles.clutch_losses, 0) as tiebreak,
        titles.year::varchar || ' (' || titles.clutch_wins::varchar || '-' || titles.clutch_losses::varchar || ')'
            as season_or_week
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
        titles.year::varchar as season_or_week
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
        lucky.year::varchar || ' W' || lucky.week::varchar as season_or_week
    from {{ ref("int__lucky_records") }} as lucky
    inner join {{ ref("int__owner_team_year_map") }} as owner_map on lucky.team_year_id = owner_map.team_year_id
    cross join (values ('best_matchup_amount'), ('worst_matchup_amount')) as directions (metric_key)
),

luck_records as (
    select
        owner_map.owner_id,
        owner_map.owner_name,
        'luckiest_win_amount' as metric_key,
        lucky.luck_points::double as metric_value,
        0::double as tiebreak,
        lucky.year::varchar || ' W' || lucky.week::varchar as season_or_week
    from {{ ref("int__lucky_records") }} as lucky
    inner join {{ ref("int__owner_team_year_map") }} as owner_map on lucky.team_year_id = owner_map.team_year_id
    where lucky.is_lucky_win
    union all
    select
        owner_map.owner_id,
        owner_map.owner_name,
        'unluckiest_loss_amount' as metric_key,
        lucky.luck_points::double as metric_value,
        0::double as tiebreak,
        lucky.year::varchar || ' W' || lucky.week::varchar as season_or_week
    from {{ ref("int__lucky_records") }} as lucky
    inner join {{ ref("int__owner_team_year_map") }} as owner_map on lucky.team_year_id = owner_map.team_year_id
    where lucky.is_unlucky_loss
),

margin_records as (
    select
        owner_map.owner_id,
        owner_map.owner_name,
        directions.metric_key,
        margins.margin as metric_value,
        0::double as tiebreak,
        margins.year::varchar || ' W' || margins.week::varchar as season_or_week
    from {{ ref("int__matchup_margins") }} as margins
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on margins.winner_team_year_id = owner_map.team_year_id
    cross join (values ('tightest_matchups'), ('biggest_blowouts')) as directions (metric_key)
    where not margins.is_tie
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
    select * from clutch_season_records
    union all
    select * from shotgun_season_records
    union all
    select * from matchup_week_records
    union all
    select * from luck_records
    union all
    select * from margin_records
),

ranked as (
    select
        meta.section,
        meta.category,
        candidates.metric_key,
        meta.metric_label,
        meta.metric_type,
        meta.value_format,
        meta.result_n,
        candidates.owner_id,
        candidates.owner_name,
        candidates.metric_value,
        candidates.season_or_week,
        rank() over (
            partition by candidates.metric_key
            order by candidates.metric_value * meta.sort_sign desc, candidates.tiebreak desc
        ) as metric_rank
    from candidates
    inner join metric_meta as meta on candidates.metric_key = meta.metric_key
)

select
    section,
    category,
    metric_key,
    metric_label,
    metric_type,
    owner_id,
    owner_name,
    round(metric_value, 2) as value,
    case value_format
        when 'int' then round(metric_value, 0)::bigint::varchar
        when 'pct' then round(metric_value, 1)::varchar || '%'
        else round(metric_value, 2)::varchar
    end as display_value,
    season_or_week,
    metric_rank::int as rank
from ranked
where metric_rank <= result_n
order by section, category, metric_key, rank
