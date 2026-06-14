# Feature Backlog

Future features we've discussed but not built yet. Lightweight notes — enough to pick the
thread back up later, not full specs. Architecture-level direction lives in
[`architecture-roadmap.md`](architecture-roadmap.md).

Each item has an **`FF-XXX`** id (zero-padded, assigned in order, never reused) so we can
reference it in conversation, branches, and commits.

**Fields** (kept deliberately small — a field only exists if it changes what to do next):
- **Area** — `frontend` / `backend` / `dbt` / `api` / `infra` / `security` / `docs` (multi-valued).
- **Priority** — `Low` / `Med` / `High` (rough; read together with Effort, not alone).
- **Effort** — `S` (< ½ day) / `M` (a day or two) / `L` (multi-day).
- **Status** — `Idea` / `Ready` / `Doing` / `Done` (archive `Done` to the bottom).
- **Done when** — a one-line definition of done, on each item.

## Index

| ID | Title | Area | Priority | Effort | Status |
|----|-------|------|----------|--------|--------|
| FF-001 | Owner-uploaded headshots | frontend, backend | Low | M | Idea |
| FF-002 | Revise sensitive-seed security | security, infra | Low | S–M | Done |
| FF-003 | Ingest s002 (FantasyData) source | backend, dbt | Low | L | Doing |
| FF-004 | One-command fly.io deploy | infra | Med | M | Idea |
| FF-005 | Fix source-fetch memory crash | backend | Low | M | Idea |
| FF-006 | Owner-attributed Roster Production (reframed) | frontend, dbt | Low | M | Done |
| FF-007 | Gallery: video upload / display / metadata | frontend, backend | Low | L | Idea |
| FF-008 | Refactor website navigation | frontend | Low | M | Done |
| FF-009 | Quantify luck via all-play / expected wins | dbt, frontend | Low | L | Done |
| FF-010 | Notification / events dashboard | dbt, backend, frontend | Low | L | Idea |
| FF-011 | Unify "league single best/worst week" logic | dbt | Low | S | Done |
| FF-012 | H2H Dashboard | dbt, frontend | Med | M | Done |
| FF-013 | Shootout / Slugfest records in League Highlights | dbt | Low | S | Done |
| FF-014 | Postseason history page | frontend, dbt | Med | M | Done |
| FF-015 | iMessage group-chat data pipeline + analytics | backend, dbt, frontend | Low | L | Done |
| FF-016 | Revise pre-Claude-Code pages/dbt/backend | frontend, dbt, backend | Med | L | Done |
| FF-017 | Roster-picker value: acquisition cost vs utilized points | dbt, frontend | Med | L | Idea |
| FF-018 | Player spotlight pages + player-centric highlights | frontend, dbt | Med | L | Idea |
| FF-019 | Glossary page + glossary as the relational concept dimension | frontend, dbt | Med | M | Done |
| FF-020 | Group-chat (s003) analytics: titles, mood, cross-source metrics | dbt, frontend, backend | Med | L | Idea |

---

## FF-001 — Owner-uploaded headshots (replace thumbnail)

**Area:** frontend, backend · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** an owner can upload an image that replaces their headshot everywhere, stored
compressed in B2 and surviving a container restart.

**What:** let an owner upload their own image to replace their headshot, instead of the
headshots being a fixed set fetched from B2 at boot.

**Why now-ish:** today headshots are static files (`resources/media/owners/<owner_id>.jpg`)
pulled from B2 by `fetch_resources` and served straight off local disk. Self-service uploads
make the gallery/owner pages feel personal without a maintainer round-trip.

**Pieces it will need:**
- An **upload UI** (likely on the owner's spotlight/gallery page, auth-gated to that owner /
  admin) — NiceGUI `ui.upload`.
- **Storage**: write the uploaded image to B2 (the source of truth), keyed by `owner_id`, so
  it survives container restarts and is picked up by `fetch_resources` on next boot. Decide
  whether to also hot-update the local copy so the change shows immediately.
- **Pre-resize / compress (required as part of this feature):** never store the raw upload at
  full size. On upload, downscale to the display size and compress (e.g. ~128px WebP, ~5–15 KB)
  before writing to B2 — see the headshot sizing discussion in `architecture-roadmap.md`. This
  is the same optimization we'd want even for the current static headshots (they're currently
  211 KB rendered at ~52 px), so doing it here solves both.
- **Validation**: file type/size limits, strip EXIF, enforce square aspect (or center-crop).

**Open questions:** who can change whose image (self-only vs admin override); keep a default
fallback image for owners who never upload; whether to version/overwrite.

---

## FF-003 — Ingest s002 (FantasyData) source

**Area:** backend, dbt · **Priority:** Low · **Effort:** L · **Status:** Doing

**Done when:** FantasyData's free prior-year data is in B2 (same partitions as `s001`) and staging
dbt models expose it to downstream models via the existing ids.

**What:** add FantasyData as source `s002`. It's a paid DaaS but the previous year is free — upload
that data to B2 directly (no extractor, to avoid cost) and build staging models so downstream models
can use it. Relevant: <https://fantasydata.com/>.

_Source: GH #12 (in progress)._

---

## FF-004 — One-command fly.io deploy

**Area:** infra · **Priority:** Med · **Effort:** M · **Status:** Idea

**Done when:** a single `make` target builds the container and pushes it to fly.io, after basic
production protection (on `main`, up-to-date).

**What:** a deploy script wrapped in a `make` command that (1) checks the branch is `main` and
up-to-date, (2) builds the docker container, (3) pushes it to fly.io. The roadmap favors staying
local for now (see `architecture-roadmap.md`), but having one-command deploy ready de-risks the
eventual cutover.

_Source: GH #18._

---

## FF-005 — Fix source-fetch memory crash

**Area:** backend · **Priority:** Low · **Effort:** M · **Status:** Idea

**Done when:** fetching any source for any year range completes without OOM (`Error 137`).

**What:** fetching `s001: players` (the largest source) for multiple years crashes the container —
an out-of-memory issue from transforming in-memory before writing to B2. Stream/chunk the transform
so it doesn't hold everything in memory.

_Source: GH #11 (bug)._

---

## FF-007 — Gallery: video upload / display / metadata (Bunny Stream)

**Area:** frontend, backend · **Priority:** Low · **Effort:** L · **Status:** Idea

**Done when:** the Gallery page lets users upload videos to Bunny Stream with metadata, browse them
organized by owner and season, and edit a video's metadata after upload.

**What:** build out the `/gallery` page (currently a "Coming Soon" stub) into a video gallery backed
by Bunny Stream. Sub-pieces (were separate GH issues):
- **Upload** — frontend upload UI + put video to Bunny Stream via the TUS resumable client (no Stream
  endpoint in the bunny SDK). _GH #5._
- **Display** — organize videos by owner and season; link from Splash shotgun counter, Owner History
  spotlight, League Highlights, etc. Stretch: simple thumbs up/down voting. _GH #6._
- **Edit metadata** — an "Edit" button per video calling the TUS/Bunny update API to correct metadata
  after upload. _GH #8._
- **Auto-source from the group chat (s003)** — most shotgun videos are dropped into the iMessage group
  chat, so the FF-015 extract could feed them straight into Bunny Stream instead of a manual upload. The
  extract currently runs `imessage-exporter -c disabled` (no attachments); switching the copy-method to
  `-c clone` (copies originals as-is, e.g. `.MOV`) or `-c full` (also converts `.MOV`→`.MP4`, needs
  ffmpeg) writes every group-chat photo/video into the export's `attachments/` folder. Bunny Stream
  transcodes on ingest, so `-c clone` likely suffices (avoids a local ffmpeg dependency + conversion
  time). Open piece: classifying which attachments are shotgun videos vs. random memes before
  auto-uploading. Related: FF-015 (the extract), FF-020 (s003 analytics).

_Source: GH #7 (parent), #5, #6, #8; s003 auto-source added after the FF-015 pipeline landed._

---

## FF-010 — Notification / events dashboard (consolidated event feed)

**Area:** dbt, backend, frontend · **Priority:** Low · **Effort:** L · **Status:** Idea

**Done when:** there's a single consolidated **events feed** capturing notable things happening across
the site — at minimum new League-Highlights events and all-time-leaderboard rank changes — in one
queryable place that downstream products can source.

**What:** build a unified stream of "what's going on" across the website, so any number of products can
read from one consolidated event layer instead of each re-deriving "what changed." The dashboard /
consumer surface is undecided on purpose — the value here is the **event-sourcing layer underneath it**.

**First events to emit (League Highlights):**
- A **new highlight event** occurs — e.g. a fresh shotgun, clutch game, best/worst week, a new title
  holder (the same week-grain events we just chip on the spotlight schedule + the season titles).
- An **all-time leaderboard change** — someone enters/moves on an `all_time_records` leaderboard (rank
  change in the All-Time view), e.g. a new career-points leader or a new biggest snub.

**Why build it as a shared layer:** "consolidate the events once, source them many times." Candidate
consumers (none committed yet):
- a **Current Events / activity-feed page** in the app;
- an **iMessage (or GroupMe — see the dormant `groupme/` puller) push hook** to alert the league;
- **context for an LLM-generated news/recap report** (feed the event list to a model → weekly writeup).

**The hard part — detecting "new":** the app **full-refreshes dbt on every boot** (`DbManager.setup`),
so there's no built-in notion of "since last time." An events feed needs **state across runs**: persist a
prior snapshot (e.g. a stored events/leaderboard table in B2, or dbt **snapshots**) and **diff** the new
build against it to materialize *change* events. This is the core design decision; without it we only
have current state, not a stream.

**Pieces it will need:**
- An **event schema / model** (one row per event: type, timestamp/season-week, subject owner(s),
  payload/summary) — likely a new `marts`/`intermediate` layer that unions per-source event producers.
- **Snapshotting + diffing** to turn full-refresh state into append-only events (the state problem above).
- Per-area **event producers** (League Highlights first; later: standings swings, draft, gallery uploads).
- One or more **consumers** (page / push / LLM) — decided later, deliberately out of scope for v1.

**Open questions:** event granularity + schema; where prior state lives (B2 snapshot vs dbt snapshots vs
a small persisted table); de-duplication / "already notified" tracking; which consumer to build first;
whether this wants the eventual FastAPI seam (see `architecture-roadmap.md`) as its read API.

---

## FF-017 — Roster-picker value: acquisition cost vs utilized points

**Area:** dbt, frontend · **Priority:** Med · **Effort:** L · **Status:** Idea

**Done when:** there's a per-owner-season metric (candidate season title "best/worst roster picker")
measuring **return on acquisition spend** — what each owner *paid* to acquire players (auction draft
$ + waiver FAAB) against the **utilized points** those players actually produced in the owner's
starting lineup — so the title rewards getting started-lineup production cheaply, not raw output or
free bench churn.

**Why:** the obvious "total roster output" picker title (sum of rostered points) is uninteresting —
bench churn is free and low-skill, and it just tracks team strength. Real roster-picking skill is
*value*: production per dollar spent acquiring the player. The Roster Production work (FF-006) gives
us the **utilized points** side (`points_started` in `int__owner_player_season`); this item pairs it
with **acquisition cost**.

**Pieces it will need:**
- **Cost per acquired player:** auction draft `bid_amount` is already in `base_s001__draftpicks` /
  `auction_draft_table`. Waiver/FAAB spend *per player acquisition* is the open data question — we
  track team-level FAAB budget/acquisitions but per-pickup FAAB cost may not be in the source; snake
  (non-auction) drafts have no $ at all (would need a pick-value proxy / draft-capital curve).
- **Value metric:** utilized points per dollar, or points-over-expected-given-cost (a cost→points
  baseline curve), rolled up to owner-season. Decide whether to scope to auction years only (clean $)
  or build a cross-format draft-capital proxy.
- Wire into `int__season_titles` (+ `_long`) and the seed catalogs (`season_highlight_metrics`,
  `all_time_record_metrics`, mirror in `h2h_metrics` per CLAUDE.md). Regular-season utilized points.

**Open questions:** is per-acquisition FAAB cost available in the ESPN source? handle snake-draft
years (pick-value proxy vs auction-only); per-dollar ratio vs over-expectation model; relationship to
FF-009 (value-over-replacement framing).

**Why later:** depends on acquisition-cost data we haven't confirmed we have for waivers, and wants a
cost→points baseline — more than a one-row-seed title. Captured now so the utilized-points side
(shipped with FF-006) can be built on deliberately.

---

## FF-018 — Player spotlight pages + player-centric highlights

**Area:** frontend, dbt · **Priority:** Med · **Effort:** L · **Status:** Idea

**Done when:** every player surfaced in the app links to a dedicated **player spotlight** page that
visualizes that player's career metrics over time, and the platform gains a set of **owner-agnostic,
player-centric league highlights** — best players of a season, and best careers by both *prime/peak*
and *total*.

**What:** today players show up in tables (Player Data, the owner-spotlight Roster tab, draft tables)
but aren't themselves a destination — there's no per-player view. Build a **player spotlight** that's
the player analogue of the owner spotlight: a player's career arc visualized, cross-linked from
everywhere a player name appears — **notably Player Data and the owner-spotlight Roster tab** (and the
draft tables). Pair it with a player-centric highlight set that ranks *players*, not owners.

**Pieces / ideas:**
- **Player spotlight page** (`/player/{player_id}` or similar) — header (name, position, NFL-team
  history) + visualizations of career metrics over time: fantasy points by season/week, position rank,
  usage, prime vs decline. Reuse existing per-player data (`int__player_season_stats`,
  `stg__player_weeks`).
- **Cross-links** — make player names link to the spotlight from Player Data, the Roster tab, and draft
  tables (same web-of-views ethos as the owner cross-links).
- **Player-centric league highlights (owner-agnostic):** rank *players* — best player of each season
  (highest / position-adjusted points), best careers by **prime** (peak N-season window) and by
  **total** (career points), plus ideas like most consistent or biggest single-season spike. Likely its
  own seed catalog (player metrics) mirroring the league-highlights machinery, surfaced on the spotlight
  and/or a league-wide players view.

**Open questions:** route shape (`/player/{id}` vs under an existing section); NiceGUI charting
approach; "prime" definition (rolling best-N seasons vs peak single season); cross-position
normalization for a fair "best player"; whether player highlights get their own page or live on the
spotlights; historical depth (data is 2018+).

_Source: discussed during the FF-016 nav PR._

---

## FF-020 — Group-chat (s003) analytics: titles, mood, cross-source metrics

**Area:** dbt, frontend, backend · **Priority:** Med · **Effort:** L · **Status:** Idea

**Done when:** the s003 group-chat source feeds owner superlatives/titles into the metric catalogs
(League Highlights + H2H) and an owner-spotlight "chat persona", with any content-derived metrics
(mood, mentions) gated behind the privacy decision below.

**What:** FF-015 landed the pipeline + a basic `/group_chat` leaderboard. This is the analytics
build-out — turning chat activity into titles, leaderboards, and cross-source insights, reusing the
existing catalog/glossary machinery. Be inclusive with ideas now; prune at build time.

**Idea buckets:**
- **Superlatives / titles** (into the three catalogs — `all_time_record_metrics`,
  `season_highlight_metrics`, `h2h_metrics`, plus a `glossary_terms` row each): The Yapper / The Ghost
  (most/fewest messages, share-of-chat %), The Philosopher / One-Liner (avg word count), The Comedian
  (most `Laughed` received), The Villain (most `Disliked` + `Questioned`), Most Loved, The Hype Man
  (reactions given), The Lurker (high given / low sent), Meme Lord (attachments), engagement rate
  (reactions received per message).
- **Behavioral / timing** (timestamp-only, no content): Night Owl / Early Bird (by hour), Weekend
  Warrior (weekday vs weekend), gameday chatter spikes.
- **Cross-source with fantasy (s001) — the novel vein:** "All Talk, No Walk" (chat volume vs season
  record), talks-more-when-winning / quieter-when-losing, draft-day chatter spike, a league activity
  timeline by week overlaid with playoffs/draft.
- **Mood:** (a) *reaction-proxy* mood — positive (`Loved`/`Liked`/`Laughed`/`Emphasized`) vs negative
  (`Disliked`/`Questioned`) ratio over time; count-safe, recommended v1. (b) *lexicon sentiment* on
  message text → per-owner/week score; content-derived → privacy decision.
- **"Word cloud" / mentions:** a literal word cloud surfaces raw text (off-limits under the count-only
  rule). Privacy-safe reframe: scan text *in staging* against s001 player/team names → most-mentioned
  player/team (counts only). Most-mentioned owner (first names) is the one path to a *pairwise* H2H chat
  axis (there are no parsed @mentions otherwise). Content-derived → privacy decision.
- **Surfacing:** an owner-spotlight "chat persona" card (volume, favorite reaction given, active hours,
  their superlatives) is the highest-value / lowest-effort home; `/group_chat` grows from the stub.

**Privacy decision (gates the mood + mention ideas):** everything past `int__owner_chat_activity` is
owner-grain counts, never content. Reaction-proxy mood + timing/volume metrics are fine as-is. Lexicon
sentiment and entity-mention counts *derive from* text (computed upstream, only numbers emitted) —
decide whether content-derived numbers are acceptable before building those.

**Scoping note:** natural first PR = superlatives into the three catalogs + the spotlight chat-persona
card (reuses catalog/glossary machinery, keeps League Highlights ↔ H2H in sync). Cross-source metrics
are the standout follow-up.

_Source: brainstormed after the FF-015 pipeline landed. Related: FF-019 (glossary machinery),
FF-007 (media — shotgun videos from the same export, see that item)._

---

## FF-011 — Unify "league single best/worst week" logic

**Area:** dbt · **Priority:** Low · **Effort:** S · **Status:** Done

**Done when:** the league's single highest/lowest regular-season week is defined in exactly one place,
with both the season title and the week-grain chip flag sourced from it (no parallel computation).

**What:** today "the league's single highest (and lowest) score this season" is computed twice, in two
intermediates:
- `int__season_titles` ranks each team's `best_week_score` / `worst_week_score` to set
  `is_matchup_title` / `is_bad_matchup_title` (the season award).
- `int__team_week_highlights` independently does `max/min(score_for)` over the year to set
  `is_best_week` / `is_worst_week` (the spotlight schedule chip).

The chip↔title alignment is a deliberate invariant (a chip should mark the exact week that won the
title), but it currently rests on two separate code paths agreeing — they could silently drift (e.g. one
filters playoffs/unplayed weeks differently, or handles a co-best-week tie differently).

**Why now-ish:** not urgent — they agree today. Worth doing before `int__team_week_highlights` grows more
consumers (FF-010 builds the events feed on it), so the shared definition is locked in before more code
depends on it.

**Plan:**
1. New `int__league_season_week_extremes` (grain: **year**): `league_best_score` / `league_worst_score`
   = `max/min(score_for) filter (where outcome != 'U')` over `int__team_week_results` (played reg-season
   weeks). This becomes the *single* definition of the league's single highest/lowest week. (Optionally
   also carry `tightest_margin` / `biggest_margin` so the same model backs the Tightest/Biggest flags.)
2. `int__team_week_highlights`: replace its inline `league_extremes` CTE with a `ref()` to the new model;
   the `is_best_week` / `is_worst_week` chip flags are unchanged.
3. `int__season_titles`: replace `rank() over (partition by year order by best_week_score desc) = 1`
   with `best_week_score = league_best_score` (join the new model) for `is_matchup_title`; mirror for
   `is_bad_matchup_title`. Identical co-title semantics (every team whose best week equals the league
   max). Drop the now-unused `matchup_rank` / `bad_matchup_rank`.
4. Add a data test asserting `is_best_week` / `is_worst_week` line up 1:1 with `is_matchup_title` /
   `is_bad_matchup_title` so future drift fails the build. Update MODELS.md (new model + the two refs).

---

## FF-012 — H2H Dashboard

**Area:** dbt, frontend · **Priority:** Med · **Effort:** M · **Status:** Done

**Done when:** `/stats_center/h2h_dashboard` lets you pick 2+ owners and compare them across a
catalog of career metrics (leader highlighted per metric) plus the true pairwise head-to-head
record, with adding a new comparison stat being a one-row-seed + one-mart-branch change.

**What (shipped v1):** a metric-rows × owner-columns comparison grid driven by the same
seed-catalog pattern as League Highlights. New dbt: `int__owner_postseason_summary` (career
playoff/championship/toilet-bowl rollup), `int__owner_head_to_head` (pairwise record, reg vs
playoff), marts `h2h_owner_metrics` (tidy/long, every owner) + `h2h_matchup_records`, and the
`h2h_metrics` seed. Frontend `h2h_dashboard.py` renders the grid (leader crowned per
`sort_sign`, suppressed when all tie) with a lead Head-to-Head section. H2H record scope =
regular season headline + playoff line when the pair met in the postseason.

**Future stats to add (easy now — seed row + candidate branch):** longest H2H win streak,
biggest H2H blowout, playoff-only records, all-play / expected wins (see FF-009), draft-capital
metrics. Possible UI follow-ups: a prominent 2-owner banner, sortable/pinned metrics.

---

## FF-013 — Shootout / Slugfest records in League Highlights

**Area:** dbt · **Priority:** Low · **Effort:** S · **Status:** Done

**Done when:** the League Highlights page surfaces the highest- and lowest-*combined-score*
regular-season games (both teams added together) — all-time top-3 and per-season — using the
same seed-catalog machinery as the existing margin records.

**Why / context:** the H2H dashboard already shows "highest shootout / lowest slugfest" per
rivalry (computed in `int__owner_head_to_head`), and they're fun league-wide too. They're
game-level matchup records, structurally identical to the existing **Tightest games / Biggest
blowouts** (margin) records — so they reuse that exact pattern.

**Best place:** the **Matchups** section of *both* tabs. All-Time → a new `Combined` category
sub-cluster next to `Margins`/`Luck` (top-3 records). By-Season → single-winner titles alongside
*Tightest game* / *Biggest blowout* (FF-012 converted the By-Season margin records to single-winner
titles and deleted the separate "Closest & Most Lopsided" block plus the `metric_type`/`result_n`
seed columns — so shootout/slugfest follow the same one-crown-per-season shape).

**Plan (mirrors the margin records end-to-end — no frontend changes):**
1. `int__matchup_margins`: add `combined = winner_score + loser_score` (one column + properties
   entry). It's already one row per played reg-season game with winner/loser scores.
2. `all_time_records.sql`: add a `combined_records` CTE mirroring `margin_records` —
   `cross join (values ('highest_shootouts'), ('lowest_slugfests')) as directions`, `metric_value
   = combined`, rank per `sort_sign`, keep top 3, `detail` = `winner_score-loser_score`; union into
   `candidates`.
3. `season_highlights.sql`: add a `combined_candidates` CTE mirroring `margin_candidates`, union into
   `candidates` (the mart's `where metric_rank = 1` keeps the single highest/lowest combined game that
   season — a single-winner title).
4. Seeds: 2 rows in `all_time_record_metrics.csv` (section `Matchups`, category `Combined`,
   `metric_type record`, `sort_sign` 1 / -1, `value_format points`, `subtitle_kind context`,
   `result_n 3`); 2 in `season_highlight_metrics.csv` (current columns — `category Combined`,
   `section Matchups`, `sort_sign` 1 / -1, `value_format points`, next `display_order`, blank
   `empty_label`). Update MODELS.md.
5. Names to ratify with the league (see OD-001) — e.g. *Highest-scoring games* / *Lowest-scoring
   games*, or *Shootouts* / *Slugfests*.

---

## FF-014 — Postseason history page

**Area:** frontend, dbt · **Priority:** Med · **Effort:** M · **Status:** Done

**Done when:** `/stats_center/postseason_history` is a real page presenting the league's postseason
history — champions, runner-ups, and toilet-bowl finishes by season, plus the per-owner trophy case —
with adding a season needing no page change.

**What (shipped):** the postseason stub is now a three-tab page. New marts under
`marts/stats_center/postseason_history/`: `postseason_timeline` (one row per season — champion /
runner-up / 3rd / toilet-bowl loser with reg-season seed), `postseason_trophy_case` (per-owner career
hardware, thin wrap of `int__owner_postseason_summary`), and `postseason_bracket` (one row per
bracket slot per round — game or first-round bye — collapsing `int__postseason_team_weeks`). The
bracket mart handles every format era: byes are **data-derived** (winners team absent from round 1, so
the 4-team era has none and the 6-team era byes the top 2 seeds), and round labels are computed
**relative to each bracket's last round** rather than hard-coded weeks. Frontend `postseason_history.py`
renders the **Brackets** tab (season picker → winners + toilet brackets as columns of matchup cards,
bye slots and a bordered championship game), **Timeline** tab (newest-first season finisher cards), and
**Trophy Case** tab (per-owner medal tallies + playoff record). Mirrors the League-Highlights card style;
`SECTION_COLORS["Postseason"]` (teal).

**Future ideas:** SVG connector lines between bracket rounds; link a season's champion to its
owner-spotlight; surface `best_finish` / playoff win% sortable. Pairs with FF-008 (nav refactor) as a
new top-level destination.

---

## FF-008 — Refactor website navigation

**Area:** frontend · **Priority:** Low · **Effort:** M · **Status:** Done

**Done when:** every major section is reachable directly from the splash/landing page (not buried
under Stats Center), and the current-season counters take a smaller footprint instead of dominating
the landing screen.

**What (shipped):** the splash (`/`) is now a pure **section-tile hub** (`section_tile` /
`SECTION_TILES`, access-gated) — every destination is a top-level route; the `/stats_center` landing
was removed and its header entry dropped (`common_header` updated to match). The current-season
standings + shotgun counters **moved off the splash entirely to their own `/current_season` page**,
resolving the open question — they no longer live on the landing at all.

---

## FF-016 — Revise pre-Claude-Code pages/dbt/backend

**Area:** frontend, dbt, backend · **Priority:** Med · **Effort:** L · **Status:** Done

**Done when:** the pages (and their dbt models + any backend) built *before* the conventions in
CLAUDE.md / MODELS.md / FRONTEND.md / BACKEND.md were established are brought up to current standards —
filter-page pattern, mart layering, contracts/properties, cross-links, doc maps — with no regressions.

**What (shipped):** a broad sweep of the pre-Claude-Code surface onto current conventions:
- **Player Data**, **Draft Analysis** (snake + auction), **Strength of Schedule**, **owner spotlight**,
  and **splash** — filter-page pattern, **page-aligned mart + page folders** (dropped the `stats_center/`
  grouping in both `marts/` and `frontend/`), contracts/properties coverage, and **cross-links to owner
  spotlights** (`rowClick → /owner_history` on SoS + both draft tables; spotlight rows/cards clickable).
- **Backend**: the `s001` teams extractor was reworked to capture rosters **per NFL week**, fixing the
  2018-2019 two-week playoff lineups (feeds `int__optimal_lineup_players` / the Roster tab).
- Doc maps (MODELS.md / FRONTEND.md / CLAUDE.md / BACKEND.md) kept current throughout.

Also folded in during the PR: current-season = latest *drafted* season (+ standings-rank hardening);
owner-spotlight navigation gated to **played** seasons + an empty-season guard; postseason round labels
unified as `TB Round N` across the dropdown and the Postseason table.

_Note: the item anticipated splitting into several small PRs; this single PR did the broad analytics sweep._

---

## FF-006 — Owner-attributed Roster Production (reframed)

**Area:** frontend, dbt · **Priority:** Low · **Effort:** M · **Status:** Done

**Done when (reframed):** each owner-season's rostered-player production is viewable, correctly handling
mid-season ownership changes (only the weeks an owner held the player count, weeks-held shown), including
started-only points. _(Original: "the Player Data table can group players by owner" — see Decision.)_

**Decision (reframe):** the original ask — an *owner filter on the Player Data table* — was dropped. A
player's fantasy points are intrinsic to the *player*, and Player Data is a player-performance reference;
splitting a traded player into per-owner rows would distort that table. "What did the players *I* rostered
produce" is an **owner-season** question, so it belongs where the grain is naturally one owner-season and
mid-season trades render correctly. Player Data stays player-centric.

**What (shipped):**
- `int__owner_player_season` (owner-season-player grain) — `weeks_held`/`points_held` (every rostered
  week, bench/IR included) + `weeks_started`/`points_started` (active lineup only); a mid-season trade
  fans the player out to one row per holder. (Delivers the started-only stretch too.)
- mart `owner_roster_production` — Rostered Pts / Started Pts / Total Pts / Capture % / Roster Util %.
- the **`/roster_production`** page (filter pattern: year / owner / position, rows cross-linked to owner
  spotlights) **and** the owner-spotlight Roster tab "All" view (`_season_roster`).

_Source: GH #27 (reframed during the FF-016 nav PR)._

---

## FF-009 — Quantify luck via all-play / expected wins

**Area:** dbt, frontend · **Priority:** Low · **Effort:** L · **Status:** Done

**Done when:** there's an `int__` model exposing each owner-season's all-play record / expected
wins, and the snub + luck metrics use it as a more rigorous "you were robbed by the schedule"
measure than the points-based gate.

**What (shipped):** the schedule-neutral **all-play / expected wins** layer plus a full surfacing.
- `int__all_play_records` (team-week: a self-join within year+week → all-play W-L-T) rolled up by
  `int__owner_season_all_play` to `all_play_win_pct`, `expected_wins` (win% × games), `actual_wins`,
  and **`schedule_luck` = actual − expected** (+ lucky, − robbed). Sanity-tested: all-play win%
  averages 0.5; a singular test (`assert_all_play_expected_equals_actual`) pins league totals to
  expected=actual / luck≈0 each season (zero-sum).
- `int__season_titles` gains an **all-play (merit-based) snub/lucky-in** variant alongside the
  existing points-based one (`all_play_vs_field` self-join on all-play win%), plus **schedule-luck
  titles** (luckiest / most-robbed), fanned out in `_long` and rolled up in `int__owner_career_summary`.
- A new top-level **Luck** section across **both** League Highlights and the H2H Dashboard
  (categories: Schedule Luck / Matchup Luck / Playoff Luck) consolidates every luck metric, moved out
  of Matchups/Postseason. Driven entirely by the three seed catalogs.
- **Single definition of luck:** the per-week all-play standing is the one source. `int__lucky_records`
  (the old median-based model) was deleted; the discrete lucky-win / unlucky-loss chips + career counts
  are now a *threshold* on the same all-play standing (won/lost a week you'd have lost/beaten most of
  the league), and the continuous `schedule_luck` is the season measure. The redundant median-based
  *season titles* were retired — all-play owns the season luck crown; the quantized view survives only
  as career week-counts + the spotlight chips.

_Built on FF-016's analytics conventions; deliberately kept the existing lightweight luck snapshots
(median-based + points-based) alongside the new measure rather than replacing them._

---

## FF-019 — Glossary page + glossary as the relational concept dimension

**Area:** frontend, dbt · **Priority:** Med · **Effort:** M · **Status:** Done

**Done when:** there's a `/glossary` page defining the platform's terms in one place, and the metric
catalogs reference those definitions relationally instead of each re-explaining concepts.

**What (shipped):**
- New **`glossary_terms`** seed — the concept dimension (~55 terms: `slug`/`term`/`category`/
  `short_def`/`full_def`/`related`), the single source of truth for terminology. Thin `glossary` mart
  backs the page.
- **Relational normalization:** each metric catalog (`all_time_record_metrics`,
  `season_highlight_metrics`, `h2h_metrics`, `h2h_rivalry_metrics`) gained a nullable `glossary_slug`
  FK (dbt `relationships` test) to its concept, and the **duplicated concept text was trimmed out of
  per-metric descriptions** — the concept lives once in the glossary. The metric marts surface
  `glossary_slug` so cards can deep-link.
- **`/glossary` page** — searchable, category-grouped (`CATEGORY_ORDER` + `SECTION_COLORS`), each term
  anchored at `#slug` for deep-linking, with related-term cross-link chips. Splash tile + a reusable
  `glossary_link()` helper.
- **Wired** the metric-card info icon → `/glossary#<slug>` on League Highlights (All-Time + By-Season),
  the H2H Dashboard rows, and the owner-spotlight Highlights card. Remaining surfaces can adopt the
  helper incrementally.

_The redundancy-reduction framing (glossary as the relational table the seeds reference) came from the
FF-009 luck-labeling discussion._

---

## FF-015 — iMessage group-chat data pipeline + analytics

**Area:** backend, dbt, frontend · **Priority:** Low · **Effort:** L · **Status:** Done

**Done when:** the league's iMessage group-chat history is ingested as a new source and at least one
aggregate analytics use case is built on it.

**What (shipped):** the league group chat as source **`s003`**, end to end —

- **Local-only extract** (`make extract-imessage` / `extract-imessage-full` → `python3 -m imessage`,
  code in **`scripts/imessage/`** — kept out of the deployed image; the deployed side is only the thin
  `S003Source` ingest descriptor): snapshots `chat.db`, **prunes the copy to the one
  target thread** and exports it with `imessage-exporter -p` (the `-t` filter is a greedy union and
  can't target a thread), parses the 4.x HTML (`parse.py`, mirroring the exporter's askama templates)
  into message + reaction rows, and uploads **incremental windowed slices** to B2 (re-exports from the
  last slice minus a day; full history on first run).
- **Append-mode ingest** (`INGEST_MODE` + `DbManager.get_all_table_paths`): every slice is unioned and
  **`base_s003__{messages,reactions}` dedupe on stable uids** (iMessage GUID when present, else a
  timestamp+sender+text hash; reactions on message+reactor so a changed tapback updates).
- **dbt:** `base → stg__chat_{messages,reactions} → int__owner_chat_activity →
  marts/group_chat/chat_activity_leaderboard`. Raw text lives only in base/staging; **every model from
  the intermediate onward is owner-grain counts**.
- **Frontend:** the **`/group_chat`** page — a year-filtered engagement leaderboard (messages, avg
  words, attachments, reactions given/received, share of chat), rows cross-linked to owner spotlights.
  Member-gated splash tile.
- **Privacy:** sender→owner attribution via the local-only `resources/sensitive_seeds/owner_handles.csv`
  (`handle,owner_id`; never uploaded — B2 stores `owner_id`). Needs league consent before the first
  extract.

**Future analytics (deferred):** reaction "burn of the year" / most-loved leaderboards, activity
timeline (chatter vs results), per-owner catchphrases/word clouds, LLM season recap (a concrete consumer
for FF-010's event feed). The v1 leaderboard is the seed; richer aggregates are additive.

---

## FF-002 — Revise sensitive-seed storage security

**Area:** security, infra · **Priority:** Low · **Effort:** S–M · **Status:** Done

**Done when:** B2-stored seeds are protected beyond bcrypt (least-privilege bucket keys, Fly
secrets, strong `STORAGE_SECRET`, git-history scan) and we've made a deliberate call on
at-rest encryption.

**What (shipped):** the at-rest call was made — **sensitive seeds are now encrypted in B2** (Fernet,
keyed by `SEED_ENCRYPTION_KEY`; `backend/crypto.py`). `write_sensitive_seeds` uploads `<name>.csv.enc`;
`fetch_resources` decrypts back to plaintext local CSVs at boot (dbt seeds read plaintext). The key
lives in a different trust boundary than the B2 credentials, hardening the "B2 leaked but app secret
didn't" case. Mandatory single path (no plaintext fallback), with transitional tolerance for legacy
plaintext partitions until the first encrypted push.
- **`make rotate-secrets`** (`scripts/rotate_secrets.py`) — one command that indexes every secret
  (app-managed vs provider-manual), rotates `STORAGE_SECRET` + `SEED_ENCRYPTION_KEY`, rewrites the
  local env files in place (never echoing values), and re-encrypts + pushes the seeds. First run is
  the "turn on encryption" step. `--dry-run` / `--keys` / `--no-push` flags.
- **gitleaks** — pre-commit hook + `make scan-secrets` (full-history). A 2023-era hardcoded GroupMe
  token was found in history, **confirmed dead (HTTP 401)**, allowlisted in `.gitleaksignore`.
- **Docs/config** — `docs/security.md` (threat model + owner-operated hardening checklist + rotation
  usage); `SEED_ENCRYPTION_KEY` added to env examples; `scripts/deploy_app.sh` fixed (drifted B2 var
  names + new key); BACKEND.md updated.

**Owner-operated (documented, not code — see `docs/security.md` checklist):** least-privilege B2 key
scoped to the one bucket, Fly secrets (not image-baked), private bucket + lifecycle rule expiring old
`sensitive_seeds/` partitions, periodic ESPN-cookie rotation. **Non-goals:** a real secrets manager
(Vault/KMS), per-column DB encryption.

**Activation (owner):** run `make rotate-secrets` once to generate the key + push the first encrypted
seed set, then `direnv reload` + `./scripts/deploy_app.sh`. Rotating `STORAGE_SECRET` logs everyone out.
