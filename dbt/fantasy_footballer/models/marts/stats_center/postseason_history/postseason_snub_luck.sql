with titles as (
    select
        year,
        owner_id,
        owner_name,
        is_snubbed,
        is_lucked_in,
        playoff_teams_outscored,
        nonplayoff_teams_outscoring
    from {{ ref("int__season_titles") }}
),

-- Snub = missed the playoffs despite outscoring >= 1 playoff team (the platform-canonical snub from
-- int__season_titles, same as League Highlights / H2H). Lucky-in = its mirror: made the playoffs
-- despite being outscored by >= 1 non-playoff team.
snubs as (
    select
        year,
        owner_id,
        owner_name,
        'snub' as kind,
        playoff_teams_outscored as context_count,
        'Outscored ' || playoff_teams_outscored::varchar
        || ' who made it' as detail
    from titles
    where is_snubbed
),

lucked_in as (
    select
        year,
        owner_id,
        owner_name,
        'lucky_in' as kind,
        nonplayoff_teams_outscoring as context_count,
        'Snuck in over ' || nonplayoff_teams_outscoring::varchar
        || ' who outscored them' as detail
    from titles
    where is_lucked_in
)

select
    year,
    owner_id,
    owner_name,
    kind,
    context_count::int as context_count,
    detail
from (
    select * from snubs
    union all
    select * from lucked_in
)
order by year desc, kind, context_count desc, owner_name
