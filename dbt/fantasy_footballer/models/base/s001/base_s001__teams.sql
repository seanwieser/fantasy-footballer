select
    team_id::int as team_id,
    team_id::varchar || '_' || year::varchar as team_year_id,
    year::int as year,
    team_abbrev::varchar as team_abbrev,
    team_name::varchar as team_name,
    division_id::int as division_id,
    division_name::varchar as division_name,
    wins::int as wins,
    losses::int as losses,
    ties::int as ties,
    wins::int + losses::int + ties::int as games_played,
    points_for::double as points_for,
    points_against::double as points_against,
    acquisitions::int as acquisitions,
    acquisition_budget_spent::int as acquisition_budget_spent,
    drops::int as drops,
    trades::int as trades,
    playoff_pct::double as playoff_pct,
    draft_projected_rank::int as draft_projected_rank,
    standing::int as standing,
    final_standing::int as final_standing,
    schedule::struct(
                week int,
                lineup struct(
                    playerId varchar,
                    lineupSlot varchar
                )[],
                score_for double,
                outcome varchar,
                opponent_team_id int
            )[] as weeks_raw,
    upper(left(trim(owners[1].firstname::varchar), 1)) ||
    lower(substring(trim(owners[1].firstname::varchar), 2, length(trim(owners[1].firstname::varchar))))
        as first_name,
    upper(left(trim(owners[1].lastname::varchar), 1)) ||
    lower(substring(trim(owners[1].lastname::varchar), 2, length(trim(owners[1].lastname::varchar)))) as last_name,
    first_name || ' ' || last_name as display_name,
    (streak_type::varchar)[1] as streak_type,
    streak_length::varchar as streak_length,
    (streak_type::varchar)[1] || streak_length::varchar as streak,
    meta__source_path::varchar as meta__source_path,
    meta__date_effective::date as meta__date_effective,
    meta__date_pulled::date as meta__date_pulled
from {{ source("s001", "teams") }}
