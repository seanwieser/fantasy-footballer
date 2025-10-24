with teams_with_ids as (
    select
        lower(owner_display_names.owner_id::varchar || '_' || s001_teams.year) as owner_year_id,
        s001_teams.team_year_id,
        owner_display_names.owner_id,
        s001_teams.year,
        owner_display_names.owner_name::varchar as owner_name,
        s001_teams.display_name,
        s001_teams.first_name,
        s001_teams.last_name,
        s001_teams.team_abbrev,
        s001_teams.team_name,
        s001_teams.division_id,
        s001_teams.division_name,
        s001_teams.wins,
        s001_teams.losses,
        s001_teams.ties,
        s001_teams.points_for,
        s001_teams.points_against,
        s001_teams.acquisitions,
        s001_teams.acquisition_budget_spent,
        s001_teams.drops,
        s001_teams.trades,
        s001_teams.playoff_pct,
        s001_teams.draft_projected_rank,
        s001_teams.streak_length,
        s001_teams.streak_type,
        s001_teams.streak,
        s001_teams.standing,
        s001_teams.final_standing,
        s001_teams.roster,
        s001_teams.matchups_raw
    from {{ ref("base_s001__teams") }} as s001_teams
    left join {{ ref("stg__owner_display_names") }} as owner_display_names
        on s001_teams.display_name = owner_display_names.display_name
)

select *
from teams_with_ids
