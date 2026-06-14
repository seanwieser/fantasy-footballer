select
    message_uid::varchar as message_uid,
    owner_id::int as owner_id,
    sent_at::timestamp as sent_at,
    year::int as year,
    "text"::varchar as message_text,
    word_count::int as word_count,
    char_count::int as char_count,
    has_attachment::boolean as has_attachment,
    attachment_count::int as attachment_count,
    service::varchar as service,
    thread_name::varchar as thread_name,
    meta__source_path::varchar as meta__source_path,
    meta__date_effective::date as meta__date_effective,
    meta__date_pulled::date as meta__date_pulled
from {{ source("s003", "messages") }}
qualify row_number() over (partition by message_uid order by meta__date_effective desc) = 1
