# Investigations

A knowledge bank of **data investigations we ran and the conclusion we reached** — especially the ones
that did *not* turn into a feature. The point is to not re-run the same analysis from scratch later, and
to preserve interesting league facts that surfaced along the way. Distinct from the
[feature backlog](feature-backlog.md) (things to *build*), [open-discussion](open-discussion.md) (questions
with no settled answer), and the [architecture roadmap](architecture-roadmap.md) (technical direction):
these have a **settled finding**.

Each item has an **`INV-XXX`** id (zero-padded, assigned in order, never reused). When an investigation
motivates real work, link it to the `FF-` item it spawns.

---

## INV-001 — "Champion snubs": would a non-playoff team have won the title?

**Question:** has a team that *missed the playoffs* ever been good enough that it would have **won the
championship** had it been in the bracket? The rigorous framing (not just "outscored the champ"): re-seed
the playoff field by **regular-season points-for**, place each snub at its PF-projected seed, rebuild the
bracket, and replay it **round-by-round using each team's actual score that playoff week** — higher score
advances. A *snub* = a team in the PF-top-N field that missed the real (record-based) playoffs. A
**champion snub** = a snub that wins this simulated bracket.

**Finding: it has never happened.** Under **both** reasonable definitions, every season's simulated
champion is a team that genuinely made the real playoffs:
- **Variant A — full PF reseed** (whole field reseeded by points-for, bracket rebuilt): no champion snub
  in any season.
- **Variant B — single insertion** (real field kept, the snub dropped in at its PF seed, the worst real
  team bumped out): no champion snub either.

The finding is **robust to the definition** — the ceiling for a snub is reaching the championship *game*,
never winning it.

**Closest call — 2018 Casey Magid.** He led the *entire league* in regular-season points (would've been
the **#1 PF seed**) yet missed the playoffs. In the reseed he reaches the **final and loses** (to Liam
Bourke, the actual champion). In Variant B, *both* 2018 PF-snubs (Casey #1 and Travis Truong #3) reach the
final but lose to Liam — i.e., 2018 Liam was a legit champion who'd beat the snubs head-to-head anyway.
Casey is a serial snub (top-of-PF-field while missing the playoffs in 2018, 2020, 2024) — the league's
points-rich, win-poor manager.

**Why the naive metric is misleading.** A simpler signal — "a non-playoff team that outscored the eventual
champion in every playoff week" — *does* fire once (2020 Casey Magid: 127.88 / 141.62 / 202.64 vs champion
Travis Truong's 121.26 / 137.28 / 184.20). But it's misleading because it **ignores the bracket path**:
seeded into the actual bracket, Casey draws a red-hot Sam Waterstone in round 1 (127.88 vs **158.02**) and
is eliminated before he could ever meet the champion. This is exactly why the path-aware simulation is the
honest test.

**Per-season simulated snub finishes (Variant A, full PF reseed):**

| Year | Sim champion | Snub (PF seed) → how far they got |
|------|--------------|-----------------------------------|
| 2018 | Liam Bourke | Casey Magid (#1) → **Runner-up**; Travis Truong (#3) → Semifinal |
| 2019 | Samir Seshadri | Sean Wieser (#4) → Semifinal |
| 2020 | Travis Truong | Casey Magid (#5) → First Round |
| 2021 | Casey Magid | Sam Waterstone (#6) → First Round |
| 2022 | Travis Truong | Nick Contarino (#3) → Semifinal |
| 2023 | Casey Magid | Sean Wieser (#6) → First Round |
| 2024 | Wynham Gweemo | Casey Magid (#4) → Semifinal |
| 2025 | Nick Contarino | (none) |

**Method / how to reproduce** (the sim was a throwaway read-only script, not kept):
- **Reg-season PF** (seeding): `int__owner_season_scoring.reg_points_total` + `made_playoffs`.
- **Per-playoff-week scores** (advancement): `int__team_week_results where is_playoff` — every team
  (including byes/consolation) has a real score each playoff week; rounds map to the sorted playoff weeks.
- **Real playoff seeds** (Variant B): `int__team_postseason.seed` where `made_playoffs`.
- **Field size / rounds:** `base_s001__settings.playoff_team_count` (4-team / 2-round in 2018–19, 6-team /
  3-round from 2020). The 2018–19 two-week matchup periods are already aggregated into one score per
  playoff "week" upstream, so each playoff week = one round in every era.
- **Assumptions:** fixed bracket (no reseed after round 1, ESPN's default); ties broken to the better
  seed. Neither assumption changes the headline (2018 Casey reaches the final, 2020 Casey exits round 1
  under either convention).

**Decision:** not built — nothing interesting enough surfaced (no champion snub ever occurred). Preserved
here as a league fact (2018 Casey Magid, the league's only "phantom finalist") and so the analysis isn't
re-derived from scratch. If revisited, the natural home would be a callout on the Postseason History page
([FF-014]).

> **Note on "snub" definitions:** this investigation seeds the simulation by a **PF-projected seed**
> (top-N by points-for). That's *not* the platform-canonical snub. The Postseason History brackets tab's
> **Snubs / Lucky-In** lists (mart `postseason_snub_luck`) use the canonical `int__season_titles`
> definitions instead (snub = missed playoffs despite outscoring ≥1 playoff team), for consistency with
> League Highlights / H2H. The two overlap heavily but aren't identical.
