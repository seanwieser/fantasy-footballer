select
    activity.year,
    activity.owner_name,
    activity.owner_id,
    activity.message_count,
    activity.avg_word_count,
    activity.attachment_count,
    activity.reactions_received,
    activity.reactions_given,
    activity.share_of_chat_pct
from {{ ref("int__owner_chat_activity") }} as activity
order by
    activity.year desc,
    activity.message_count desc
