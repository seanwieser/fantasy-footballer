with league_settings as (
    select
        year,
        reg_season_count,
        team_count
    from {{ ref("base_s001__settings") }}
),

-- Winners-bracket membership is data-driven (WINNERS_BRACKET participation), NOT seed-based:
-- in 2018 the league had two divisions (East/West, since removed) so `standing` is
-- division-aware (a 7-6 division winner outranks 9-4 teams) and != the playoff seed.
winners_participants as (
    select distinct team_year_id
    from {{ ref("base_s001__matchups") }}
    where matchup_type = 'WINNERS_BRACKET'
),

team_brackets as (
    select
        teams.team_id,
        teams.team_year_id,
        teams.year,
        teams.standing as seed,
        league_settings.reg_season_count,
        case
            when winners_participants.team_year_id is not null then 'winners'
            when teams.standing > league_settings.team_count - 4 then 'toilet_bowl'
            else 'kiss_my_sister'
        end as bracket
    from {{ ref("base_s001__teams") }} as teams
    inner join league_settings
        on teams.year = league_settings.year
    left join winners_participants
        on teams.team_year_id = winners_participants.team_year_id
),

postseason_weeks as (
    select
        team_weeks.team_year_id,
        team_weeks.team_week_id,
        team_weeks.year,
        team_weeks.week,
        team_weeks.week - team_brackets.reg_season_count as postseason_week_num,
        team_weeks.score_for,
        team_weeks.outcome,
        team_weeks.opponent_team_year_id,
        team_brackets.seed,
        team_brackets.bracket,
        matchups.matchup_type
    from {{ ref("stg__team_weeks") }} as team_weeks
    inner join team_brackets
        on team_weeks.team_year_id = team_brackets.team_year_id
    inner join {{ ref("stg__settings_matchup_weeks_map") }} as matchup_weeks_map
        on
            team_weeks.year = matchup_weeks_map.year and
            team_weeks.week = matchup_weeks_map.week
    inner join {{ ref("base_s001__matchups") }} as matchups
        on
            team_weeks.team_year_id = matchups.team_year_id and
            matchup_weeks_map.matchup_week = matchups.matchup_week
    where
        team_weeks.week > team_brackets.reg_season_count and
        team_weeks.outcome != 'U' -- excludes byes (top seeds skip round 1)
),

week_bounds as (
    select
        year,
        max(week) as last_postseason_week
    from postseason_weeks
    group by year
),

postseason_weeks_enriched as (
    select
        postseason_weeks.*,
        week_bounds.last_postseason_week,
        opponent_brackets.bracket as opponent_bracket
    from postseason_weeks
    inner join week_bounds
        on postseason_weeks.year = week_bounds.year
    left join team_brackets as opponent_brackets
        on postseason_weeks.opponent_team_year_id = opponent_brackets.team_year_id
),

-- The semifinal is the second-to-last postseason week. Its winners contest the championship
-- (1st/2nd) in the final week; its losers contest the 3rd-place game. Identifying placement
-- games by semifinal result is robust to the final week's matchup_type label, which differs
-- between the 2-week (4-team) and 3-week (6-team) formats.
semifinal_winners as (
    select team_year_id
    from postseason_weeks_enriched
    where
        matchup_type = 'WINNERS_BRACKET' and
        week = last_postseason_week - 1 and
        outcome = 'W'
),

semifinal_losers as (
    select team_year_id
    from postseason_weeks_enriched
    where
        matchup_type = 'WINNERS_BRACKET' and
        week = last_postseason_week - 1 and
        outcome = 'L'
),

flagged as (
    select
        team_year_id,
        team_week_id,
        year,
        week,
        postseason_week_num,
        seed,
        bracket,
        matchup_type,
        score_for,
        outcome,
        opponent_team_year_id,
        week = last_postseason_week and
        team_year_id in (select semifinal_winners.team_year_id from semifinal_winners) as is_championship_game,
        week = last_postseason_week and
        team_year_id in (select semifinal_losers.team_year_id from semifinal_losers) as is_third_place_game,
        bracket = 'toilet_bowl' and
        opponent_bracket = 'toilet_bowl' and
        postseason_week_num <= 2 as is_toilet_game
    from postseason_weeks_enriched
)

select
    team_year_id,
    team_week_id,
    year,
    week,
    postseason_week_num,
    seed,
    bracket,
    matchup_type,
    score_for,
    outcome,
    opponent_team_year_id,
    is_championship_game,
    is_third_place_game,
    is_toilet_game,
    matchup_type = 'WINNERS_BRACKET' or is_third_place_game or is_toilet_game as is_meaningful
from flagged
