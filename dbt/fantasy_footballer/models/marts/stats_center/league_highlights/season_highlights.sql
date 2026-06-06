{% set top_n = 3 %}

with metric_meta (
    metric_key, category, metric_label, metric_type, sort_sign, result_n, value_format
) as (
    values
    ('scoring_title', 'Season', 'Scoring title', 'title', 1, 1, 'points'),
    ('non_scoring_title', 'Season', 'Non-scoring title', 'title', -1, 1, 'points'),
    ('matchup_title', 'Matchup', 'Best-week title', 'title', 1, 1, 'points'),
    ('bad_matchup_title', 'Matchup', 'Worst-week title', 'title', -1, 1, 'points'),
    ('non_playoff_scoring_title', 'Playoff', 'Snub title', 'title', 1, 1, 'points'),
    ('playoff_non_scoring_title', 'Playoff', 'Lucky-in title', 'title', -1, 1, 'points'),
    ('clutch_winning_title', 'Clutch', 'Clutch-winning title', 'title', 1, 1, 'int'),
    ('clutch_losing_title', 'Clutch', 'Clutch-losing title', 'title', 1, 1, 'int'),
    ('lucky_winner_title', 'Luck', 'Lucky-winner title', 'title', 1, 1, 'int'),
    ('unlucky_loser_title', 'Luck', 'Unlucky-loser title', 'title', 1, 1, 'int'),
    ('shotgun_title', 'Shotgun', 'Shotgun title', 'title', 1, 1, 'int'),
    ('no_shotgun_season', 'Shotgun', 'Clean season', 'title', 1, 1, 'int'),
    ('tightest_matchups', 'Margins', 'Tightest game', 'leaderboard', -1, {{ top_n }}, 'points'),
    ('biggest_blowouts', 'Margins', 'Biggest blowout', 'leaderboard', 1, {{ top_n }}, 'points')
),

-- Per-season title holders (co-titles included) — read straight from the tidy long table
title_candidates as (
    select
        year,
        owner_id,
        owner_name,
        metric_key,
        amount as metric_value,
        null::varchar as opponent_name,
        null::int as week
    from {{ ref("int__season_titles_long") }}
    where is_title_holder
),

-- Per-season margin leaderboards (winner is the owner, loser the opponent)
margin_candidates as (
    select
        margins.year,
        winner.owner_id,
        winner.owner_name,
        directions.metric_key,
        margins.margin as metric_value,
        loser.owner_name as opponent_name,
        margins.week
    from {{ ref("int__matchup_margins") }} as margins
    inner join {{ ref("int__owner_team_year_map") }} as winner
        on margins.winner_team_year_id = winner.team_year_id
    inner join {{ ref("int__owner_team_year_map") }} as loser
        on margins.loser_team_year_id = loser.team_year_id
    cross join (values ('tightest_matchups'), ('biggest_blowouts')) as directions (metric_key)
    where not margins.is_tie
),

candidates as (
    select * from title_candidates
    union all
    select * from margin_candidates
),

ranked as (
    select
        meta.category,
        candidates.metric_key,
        meta.metric_label,
        meta.metric_type,
        meta.value_format,
        meta.result_n,
        candidates.year,
        candidates.owner_id,
        candidates.owner_name,
        candidates.metric_value,
        candidates.opponent_name,
        candidates.week,
        rank() over (
            partition by candidates.year, candidates.metric_key
            order by candidates.metric_value * meta.sort_sign desc
        ) as metric_rank
    from candidates
    inner join metric_meta as meta on candidates.metric_key = meta.metric_key
)

select
    category,
    metric_key,
    metric_label,
    metric_type,
    year,
    owner_id,
    owner_name,
    round(metric_value, 2) as value,
    case value_format
        when 'int' then round(metric_value, 0)::bigint::varchar
        when 'pct' then round(metric_value, 1)::varchar || '%'
        else round(metric_value, 2)::varchar
    end as display_value,
    opponent_name,
    week,
    metric_rank::int as rank
from ranked
where metric_rank <= result_n
order by year, category, metric_key, rank
