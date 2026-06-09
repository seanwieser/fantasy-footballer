#!/usr/bin/env bash
# Stub the gitignored sensitive seeds so dbt can build its manifest where the real CSVs are
# absent (e.g. pre-commit.ci's public checkout) — which is all the sqlfluff dbt templater needs
# to compile. Only writes a header-only stub when the real seed is MISSING, so it never clobbers
# real data locally; stubs land in the gitignored resources/sensitive_seeds/, so no PII is ever
# committed. Only the seeds that dbt models ref() are needed (owner_names, display_names).
set -euo pipefail

dir="resources/sensitive_seeds"
mkdir -p "$dir"

[ -f "$dir/owner_names.csv" ]   || printf 'owner_id,owner_name\n'   > "$dir/owner_names.csv"
[ -f "$dir/display_names.csv" ] || printf 'owner_id,display_name\n' > "$dir/display_names.csv"
