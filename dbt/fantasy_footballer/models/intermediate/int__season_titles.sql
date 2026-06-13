with shotgun_counts as (
    select
        team_year_id,
        count_if(is_shotgun)::int as shotgun_count
    from {{ ref("int__shotguns") }}
    group by team_year_id
),

clutch as (
    select
        team_year_id,
        split_part(record, '-', 1)::int as clutch_wins,
        split_part(record, '-', 2)::int as clutch_losses
    from {{ ref("int__clutch_records") }}
),

owner_seasons as (
    select
        scoring.owner_id,
        scoring.owner_name,
        scoring.owner_year_id,
        scoring.team_year_id,
        scoring.year,
        scoring.reg_points_total,
        scoring.reg_points_per_game,
        scoring.best_week_score,
        scoring.worst_week_score,
        scoring.made_playoffs,
        coalesce(clutch.clutch_wins, 0) as clutch_wins,
        coalesce(clutch.clutch_losses, 0) as clutch_losses,
        coalesce(shotgun_counts.shotgun_count, 0) as shotgun_count,
        lineup.points_left_on_table,
        lineup.lineup_efficiency,
        all_play.all_play_win_pct,
        all_play.expected_wins,
        all_play.schedule_luck,
        case
            when coalesce(clutch.clutch_wins, 0) + coalesce(clutch.clutch_losses, 0) > 0
                then clutch.clutch_wins::double / (clutch.clutch_wins + clutch.clutch_losses)
            else 0
        end as clutch_win_pct
    from {{ ref("int__owner_season_scoring") }} as scoring
    left join clutch on scoring.team_year_id = clutch.team_year_id
    left join shotgun_counts on scoring.team_year_id = shotgun_counts.team_year_id
    left join {{ ref("int__owner_lineup_efficiency") }} as lineup on scoring.team_year_id = lineup.team_year_id
    left join {{ ref("int__owner_season_all_play") }} as all_play on scoring.team_year_id = all_play.team_year_id
),

-- Cross-team points comparison within a season: how many playoff teams each team outscored
-- (and how many non-playoff teams outscored it). A "snub" requires outscoring >= 1 playoff team
-- (more deserving by points than someone who got in); "lucked in" is the mirror.
points_vs_field as (
    select
        team.team_year_id,
        count(*) filter (
            where other.made_playoffs and other.reg_points_total < team.reg_points_total
        )::int as playoff_teams_outscored,
        count(*) filter (
            where not other.made_playoffs and other.reg_points_total > team.reg_points_total
        )::int as nonplayoff_teams_outscoring
    from owner_seasons as team
    inner join owner_seasons as other
        on team.year = other.year and team.team_year_id != other.team_year_id
    group by team.team_year_id
),

-- All-play analogue of points_vs_field: a more rigorous snub gate ranks on schedule-neutral merit
-- (all-play win%) instead of raw points. A snub out-played (not just outscored) a team that got in.
all_play_vs_field as (
    select
        team.team_year_id,
        count(*) filter (
            where other.made_playoffs and other.all_play_win_pct < team.all_play_win_pct
        )::int as all_play_playoff_teams_outranked,
        count(*) filter (
            where not other.made_playoffs and other.all_play_win_pct > team.all_play_win_pct
        )::int as all_play_nonplayoff_teams_outranking
    from owner_seasons as team
    inner join owner_seasons as other
        on team.year = other.year and team.team_year_id != other.team_year_id
    group by team.team_year_id
),

ranked as (
    select
        *,
        rank() over (partition by year order by reg_points_total desc) as scoring_rank,
        rank() over (partition by year order by reg_points_total asc) as non_scoring_rank,
        rank() over (partition by year, made_playoffs order by reg_points_total desc) as snub_rank,
        rank() over (partition by year, made_playoffs order by reg_points_total asc) as luck_in_rank,
        rank() over (partition by year, made_playoffs order by all_play_win_pct desc) as all_play_snub_rank,
        rank() over (partition by year, made_playoffs order by all_play_win_pct asc) as all_play_luck_in_rank,
        rank() over (partition by year order by schedule_luck desc) as lucky_schedule_rank,
        rank() over (partition by year order by schedule_luck asc) as unlucky_schedule_rank,
        rank() over (partition by year order by clutch_wins desc, clutch_win_pct desc) as clutch_win_rank,
        rank() over (partition by year order by clutch_losses desc, clutch_win_pct asc) as clutch_loss_rank,
        rank() over (partition by year order by shotgun_count desc) as shotgun_rank,
        rank() over (partition by year order by points_left_on_table asc) as best_lineup_rank,
        rank() over (partition by year order by points_left_on_table desc) as worst_lineup_rank,
        rank() over (partition by year order by lineup_efficiency desc) as efficiency_rank,
        rank() over (partition by year order by lineup_efficiency asc) as inefficiency_rank
    from owner_seasons
)

select
    ranked.owner_id,
    ranked.owner_name,
    ranked.owner_year_id,
    ranked.team_year_id,
    ranked.year,
    ranked.reg_points_total,
    ranked.reg_points_per_game,
    ranked.best_week_score,
    ranked.worst_week_score,
    ranked.made_playoffs,
    ranked.clutch_wins,
    ranked.clutch_losses,
    ranked.shotgun_count,
    ranked.points_left_on_table,
    ranked.lineup_efficiency,
    ranked.all_play_win_pct,
    ranked.expected_wins,
    ranked.schedule_luck,
    points_vs_field.playoff_teams_outscored,
    points_vs_field.nonplayoff_teams_outscoring,
    all_play_vs_field.all_play_playoff_teams_outranked,
    all_play_vs_field.all_play_nonplayoff_teams_outranking,
    ranked.scoring_rank = 1 as is_scoring_title,
    ranked.non_scoring_rank = 1 as is_non_scoring_title,
    -- Matchup titles derive from the shared league single-week extreme so they can never drift from
    -- the is_best_week / is_worst_week chips in int__team_week_highlights (same source model).
    ranked.best_week_score = extremes.league_best_score as is_matchup_title,
    ranked.worst_week_score = extremes.league_worst_score as is_bad_matchup_title,
    not ranked.made_playoffs and ranked.snub_rank = 1 and points_vs_field.playoff_teams_outscored >= 1
        as is_non_playoff_scoring_title,
    ranked.made_playoffs and ranked.luck_in_rank = 1 and points_vs_field.nonplayoff_teams_outscoring >= 1
        as is_playoff_non_scoring_title,
    ranked.clutch_win_rank = 1 and ranked.clutch_wins > 0 as is_clutch_winning_title,
    ranked.clutch_loss_rank = 1 and ranked.clutch_losses > 0 as is_clutch_losing_title,
    ranked.shotgun_rank = 1 and ranked.shotgun_count > 0 as is_shotgun_title,
    ranked.shotgun_count = 0 as is_no_shotgun_season,
    -- Lineup-setter titles, two complementary angles (from int__owner_lineup_efficiency, depth-neutral):
    -- absolute points left on the bench vs the optimal legal lineup, and the share of the optimal
    -- captured (efficiency %). Points reward raw start/sit production; efficiency normalizes for how
    -- much was even on the table, so a low-scoring team that set near-perfect lineups can still lead.
    ranked.best_lineup_rank = 1 as is_best_lineup_title,
    ranked.worst_lineup_rank = 1 as is_worst_lineup_title,
    ranked.efficiency_rank = 1 as is_most_efficient_lineup_title,
    ranked.inefficiency_rank = 1 as is_least_efficient_lineup_title,
    -- Occurrence flags (broader than the titles above): every snubbed / lucked-in team-season.
    not ranked.made_playoffs and points_vs_field.playoff_teams_outscored >= 1 as is_snubbed,
    ranked.made_playoffs and points_vs_field.nonplayoff_teams_outscoring >= 1 as is_lucked_in,
    -- Schedule-luck titles: most/least wins relative to a schedule-neutral expectation (all-play).
    ranked.lucky_schedule_rank = 1 and ranked.schedule_luck > 0 as is_lucky_schedule_title,
    ranked.unlucky_schedule_rank = 1 and ranked.schedule_luck < 0 as is_unlucky_schedule_title,
    -- All-play snub/lucky-in: the merit-based analogue of the points-based snub above. A snub
    -- out-played (higher all-play win%) a team that made the playoffs; lucked-in is the mirror.
    not ranked.made_playoffs and ranked.all_play_snub_rank = 1 and
    all_play_vs_field.all_play_playoff_teams_outranked >= 1 as is_all_play_snub_title,
    ranked.made_playoffs and ranked.all_play_luck_in_rank = 1 and
    all_play_vs_field.all_play_nonplayoff_teams_outranking >= 1 as is_all_play_luck_in_title,
    not ranked.made_playoffs and all_play_vs_field.all_play_playoff_teams_outranked >= 1
        as is_all_play_snubbed,
    ranked.made_playoffs and all_play_vs_field.all_play_nonplayoff_teams_outranking >= 1
        as is_all_play_lucked_in
from ranked
inner join points_vs_field on ranked.team_year_id = points_vs_field.team_year_id
inner join all_play_vs_field on ranked.team_year_id = all_play_vs_field.team_year_id
inner join {{ ref("int__league_season_week_extremes") }} as extremes on ranked.year = extremes.year
