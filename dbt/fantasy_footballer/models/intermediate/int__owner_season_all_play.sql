with all_play_season as (
    select
        team_year_id,
        sum(all_play_wins)::int as all_play_wins,
        sum(all_play_losses)::int as all_play_losses,
        sum(all_play_ties)::int as all_play_ties,
        sum(all_play_games)::int as all_play_games,
        count_if(is_lucky_win)::int as lucky_win_weeks,
        count_if(is_unlucky_loss)::int as unlucky_loss_weeks
    from {{ ref("int__all_play_records") }}
    group by team_year_id
),

-- Actual head-to-head reg-season record, to contrast with the schedule-neutral expectation.
actual_record as (
    select
        team_year_id,
        count_if(outcome = 'W')::int as actual_wins,
        count_if(outcome = 'L')::int as actual_losses
    from {{ ref("int__team_week_results") }}
    where not is_playoff and outcome != 'U'
    group by team_year_id
),

owner_season_all_play as (
    select
        scoring.owner_id,
        scoring.owner_name,
        scoring.owner_year_id,
        scoring.team_year_id,
        scoring.year,
        scoring.games_played,
        scoring.made_playoffs,
        all_play_season.all_play_wins,
        all_play_season.all_play_losses,
        all_play_season.all_play_ties,
        all_play_season.all_play_games,
        all_play_season.lucky_win_weeks,
        all_play_season.unlucky_loss_weeks,
        actual_record.actual_wins,
        actual_record.actual_losses,
        (all_play_season.all_play_wins + 0.5 * all_play_season.all_play_ties) /
        all_play_season.all_play_games as all_play_win_pct,
        (all_play_season.all_play_wins + 0.5 * all_play_season.all_play_ties) /
        all_play_season.all_play_games * scoring.games_played as expected_wins,
        actual_record.actual_wins -
        (all_play_season.all_play_wins + 0.5 * all_play_season.all_play_ties) /
        all_play_season.all_play_games * scoring.games_played as schedule_luck
    from {{ ref("int__owner_season_scoring") }} as scoring
    inner join all_play_season on scoring.team_year_id = all_play_season.team_year_id
    inner join actual_record on scoring.team_year_id = actual_record.team_year_id
)

select * from owner_season_all_play
