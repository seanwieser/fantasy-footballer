select
    messages.message_uid,
    messages.owner_id,
    coalesce(owner_names.owner_name, 'Unknown') as owner_name,
    messages.sent_at,
    messages.year,
    messages.word_count,
    messages.char_count,
    messages.has_attachment,
    messages.attachment_count,
    messages.service
from {{ ref("base_s003__messages") }} as messages
left join {{ ref("owner_names") }} as owner_names
    on messages.owner_id = owner_names.owner_id
