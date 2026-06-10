-- int__owner_head_to_head summed across every opponent must reproduce each owner's regular-season
-- W-L-T as recorded by ESPN on base_s001__teams. The H2H career record is built solely from the
-- pairwise rivalry rows, so this anchors that derived record back to the raw source — a mismatch means
-- a meeting was double-counted or dropped, or an owner-season went unmapped.
with h2h as (
    select
        owner_id,
        sum(reg_wins) as wins,
        sum(reg_losses) as losses,
        sum(reg_ties) as ties
    from {{ ref("int__owner_head_to_head") }}
    group by owner_id
),

source as (
    select
        owner_map.owner_id,
        sum(teams.wins) as wins,
        sum(teams.losses) as losses,
        sum(teams.ties) as ties
    from {{ ref("base_s001__teams") }} as teams
    inner join {{ ref("int__owner_team_year_map") }} as owner_map
        on teams.team_year_id = owner_map.team_year_id
    group by owner_map.owner_id
)

select
    h2h.owner_id,
    h2h.wins as h2h_wins,
    source.wins as source_wins,
    h2h.losses as h2h_losses,
    source.losses as source_losses,
    h2h.ties as h2h_ties,
    source.ties as source_ties
from h2h
inner join source on h2h.owner_id = source.owner_id
where
    h2h.wins != source.wins or
    h2h.losses != source.losses or
    h2h.ties != source.ties
