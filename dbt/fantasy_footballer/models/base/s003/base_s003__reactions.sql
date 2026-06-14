select
    reaction_uid::varchar as reaction_uid,
    message_uid::varchar as message_uid,
    reactor_owner_id::int as reactor_owner_id,
    reaction_type::varchar as reaction_type,
    year::int as year,
    meta__source_path::varchar as meta__source_path,
    meta__date_effective::date as meta__date_effective,
    meta__date_pulled::date as meta__date_pulled
from {{ source("s003", "reactions") }}
qualify row_number() over (partition by reaction_uid order by meta__date_effective desc) = 1
