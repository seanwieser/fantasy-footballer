with head_to_head as (
    select * from {{ ref("int__owner_head_to_head") }}
),

shaped as (
    select
        owner_opponent_id,
        owner_id,
        owner_name,
        opponent_owner_id,
        opponent_owner_name,
        total_meetings,
        longest_win_streak,
        held_under_100,
        lucky_wins,
        unlucky_losses,
        round(avg_points_for, 1)::varchar as avg_points,
        case when biggest_win_margin > 0 then biggest_win_context end as biggest_win,
        closest_context as closest_game,
        closest_leader as closest_game_leader,
        shootout_context as highest_shootout,
        shootout_leader as highest_shootout_leader,
        slugfest_context as lowest_slugfest,
        slugfest_leader as lowest_slugfest_leader,
        -- Symmetric rivalry facts: each value is owner-perspective (this row's owner first) + the
        -- owner_id of whoever leads it (null when even). The page reads the left owner's row, so the
        -- value already orders left-to-right by column, and the arrow points at the leader.
        reg_wins::varchar || '-' || reg_losses::varchar ||
        case when reg_ties > 0 then '-' || reg_ties::varchar else '' end ||
        ' (' || round((reg_wins + 0.5 * reg_ties) / reg_games * 100, 0)::bigint::varchar || '%)' as rivalry_record,
        case
            when reg_wins > reg_losses then owner_id
            when reg_losses > reg_wins then opponent_owner_id
        end as rivalry_record_leader,
        case
            when playoff_games = 0 then 'None'
            else playoff_wins::varchar || '-' || playoff_losses::varchar
        end as rivalry_playoff_record,
        case
            when playoff_wins > playoff_losses then owner_id
            when playoff_losses > playoff_wins then opponent_owner_id
        end as rivalry_playoff_record_leader,
        round(total_points_for, 0)::bigint::varchar || '-' || round(total_points_against, 0)::bigint::varchar ||
        case when total_points_for - total_points_against >= 0 then ' (+' else ' (' end ||
        round(total_points_for - total_points_against, 0)::bigint::varchar || ')' as rivalry_points,
        case
            when total_points_for > total_points_against then owner_id
            when total_points_against > total_points_for then opponent_owner_id
        end as rivalry_points_leader,
        case
            when avg_margin = 0 then 'Even'
            when avg_margin > 0 then '+' || round(avg_margin, 1)::varchar
            else round(avg_margin, 1)::varchar
        end as rivalry_avg_margin,
        case
            when avg_margin > 0 then owner_id
            when avg_margin < 0 then opponent_owner_id
        end as rivalry_avg_margin_leader,
        case current_outcome
            when 'W' then 'W' || current_streak::varchar
            when 'L' then 'L' || current_streak::varchar
            else 'Tied'
        end as rivalry_streak,
        case
            when current_outcome = 'W' then owner_id
            when current_outcome = 'L' then opponent_owner_id
        end as rivalry_streak_leader,
        last_meeting_context as rivalry_last_meeting,
        case
            when current_outcome = 'W' then owner_id
            when current_outcome = 'L' then opponent_owner_id
        end as rivalry_last_meeting_leader,
        case
            when clutch_wins = 0 and clutch_losses = 0 then 'None'
            else clutch_wins::varchar || '-' || clutch_losses::varchar
        end as rivalry_clutch,
        case
            when clutch_wins > clutch_losses then owner_id
            when clutch_losses > clutch_wins then opponent_owner_id
        end as rivalry_clutch_leader
    from head_to_head
)

select * from shaped
