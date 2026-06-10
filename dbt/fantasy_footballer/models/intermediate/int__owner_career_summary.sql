with title_aggregates as (
    select
        owner_id,
        max(owner_name) as owner_name,
        count_if(metric_key = 'scoring_title' and is_title_holder)::int as scoring_title_count,
        count_if(metric_key = 'non_scoring_title' and is_title_holder)::int as non_scoring_title_count,
        count_if(metric_key = 'matchup_title' and is_title_holder)::int as matchup_title_count,
        count_if(metric_key = 'bad_matchup_title' and is_title_holder)::int as bad_matchup_title_count,
        count_if(metric_key = 'non_playoff_scoring_title' and is_title_holder)::int as non_playoff_scoring_title_count,
        count_if(metric_key = 'playoff_non_scoring_title' and is_title_holder)::int as playoff_non_scoring_title_count,
        count_if(metric_key = 'clutch_winning_title' and is_title_holder)::int as clutch_winning_title_count,
        count_if(metric_key = 'clutch_losing_title' and is_title_holder)::int as clutch_losing_title_count,
        count_if(metric_key = 'lucky_winner_title' and is_title_holder)::int as lucky_winner_title_count,
        count_if(metric_key = 'unlucky_loser_title' and is_title_holder)::int as unlucky_loser_title_count,
        count_if(metric_key = 'shotgun_title' and is_title_holder)::int as shotgun_title_count,
        count_if(metric_key = 'no_shotgun_season' and is_title_holder)::int as no_shotgun_season_count,
        sum(case when metric_key = 'lucky_winner_title' then amount end)::double as lucky_wins_total,
        sum(case when metric_key = 'unlucky_loser_title' then amount end)::double as unlucky_losses_total,
        sum(case when metric_key = 'shotgun_title' then amount end)::double as shotgun_total,
        sum(case when metric_key = 'clutch_winning_title' then amount end)::double as clutch_wins_total,
        sum(case when metric_key = 'clutch_losing_title' then amount end)::double as clutch_losses_total
    from {{ ref("int__season_titles_long") }}
    group by owner_id
),

scoring_aggregates as (
    select
        owner_id,
        count(*)::int as seasons_played,
        sum(reg_points_total)::double as points_total,
        sum(games_played)::double as games_total
    from {{ ref("int__owner_season_scoring") }}
    group by owner_id
),

snub_aggregates as (
    select
        owner_id,
        count_if(is_snubbed)::int as snub_total,
        count_if(is_lucked_in)::int as luck_in_total
    from {{ ref("int__season_titles") }}
    group by owner_id
),

-- Career roster-move totals: waiver/free-agent acquisitions and completed trades across all seasons.
transaction_aggregates as (
    select
        owner_map.owner_id,
        sum(teams.acquisitions)::int as acquisitions_total,
        sum(teams.trades)::int as trades_total
    from {{ ref("base_s001__teams") }} as teams
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on teams.team_year_id = owner_map.team_year_id
    group by owner_map.owner_id
),

combined as (
    select
        title_aggregates.*,
        scoring_aggregates.seasons_played,
        scoring_aggregates.points_total,
        scoring_aggregates.games_total,
        snub_aggregates.snub_total,
        snub_aggregates.luck_in_total,
        transaction_aggregates.acquisitions_total,
        transaction_aggregates.trades_total,
        scoring_aggregates.points_total / nullif(scoring_aggregates.games_total, 0) as points_per_game,
        title_aggregates.clutch_wins_total /
        nullif(title_aggregates.clutch_wins_total + title_aggregates.clutch_losses_total, 0) *
        100 as clutch_win_pct
    from title_aggregates
    inner join scoring_aggregates on title_aggregates.owner_id = scoring_aggregates.owner_id
    inner join snub_aggregates on title_aggregates.owner_id = snub_aggregates.owner_id
    inner join transaction_aggregates on title_aggregates.owner_id = transaction_aggregates.owner_id
)

select * from combined
