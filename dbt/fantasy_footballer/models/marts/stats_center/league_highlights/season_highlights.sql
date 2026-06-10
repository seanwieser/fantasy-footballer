-- Metric metadata (key -> category/label/type/sort/format/tooltip) lives in a seed.
with metric_meta as (
    select * from {{ ref("season_highlight_metrics") }}
),

-- Per-season title holders (co-titles included) — read straight from the tidy long table
title_candidates as (
    select
        year,
        team_year_id,
        owner_id,
        owner_name,
        metric_key,
        amount as metric_value,
        null::varchar as detail
    from {{ ref("int__season_titles_long") }}
    where is_title_holder
),

-- Per-season game-level titles (winner is the owner, loser the opponent), each ranked on a single
-- number: the victory margin (tightest game / biggest blowout) or the combined score (shootout /
-- slugfest). The winner/loser join and the composed display subtitle are identical for all four, so
-- the direction key just picks which number is ranked. Mirrors all_time_records' matchup_game_records.
matchup_candidates as (
    select
        margins.year,
        winner.team_year_id,
        winner.owner_id,
        winner.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'highest_shootouts' then margins.combined
            when 'lowest_slugfests' then margins.combined
            else margins.margin
        end as metric_value,
        'def. ' || loser.owner_name || ' · ' ||
        round(margins.winner_score, 2)::varchar || '-' || round(margins.loser_score, 2)::varchar ||
        ' · Wk ' || margins.week::varchar as detail
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

-- Per-season roster-move leaders: who made the most acquisitions / trades that year. Zeros are
-- dropped so a quiet season renders the catalog's empty-state card instead of a "0" winner.
transaction_candidates as (
    select
        teams.year,
        teams.team_year_id,
        owner_map.owner_id,
        owner_map.owner_name,
        directions.metric_key,
        case directions.metric_key
            when 'most_acquisitions_season' then teams.acquisitions
            else teams.trades
        end::double as metric_value,
        null::varchar as detail
    from {{ ref("base_s001__teams") }} as teams
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on teams.team_year_id = owner_map.team_year_id
    cross join (values ('most_acquisitions_season'), ('most_trades_season')) as directions (metric_key)
    where case directions.metric_key
        when 'most_acquisitions_season' then teams.acquisitions
        else teams.trades
    end > 0
),

-- Per-season postseason result titles: the league champion and the toilet-bowl loser (dead last),
-- each shown with their regular-season seed (champion = upset factor, toilet-bowl = collapse factor).
postseason_title_candidates as (
    select
        postseason.year,
        postseason.team_year_id,
        owner_map.owner_id,
        owner_map.owner_name,
        directions.metric_key,
        postseason.seed::double as metric_value,
        null::varchar as detail
    from {{ ref("int__team_postseason") }} as postseason
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on postseason.team_year_id = owner_map.team_year_id
    cross join (values ('champion'), ('toilet_bowl_loser')) as directions (metric_key)
    where
        (directions.metric_key = 'champion' and postseason.is_champion) or
        (directions.metric_key = 'toilet_bowl_loser' and postseason.is_last)
),

candidates as (
    select * from title_candidates
    union all
    select * from matchup_candidates
    union all
    select * from transaction_candidates
    union all
    select * from postseason_title_candidates
),

-- Regular-season weekly scores, used to find each team's best/worst single week.
reg_results as (
    select
        team_year_id,
        week,
        score_for
    from {{ ref("int__team_week_results") }}
    where not is_playoff and outcome != 'U'
),

extreme_weeks as (
    select
        team_year_id,
        arg_max(week, score_for) as best_week,
        arg_min(week, score_for) as worst_week
    from reg_results
    group by team_year_id
),

shotgun_weeks as (
    select
        team_year_id,
        if(count(*) = 1, 'Wk ', 'Wks ') || string_agg(week::varchar, ', ' order by week) as label
    from {{ ref("int__shotguns") }}
    where is_shotgun
    group by team_year_id
),

luck_weeks as (
    select
        team_year_id,
        if(count(*) filter (where is_lucky_win) = 1, 'Wk ', 'Wks ') ||
        string_agg(week::varchar, ', ' order by week) filter (where is_lucky_win) as lucky_label,
        if(count(*) filter (where is_unlucky_loss) = 1, 'Wk ', 'Wks ') ||
        string_agg(week::varchar, ', ' order by week) filter (where is_unlucky_loss) as unlucky_label
    from {{ ref("int__lucky_records") }}
    group by team_year_id
),

-- One row per team-season of subtitle context: reg-season seed, clutch record, key weeks.
title_context as (
    select
        teams.team_year_id,
        clutch.record as clutch_record,
        extreme_weeks.best_week,
        extreme_weeks.worst_week,
        shotgun_weeks.label as shotgun_label,
        luck_weeks.lucky_label,
        luck_weeks.unlucky_label,
        season_titles.playoff_teams_outscored,
        season_titles.nonplayoff_teams_outscoring,
        -- Ordinal of the end-of-regular-season standing, e.g. "7th seed".
        teams.standing::varchar || case
            when teams.standing % 100 in (11, 12, 13) then 'th'
            when teams.standing % 10 = 1 then 'st'
            when teams.standing % 10 = 2 then 'nd'
            when teams.standing % 10 = 3 then 'rd'
            else 'th'
        end || ' seed' as seed_label
    from {{ ref("base_s001__teams") }} as teams
    left join {{ ref("int__clutch_records") }} as clutch on teams.team_year_id = clutch.team_year_id
    left join {{ ref("int__season_titles") }} as season_titles on teams.team_year_id = season_titles.team_year_id
    left join extreme_weeks on teams.team_year_id = extreme_weeks.team_year_id
    left join shotgun_weeks on teams.team_year_id = shotgun_weeks.team_year_id
    left join luck_weeks on teams.team_year_id = luck_weeks.team_year_id
),

ranked as (
    select
        meta.section,
        candidates.metric_key,
        meta.metric_label,
        meta.description,
        meta.display_order,
        meta.value_format,
        candidates.year,
        candidates.owner_id,
        candidates.owner_name,
        candidates.metric_value,
        ctx.clutch_record,
        -- Margin rows already carry their full composed subtitle; title rows get a "how/when/where
        -- earned" line: end-of-season seed, the key week(s), or the clutch record.
        coalesce(candidates.detail, case candidates.metric_key
            when 'scoring_title' then ctx.seed_label
            when 'non_scoring_title' then ctx.seed_label
            when 'non_playoff_scoring_title'
                then ctx.seed_label || ' · outscored ' || ctx.playoff_teams_outscored::varchar || ' who made it'
            when 'playoff_non_scoring_title'
                then ctx.seed_label || ' · snuck in over ' || ctx.nonplayoff_teams_outscoring::varchar
            when 'matchup_title' then 'Wk ' || ctx.best_week::varchar
            when 'bad_matchup_title' then 'Wk ' || ctx.worst_week::varchar
            when 'shotgun_title' then ctx.shotgun_label
            when 'lucky_winner_title' then ctx.lucky_label
            when 'unlucky_loser_title' then ctx.unlucky_label
        end) as detail,
        rank() over (
            partition by candidates.year, candidates.metric_key
            order by candidates.metric_value * meta.sort_sign desc
        ) as metric_rank
    from candidates
    inner join metric_meta as meta on candidates.metric_key = meta.metric_key
    left join title_context as ctx on candidates.team_year_id = ctx.team_year_id
)

select
    section,
    metric_key,
    metric_label,
    description,
    display_order::int as display_order,
    year,
    owner_id,
    owner_name,
    coalesce(
        -- Clutch titles headline the W-L record itself, not the raw clutch-win/loss count.
        case when metric_key in ('clutch_winning_title', 'clutch_losing_title') then clutch_record end,
        {{ format_metric_value("metric_value", "value_format") }}
    ) as display_value,
    detail,
    metric_rank::int as rank
from ranked
-- Every By-Season metric is a single-winner title; keep rank 1 (co-titles share it).
where metric_rank = 1
order by year, display_order, rank
