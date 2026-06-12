with postseason_weeks as (
    select * from {{ ref("int__postseason_team_weeks") }}
),

owner_map as (
    select
        team_year_id,
        owner_id,
        owner_name
    from {{ ref("int__owner_team_year_map") }}
),

-- The games that make up the bracket view: the full winners ladder plus the 3rd-place game and the
-- toilet-bowl final (is_meaningful). Pure kiss-my-sister consolation games are excluded.
meaningful_rows as (
    select
        postseason_weeks.team_year_id,
        postseason_weeks.year,
        postseason_weeks.week,
        postseason_weeks.postseason_week_num,
        postseason_weeks.seed,
        postseason_weeks.bracket,
        postseason_weeks.score_for,
        postseason_weeks.outcome,
        postseason_weeks.opponent_team_year_id,
        postseason_weeks.is_championship_game,
        postseason_weeks.is_third_place_game,
        postseason_weeks.is_toilet_game,
        owner_map.owner_id,
        owner_map.owner_name
    from postseason_weeks
    inner join owner_map
        on postseason_weeks.team_year_id = owner_map.team_year_id
    where postseason_weeks.is_meaningful
),

-- The last round of each bracket per season (winners = championship round, toilet = dead-last
-- decider). Rounds are labelled relative to it, so the 2-round (4-team) and 3-round (6-team) eras
-- both work without hard-coded weeks.
final_round as (
    select
        year,
        bracket,
        max(postseason_week_num) as last_round
    from meaningful_rows
    group by year, bracket
),

-- Collapse the two team-perspective rows of each game into one matchup row, anchored on the better
-- (lower-numbered) seed. Seeds are unique within a season, so the inequality dedupes cleanly.
games as (
    select
        top_row.year,
        top_row.bracket,
        top_row.postseason_week_num as round_num,
        top_row.is_championship_game,
        top_row.is_third_place_game,
        top_row.is_toilet_game,
        top_row.owner_id as top_seed_owner_id,
        top_row.owner_name as top_seed_owner_name,
        top_row.seed as top_seed,
        top_row.score_for as top_seed_score,
        low_row.owner_id as low_seed_owner_id,
        low_row.owner_name as low_seed_owner_name,
        low_row.seed as low_seed,
        low_row.score_for as low_seed_score,
        case
            when top_row.outcome = 'W' then top_row.owner_id
            when top_row.outcome = 'L' then low_row.owner_id
        end as winner_owner_id,
        case
            when top_row.outcome = 'W' then top_row.owner_name
            when top_row.outcome = 'L' then low_row.owner_name
        end as winner_owner_name,
        false as is_bye
    from meaningful_rows as top_row
    inner join meaningful_rows as low_row
        on
            top_row.opponent_team_year_id = low_row.team_year_id and
            top_row.year = low_row.year and
            top_row.week = low_row.week
    where top_row.seed < low_row.seed
),

-- Winners-bracket teams that sat out round 1 (the top seeds' first-round bye). Data-derived rather
-- than seed-assumed: a bye is simply a winners team with no round-1 game. Empty for the 4-team era.
round1_winners as (
    select distinct team_year_id
    from postseason_weeks
    where bracket = 'winners' and postseason_week_num = 1
),

winners_teams as (
    select distinct
        team_year_id,
        year,
        seed,
        owner_id,
        owner_name
    from meaningful_rows
    where bracket = 'winners'
),

byes as (
    select
        winners_teams.year,
        'winners' as bracket,
        1 as round_num,
        false as is_championship_game,
        false as is_third_place_game,
        false as is_toilet_game,
        winners_teams.owner_id as top_seed_owner_id,
        winners_teams.owner_name as top_seed_owner_name,
        winners_teams.seed as top_seed,
        null::double as top_seed_score,
        null::int as low_seed_owner_id,
        null::varchar as low_seed_owner_name,
        null::int as low_seed,
        null::double as low_seed_score,
        winners_teams.owner_id as winner_owner_id,
        winners_teams.owner_name as winner_owner_name,
        true as is_bye
    from winners_teams
    left join round1_winners
        on winners_teams.team_year_id = round1_winners.team_year_id
    where round1_winners.team_year_id is null
),

slots as (
    select * from games
    union all
    select * from byes
)

select
    slots.year,
    slots.bracket,
    slots.round_num::int as round_num,
    case
        when slots.is_championship_game then 'Championship'
        when slots.is_third_place_game then '3rd Place Game'
        when slots.bracket = 'toilet_bowl'
            then if(slots.round_num = final_round.last_round, 'Toilet Bowl', 'First Round')
        when slots.round_num = final_round.last_round - 1 then 'Semifinal'
        when slots.round_num = final_round.last_round - 2 then 'First Round'
        else 'Postseason'
    end as round_label,
    slots.is_championship_game,
    slots.is_third_place_game,
    slots.is_toilet_game,
    slots.is_bye,
    slots.top_seed_owner_id::int as top_seed_owner_id,
    slots.top_seed_owner_name,
    slots.top_seed::int as top_seed,
    round(slots.top_seed_score, 2) as top_seed_score,
    slots.low_seed_owner_id::int as low_seed_owner_id,
    slots.low_seed_owner_name,
    slots.low_seed::int as low_seed,
    round(slots.low_seed_score, 2) as low_seed_score,
    slots.winner_owner_id::int as winner_owner_id,
    slots.winner_owner_name,
    -- Who advances: the game winner in the winners bracket, but the LOSER in the toilet bowl (you
    -- advance by losing, toward dead last). Drives the bracket highlight. Null on a tie.
    case
        when slots.winner_owner_id is null then null
        when slots.bracket = 'toilet_bowl' and slots.winner_owner_id = slots.top_seed_owner_id
            then slots.low_seed_owner_id
        when slots.bracket = 'toilet_bowl'
            then slots.top_seed_owner_id
        else slots.winner_owner_id
    end::int as advancer_owner_id
from slots
inner join final_round
    on
        slots.year = final_round.year and
        slots.bracket = final_round.bracket
order by slots.year desc, slots.bracket asc, slots.round_num asc, slots.top_seed asc
