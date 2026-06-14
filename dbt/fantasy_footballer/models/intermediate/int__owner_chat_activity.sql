with messages as (
    select
        owner_id,
        owner_name,
        year,
        count(*) as message_count,
        sum(word_count) as total_words,
        round(avg(word_count), 1) as avg_word_count,
        sum(attachment_count) as attachment_count,
        count(distinct date_trunc('week', sent_at)) as active_weeks
    from {{ ref("stg__chat_messages") }}
    where owner_id >= 0
    group by owner_id, owner_name, year
),

reactions_received as (
    select
        message_owner_id as owner_id,
        year,
        count(*) as reactions_received
    from {{ ref("stg__chat_reactions") }}
    where message_owner_id >= 0
    group by message_owner_id, year
),

reactions_given as (
    select
        reactor_owner_id as owner_id,
        year,
        count(*) as reactions_given
    from {{ ref("stg__chat_reactions") }}
    where reactor_owner_id >= 0
    group by reactor_owner_id, year
),

year_totals as (
    select
        year,
        sum(message_count) as year_message_total
    from messages
    group by year
)

select
    messages.owner_id,
    messages.owner_name,
    messages.year,
    messages.message_count::bigint as message_count,
    messages.total_words::bigint as total_words,
    messages.avg_word_count::double as avg_word_count,
    messages.attachment_count::bigint as attachment_count,
    messages.active_weeks::bigint as active_weeks,
    coalesce(reactions_received.reactions_received, 0)::bigint as reactions_received,
    coalesce(reactions_given.reactions_given, 0)::bigint as reactions_given,
    round(100.0 * messages.message_count / nullif(year_totals.year_message_total, 0), 1)::double
        as share_of_chat_pct
from messages
left join reactions_received
    on messages.owner_id = reactions_received.owner_id and messages.year = reactions_received.year
left join reactions_given
    on messages.owner_id = reactions_given.owner_id and messages.year = reactions_given.year
left join year_totals
    on messages.year = year_totals.year
