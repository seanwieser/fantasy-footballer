with players_raw as (
    select
        playerid::varchar as persistent_player_id,
        name::varchar as name,
        year::integer as year,
        eligibleslots::varchar [] as eligible_slots,
        proteam::varchar as pro_team,
        onteamid::integer as team_id,
        position::varchar as position_slot,
        injured::boolean as is_injured,
        total_points::double as total_points,
        avg_points::double as avg_points,
        projected_total_points::double as projected_total_points,
        projected_avg_points::double as projected_avg_points,
        percent_owned::double as percent_owned,
        percent_started::double as percent_started,
        stats as stats_raw,
        persistent_player_id || '_' || year::varchar as player_id,
        try_cast(posrank as integer) as position_rank,
        if(injurystatus != '[]', replace(injurystatus::varchar, '"', '')::varchar, null) as injury_status
    from {{ source("s001", "players") }}
)

select *
from players_raw
