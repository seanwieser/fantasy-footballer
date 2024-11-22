with players_raw as (
    select
        playerId::varchar                                                                   as persistent_player_id,
        name::varchar                                                                       as name,
        year::integer                                                                       as year,
        persistent_player_id || '_' || year::varchar                                        as player_id,
        try_cast(posRank as integer)                                                        as position_rank,
        eligibleSlots::varchar[]                                                            as eligible_slots,
        proTeam::varchar                                                                    as pro_team,
        onTeamId::integer                                                                   as team_id,
        position::varchar                                                                   as position_slot,
        if(injuryStatus != '[]', replace(injuryStatus::varchar, '"', '')::varchar, null)    as injury_status,
        injured::boolean                                                                    as is_injured,
        total_points::double                                                                as total_points,
        avg_points::double                                                                  as avg_points,
        projected_total_points::double                                                      as projected_total_points,
        projected_avg_points::double                                                        as projected_avg_points,
        percent_owned::double                                                               as percent_owned,
        percent_started::double                                                             as percent_started,
        stats                                                                               as stats_raw
    from {{ source("s001", "players") }}
)
select *
from players_raw