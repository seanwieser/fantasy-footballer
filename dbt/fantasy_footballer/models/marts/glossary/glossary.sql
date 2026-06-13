select
    slug,
    term,
    category,
    short_def,
    full_def,
    related
from {{ ref("glossary_terms") }}
order by category, term
