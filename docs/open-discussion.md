# Open Discussion Items

Open questions and decisions to talk through — often **with the league** — before they become
concrete work. Distinct from the [feature backlog](feature-backlog.md) (things to *build*) and the
[architecture roadmap](architecture-roadmap.md) (technical direction): these have **no settled answer
yet**. When one is resolved, it either graduates into the backlog or is just decided and removed here.

Each item has an **`OD-XXX`** id (zero-padded, assigned in order, never reused) for easy reference.

---

## OD-001 — Formalize highlight names / league slang

**Question:** the League Highlights metrics currently use working names — some playful, some literal —
that aren't yet the league's *agreed* vocabulary. Pin down canonical names with the league so the
slang is consistent and feels owned.

**Why it's a discussion, not a task:** naming is a group/culture call, not a technical one. Better to
settle the vocabulary once with the league than to keep churning labels solo.

**Where the names live (so a decision is a quick change):** the `metric_label` column of the seed
catalogs — `dbt/fantasy_footballer/seeds/all_time_record_metrics.csv` and
`season_highlight_metrics.csv`. Each rename is a one-cell edit + `dbt build` (no schema change). Keep
the All-Time (plural, "… titles") and By-Season (singular, "… title") labels consistent for the same
concept.

**Names in flux / worth ratifying:**
- **Bottom-scorer title** — current pick for fewest season points (was "Wooden-spoon"; other candidates
  floated: *Sacko*, *Toilet Bowl*, *Cellar-dweller*, *Lowest-scoring*).
- **Snub** (most points but missed playoffs) / **Lucky-in** (made playoffs on fewest points).
- **Clutch** (games decided by < 10) — *Clutch-winning* / *Clutch-losing*.
- **Lucky-winner** / **Unlucky-loser** (won below / lost above the week's league median).
- **Shotgun** (week under 100 pts or the week's league low) — already league slang; confirm it's the
  canonical term and the derived names (*Shotgun title*, *Clean season*) land.

**Open until:** the league ratifies a naming convention; then update the seed labels in one pass.
