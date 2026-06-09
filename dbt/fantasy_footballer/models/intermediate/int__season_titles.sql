with shotgun_counts as (
    select
        team_year_id,
        count_if(is_shotgun)::int as shotgun_count
    from {{ ref("int__shotguns") }}
    group by team_year_id
),

luck_counts as (
    select
        team_year_id,
        count_if(is_lucky_win)::int as lucky_wins,
        count_if(is_unlucky_loss)::int as unlucky_losses
    from {{ ref("int__lucky_records") }}
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
        coalesce(luck_counts.lucky_wins, 0) as lucky_wins,
        coalesce(luck_counts.unlucky_losses, 0) as unlucky_losses,
        coalesce(shotgun_counts.shotgun_count, 0) as shotgun_count,
        case
            when coalesce(clutch.clutch_wins, 0) + coalesce(clutch.clutch_losses, 0) > 0
                then clutch.clutch_wins::double / (clutch.clutch_wins + clutch.clutch_losses)
            else 0
        end as clutch_win_pct
    from {{ ref("int__owner_season_scoring") }} as scoring
    left join clutch on scoring.team_year_id = clutch.team_year_id
    left join luck_counts on scoring.team_year_id = luck_counts.team_year_id
    left join shotgun_counts on scoring.team_year_id = shotgun_counts.team_year_id
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

ranked as (
    select
        *,
        rank() over (partition by year order by reg_points_total desc) as scoring_rank,
        rank() over (partition by year order by reg_points_total asc) as non_scoring_rank,
        rank() over (partition by year order by best_week_score desc) as matchup_rank,
        rank() over (partition by year order by worst_week_score asc) as bad_matchup_rank,
        rank() over (partition by year, made_playoffs order by reg_points_total desc) as snub_rank,
        rank() over (partition by year, made_playoffs order by reg_points_total asc) as luck_in_rank,
        rank() over (partition by year order by clutch_wins desc, clutch_win_pct desc) as clutch_win_rank,
        rank() over (partition by year order by clutch_losses desc, clutch_win_pct asc) as clutch_loss_rank,
        rank() over (partition by year order by lucky_wins desc) as lucky_rank,
        rank() over (partition by year order by unlucky_losses desc) as unlucky_rank,
        rank() over (partition by year order by shotgun_count desc) as shotgun_rank
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
    ranked.lucky_wins,
    ranked.unlucky_losses,
    ranked.shotgun_count,
    points_vs_field.playoff_teams_outscored,
    points_vs_field.nonplayoff_teams_outscoring,
    ranked.scoring_rank = 1 as is_scoring_title,
    ranked.non_scoring_rank = 1 as is_non_scoring_title,
    ranked.matchup_rank = 1 as is_matchup_title,
    ranked.bad_matchup_rank = 1 as is_bad_matchup_title,
    not ranked.made_playoffs and ranked.snub_rank = 1 and points_vs_field.playoff_teams_outscored >= 1
        as is_non_playoff_scoring_title,
    ranked.made_playoffs and ranked.luck_in_rank = 1 and points_vs_field.nonplayoff_teams_outscoring >= 1
        as is_playoff_non_scoring_title,
    ranked.clutch_win_rank = 1 and ranked.clutch_wins > 0 as is_clutch_winning_title,
    ranked.clutch_loss_rank = 1 and ranked.clutch_losses > 0 as is_clutch_losing_title,
    ranked.lucky_rank = 1 and ranked.lucky_wins > 0 as is_lucky_winner_title,
    ranked.unlucky_rank = 1 and ranked.unlucky_losses > 0 as is_unlucky_loser_title,
    ranked.shotgun_rank = 1 and ranked.shotgun_count > 0 as is_shotgun_title,
    ranked.shotgun_count = 0 as is_no_shotgun_season,
    -- Occurrence flags (broader than the titles above): every snubbed / lucked-in team-season.
    not ranked.made_playoffs and points_vs_field.playoff_teams_outscored >= 1 as is_snubbed,
    ranked.made_playoffs and points_vs_field.nonplayoff_teams_outscoring >= 1 as is_lucked_in
from ranked
inner join points_vs_field on ranked.team_year_id = points_vs_field.team_year_id
