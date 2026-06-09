with titles as (
    select * from {{ ref("int__season_titles") }}
),

-- Fan each owner-season out to one row per title metric (holder or not), so downstream
-- models can count holders, sum amounts, or take season extremes from a single tidy table.
unnested as (
    select
        titles.owner_id,
        titles.owner_name,
        titles.owner_year_id,
        titles.team_year_id,
        titles.year,
        title.metric_key,  --noqa: RF01
        title.amount,  --noqa: RF01
        title.is_title_holder  --noqa: RF01
    from titles
    cross join unnest(  --noqa: LT02
        [
            {'metric_key': 'scoring_title', 'amount': titles.reg_points_total::double, 'is_title_holder': titles.is_scoring_title},  --noqa: LT05
            {'metric_key': 'non_scoring_title', 'amount': titles.reg_points_total::double, 'is_title_holder': titles.is_non_scoring_title},  --noqa: LT05
            {'metric_key': 'matchup_title', 'amount': titles.best_week_score::double, 'is_title_holder': titles.is_matchup_title},  --noqa: LT05
            {'metric_key': 'bad_matchup_title', 'amount': titles.worst_week_score::double, 'is_title_holder': titles.is_bad_matchup_title},  --noqa: LT05
            {'metric_key': 'non_playoff_scoring_title', 'amount': titles.reg_points_total::double, 'is_title_holder': titles.is_non_playoff_scoring_title},  --noqa: LT05
            {'metric_key': 'playoff_non_scoring_title', 'amount': titles.reg_points_total::double, 'is_title_holder': titles.is_playoff_non_scoring_title},  --noqa: LT05
            {'metric_key': 'clutch_winning_title', 'amount': titles.clutch_wins::double, 'is_title_holder': titles.is_clutch_winning_title},  --noqa: LT05
            {'metric_key': 'clutch_losing_title', 'amount': titles.clutch_losses::double, 'is_title_holder': titles.is_clutch_losing_title},  --noqa: LT05
            {'metric_key': 'lucky_winner_title', 'amount': titles.lucky_wins::double, 'is_title_holder': titles.is_lucky_winner_title},  --noqa: LT05
            {'metric_key': 'unlucky_loser_title', 'amount': titles.unlucky_losses::double, 'is_title_holder': titles.is_unlucky_loser_title},  --noqa: LT05
            {'metric_key': 'shotgun_title', 'amount': titles.shotgun_count::double, 'is_title_holder': titles.is_shotgun_title},  --noqa: LT05
            {'metric_key': 'no_shotgun_season', 'amount': titles.shotgun_count::double, 'is_title_holder': titles.is_no_shotgun_season}  --noqa: LT05
        ]
    ) as unnested (title)
)

select * from unnested
