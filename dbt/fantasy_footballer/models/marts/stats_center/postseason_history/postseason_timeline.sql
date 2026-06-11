with postseason as (
    select * from {{ ref("int__team_postseason") }}
),

owner_map as (
    select
        team_year_id,
        owner_id,
        owner_name
    from {{ ref("int__owner_team_year_map") }}
),

finishers as (
    select
        postseason.year,
        owner_map.owner_id,
        owner_map.owner_name,
        postseason.seed,
        postseason.is_champion,
        postseason.is_runner_up,
        postseason.is_third,
        postseason.is_last
    from postseason
    inner join owner_map
        on postseason.team_year_id = owner_map.team_year_id
)

-- One row per season: the four headline finishers (champion, runner-up, 3rd, toilet-bowl loser),
-- each with the owner's regular-season seed so the page can frame the upset/collapse factor.
-- Exactly one team carries each placement flag per year, so the filtered aggregates pick a single value.
select
    year,
    max(owner_id) filter (where is_champion)::int as champion_owner_id,
    max(owner_name) filter (where is_champion) as champion_owner_name,
    max(seed) filter (where is_champion)::int as champion_seed,
    max(owner_id) filter (where is_runner_up)::int as runner_up_owner_id,
    max(owner_name) filter (where is_runner_up) as runner_up_owner_name,
    max(seed) filter (where is_runner_up)::int as runner_up_seed,
    max(owner_id) filter (where is_third)::int as third_owner_id,
    max(owner_name) filter (where is_third) as third_owner_name,
    max(seed) filter (where is_third)::int as third_seed,
    max(owner_id) filter (where is_last)::int as toilet_owner_id,
    max(owner_name) filter (where is_last) as toilet_owner_name,
    max(seed) filter (where is_last)::int as toilet_seed
from finishers
group by year
order by year desc
