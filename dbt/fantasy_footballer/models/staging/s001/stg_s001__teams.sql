with teams_raw as (
    select
        upper(left(trim(owners[1].firstName::varchar), 1)) ||
            lower(substring(trim(owners[1].firstName::varchar), 2, length(trim(owners[1].firstName::varchar)))) as first_name,
        upper(left(trim(owners[1].lastName::varchar), 1)) ||
            lower(substring(trim(owners[1].lastName::varchar), 2, length(trim(owners[1].lastName::varchar)))) as last_name,
        first_name || ' ' || last_name                       as display_name,
        year::integer                                        as year,
        team_abbrev::varchar                                 as team_abbrev,
        team_name::varchar                                   as team_name,
        division_id::integer                                 as division_id,
        division_name::varchar                               as division_name,
        wins::integer                                        as wins,
        losses::integer                                      as losses,
        ties::integer                                        as ties,
        points_for::double                                   as points_for,
        points_against::double                               as points_against,
        acquisitions::integer                                as acquisitions,
        acquisition_budget_spent::integer                    as acquisition_budget_spent,
        drops::integer                                       as drops,
        trades::integer                                      as trades,
        playoff_pct::double                                  as playoff_pct,
        draft_projected_rank::integer                        as draft_projected_rank,
        streak_length::integer                               as streak_length,
        (streak_type::varchar)[1]                            as streak_type,
        (streak_type::varchar)[1] || streak_length::varchar  as streak,
        standing::integer                                    as standing,
        final_standing::integer                              as final_standing,
        roster::integer[]                                    as roster,
        schedule                                             as schedule_raw
    from {{ source("s001", "teams") }} s001_teams

),
teams_with_ids as (
    select
        display_names.owner_id                                          as owner_id,
        owner_names.owner_name                                          as owner_name,
        lower(display_names.owner_id::varchar || '_' || teams_raw.year) as team_id,
        teams_raw.display_name,
        teams_raw.first_name,
        teams_raw.last_name,
        teams_raw.year,
        teams_raw.team_abbrev,
        teams_raw.team_name,
        teams_raw.division_id,
        teams_raw.division_name,
        teams_raw.wins,
        teams_raw.losses,
        teams_raw.ties,
        teams_raw.points_for,
        teams_raw.points_against,
        teams_raw.acquisitions,
        teams_raw.acquisition_budget_spent,
        teams_raw.drops,
        teams_raw.trades,
        teams_raw.playoff_pct,
        teams_raw.draft_projected_rank,
        teams_raw.streak_length,
        teams_raw.streak_type,
        teams_raw.streak,
        teams_raw.standing,
        teams_raw.final_standing,
        teams_raw.roster,
        teams_raw.schedule_raw
    from teams_raw
    join {{ ref("display_names") }} display_names
    on teams_raw.display_name = display_names.display_name
    join {{ ref("owner_names") }} owner_names
    on display_names.owner_id = owner_names.owner_id
)
select *
from teams_with_ids