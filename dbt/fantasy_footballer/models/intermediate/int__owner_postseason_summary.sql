with team_postseason as (
    select * from {{ ref("int__team_postseason") }}
),

owner_map as (
    select * from {{ ref("int__owner_team_year_map") }}
),

postseason_weeks as (
    select * from {{ ref("int__postseason_team_weeks") }}
),

owner_postseason as (
    select
        owner_map.owner_id,
        max(owner_map.owner_name) as owner_name,
        count_if(team_postseason.made_playoffs)::int as playoff_appearances,
        count_if(team_postseason.is_champion)::int as championships,
        count_if(team_postseason.is_runner_up)::int as runner_ups,
        count_if(team_postseason.is_third)::int as third_places,
        count_if(team_postseason.bracket = 'toilet_bowl')::int as toilet_bowl_appearances,
        -- Dead last (12th): the team that "wins" the toilet bowl.
        count_if(team_postseason.is_last)::int as last_place_finishes,
        count_if(team_postseason.is_second_to_last)::int as second_to_last_finishes,
        min(team_postseason.final_standing)::int as best_finish
    from team_postseason
    inner join owner_map
        on team_postseason.team_year_id = owner_map.team_year_id
    group by owner_map.owner_id
),

-- Game-level records across meaningful postseason games, kept SEPARATE by bracket: the championship
-- (winners) bracket is the true "playoff record" and reconciles with playoff_appearances; the toilet
-- bowl is its own thing (you reach it by missing the playoffs). Both exclude filler/middle games.
owner_playoff_games as (
    select
        owner_map.owner_id,
        count_if(
            postseason_weeks.is_meaningful and postseason_weeks.bracket = 'winners' and
            postseason_weeks.outcome = 'W'
        )::int as playoff_wins,
        count_if(
            postseason_weeks.is_meaningful and postseason_weeks.bracket = 'winners' and
            postseason_weeks.outcome = 'L'
        )::int as playoff_losses,
        count_if(
            postseason_weeks.is_meaningful and postseason_weeks.bracket = 'toilet_bowl' and
            postseason_weeks.outcome = 'W'
        )::int as toilet_bowl_wins,
        count_if(
            postseason_weeks.is_meaningful and postseason_weeks.bracket = 'toilet_bowl' and
            postseason_weeks.outcome = 'L'
        )::int as toilet_bowl_losses
    from postseason_weeks
    inner join owner_map
        on postseason_weeks.team_year_id = owner_map.team_year_id
    group by owner_map.owner_id
)

select
    owner_postseason.*,
    coalesce(owner_playoff_games.playoff_wins, 0)::int as playoff_wins,
    coalesce(owner_playoff_games.playoff_losses, 0)::int as playoff_losses,
    coalesce(owner_playoff_games.toilet_bowl_wins, 0)::int as toilet_bowl_wins,
    coalesce(owner_playoff_games.toilet_bowl_losses, 0)::int as toilet_bowl_losses
from owner_postseason
left join owner_playoff_games
    on owner_postseason.owner_id = owner_playoff_games.owner_id
