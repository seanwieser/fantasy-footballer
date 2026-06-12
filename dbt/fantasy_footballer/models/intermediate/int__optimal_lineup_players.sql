-- Per team-(NFL week)-player (regular season + meaningful postseason games): whether the player was
-- actually started and whether they belong in the best legal lineup that NFL week (the optimal), plus
-- the slot each lineup puts them in. The optimal greedily fills dedicated slots with the top scorers
-- per position, then FLEX with the best remaining RB/WR/TE.
--
-- Rosters arrive per NFL week from stg__team_week_players (the 2018-2019 two-week playoff matchups
-- carry a lineup per NFL week), so points pair 1:1 with stg__player_weeks on player_week_id. is_playoff
-- is resolved on the matchup week; those rows are excluded from the season aggregate (int__optimal_lineups)
-- but surfaced per week by the owner-spotlight Roster view.
with meaningful_postseason as (
    select distinct
        team_year_id,
        week as matchup_week
    from {{ ref("int__postseason_team_weeks") }}
    where is_meaningful
),

matchup_playoff as (
    select distinct
        year,
        matchup_week,
        is_playoff
    from {{ ref("int__matchup_week_playoff_map") }}
),

roster_base as (
    select
        team_week_players.team_year_id,
        team_week_players.team_week_id,
        team_week_players.player_week_id,
        team_week_players.player_id,
        players.player_name,
        team_week_players.year,
        team_week_players.matchup_week,
        team_week_players.week,
        matchup_playoff.is_playoff,
        team_week_players.lineup_slot,
        team_week_players.lineup_slot not in ('BE', 'IR') as is_started,
        players.position_slot as position,
        players.position_slot in ('RB', 'WR', 'TE') as flex_eligible,
        coalesce(player_weeks.points, 0) as points
    from {{ ref("stg__team_week_players") }} as team_week_players
    inner join matchup_playoff
        on
            team_week_players.year = matchup_playoff.year and
            team_week_players.matchup_week = matchup_playoff.matchup_week
    inner join {{ ref("base_s001__players") }} as players
        on team_week_players.player_year_id = players.player_year_id
    left join {{ ref("stg__player_weeks") }} as player_weeks
        on team_week_players.player_week_id = player_weeks.player_week_id
    left join meaningful_postseason
        on
            team_week_players.team_year_id = meaningful_postseason.team_year_id and
            team_week_players.matchup_week = meaningful_postseason.matchup_week
    -- Regular-season weeks always; postseason weeks only for meaningful bracket games (an eliminated
    -- team's locked roster in the weeks after is dropped).
    where not matchup_playoff.is_playoff or meaningful_postseason.matchup_week is not null
),

-- Slot needs + optimal ranking are computed per NFL week (team_week_id is NFL-week-grained).
slot_requirements as (
    select
        team_week_id,
        count_if(lineup_slot = 'QB') as n_qb,
        count_if(lineup_slot = 'RB') as n_rb,
        count_if(lineup_slot = 'WR') as n_wr,
        count_if(lineup_slot = 'TE') as n_te,
        count_if(lineup_slot = 'K') as n_k,
        count_if(lineup_slot = 'D/ST') as n_dst,
        count_if(lineup_slot = 'FLEX') as n_flex
    from roster_base
    where is_started
    group by team_week_id
),

ranked_by_position as (
    select
        roster_base.*,
        row_number() over (
            partition by roster_base.team_week_id, roster_base.position
            order by roster_base.points desc
        ) as position_rank
    from roster_base
),

dedicated_flagged as (
    select
        ranked_by_position.*,
        slot_requirements.n_flex,
        ranked_by_position.position_rank <= (
            case ranked_by_position.position
                when 'QB' then slot_requirements.n_qb
                when 'RB' then slot_requirements.n_rb
                when 'WR' then slot_requirements.n_wr
                when 'TE' then slot_requirements.n_te
                when 'K' then slot_requirements.n_k
                when 'D/ST' then slot_requirements.n_dst
                else 0
            end
        ) as is_dedicated
    from ranked_by_position
    inner join slot_requirements
        on ranked_by_position.team_week_id = slot_requirements.team_week_id
),

flex_candidates as (
    select
        dedicated_flagged.*,
        case
            when dedicated_flagged.flex_eligible and not dedicated_flagged.is_dedicated
                then dedicated_flagged.points
        end as flex_candidate_points
    from dedicated_flagged
),

flex_ranked as (
    select
        flex_candidates.*,
        row_number() over (
            partition by flex_candidates.team_week_id
            order by flex_candidates.flex_candidate_points desc nulls last
        ) as flex_rank
    from flex_candidates
),

flagged as (
    select
        team_year_id,
        team_week_id,
        player_week_id,
        player_id,
        player_name,
        year,
        matchup_week,
        week,
        is_playoff,
        position,
        points,
        is_started,
        lineup_slot,
        is_dedicated,
        flex_eligible and not is_dedicated and flex_rank <= n_flex as is_flex_pick
    from flex_ranked
)

select
    team_year_id,
    team_week_id,
    player_week_id,
    player_id,
    player_name,
    year,
    matchup_week,
    week,
    is_playoff,
    position,
    points,
    is_started,
    is_dedicated or is_flex_pick as is_optimal,
    lineup_slot as actual_slot,
    case
        when is_dedicated then position
        when is_flex_pick then 'FLEX'
    end as optimal_slot
from flagged
