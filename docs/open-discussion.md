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
  canonical term and the derived names (*Shotgun title*, *Sober season*) land.

**Open until:** the league ratifies a naming convention; then update the seed labels in one pass.

---

## OD-002 — Scoring metric to feature: total vs points-per-game

**Question:** for season-scoring highlights, do we headline **total** regular-season points, **points
per game (PPG)**, or keep surfacing **both**? Currently we keep both (`int__owner_season_scoring`
carries `reg_points_total` and `reg_points_per_game`, and the highlights show both).

**Why it's a discussion, not a task:** neither compares like-for-like *across* seasons, so it's a
judgment call about what's "fairest," not a bug. Season length varies (13 games in 2018–2019 vs 14
from 2021 on) **and** the active matchup roster size has changed over the years, so a season can score
more *per game* regardless of length. Within a season the two rank owners identically (everyone plays
the same games) — they only diverge across years.

**Decision so far:** deferred indefinitely, keep BOTH until we find a normalization that accounts for
*both* season length and roster-size drift. For reference, the two crown different record-holders: by
total, #1 = Aditya 2023 (2052.8); by PPG, #1 = Casey Magid 2018 (155.24).

**Open until:** we either adopt a normalization that makes one canonical, or the league decides which to
feature; then drop or de-emphasize the other in the highlights.

---

## OD-003 — League review of the Head-to-Head dashboard metrics

**Question:** the H2H Dashboard (`/stats_center/h2h_dashboard`) ships a first cut of pairwise rivalry
metrics — **The Rivalry** (series record, playoff record, points + differential, avg margin, current
streak, last meeting, clutch record, highest score, toughest beat, closest game, highest shootout,
lowest slugfest) and per-owner **Head to Head** (avg score, longest win streak, biggest win, held
under 100). Put it in front of the league: which metrics earn their spot, which are noise, what's
missing, and are the labels/tooltips clear? (Earlier idea-batches surfaced more candidates than we
shipped — e.g. *first meeting*, *avg combined score*.)

**Why it's a discussion, not a task:** what makes a rivalry stat *fun* is a group taste call, not a
technical one — better to gather league reactions in one pass than to keep adding/cutting rows solo.

**Where the rows live (so a decision is a quick change):** the **`h2h_rivalry_metrics` seed**
(`dbt/fantasy_footballer/seeds/h2h_rivalry_metrics.csv`) drives the two pairwise sections — adding,
removing, relabelling, retooltipping, or reordering a row is a one-line seed edit (+ a mart column +
`int__owner_head_to_head` computation for genuinely new stats). Career-comparison rows are the separate
`h2h_metrics` seed (see OD-001 for naming).

**Open until:** the league gives feedback on which rivalry metrics to keep / cut / add; then update the
seed (and marts for any new stats) in one pass.
