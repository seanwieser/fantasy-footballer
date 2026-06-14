select
    reactions.reaction_uid,
    reactions.message_uid,
    reactions.reactor_owner_id,
    coalesce(reactor.owner_name, 'Unknown') as reactor_owner_name,
    reactions.reaction_type,
    reactions.year,
    messages.owner_id as message_owner_id,
    coalesce(author.owner_name, 'Unknown') as message_owner_name
from {{ ref("base_s003__reactions") }} as reactions
left join {{ ref("owner_names") }} as reactor
    on reactions.reactor_owner_id = reactor.owner_id
left join {{ ref("base_s003__messages") }} as messages
    on reactions.message_uid = messages.message_uid
left join {{ ref("owner_names") }} as author
    on messages.owner_id = author.owner_id
