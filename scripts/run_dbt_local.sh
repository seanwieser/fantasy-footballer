#!/bin/bash

poetry run dbt build --full-refresh --no-partial-parse --show-all-deprecations --profiles-dir ./dbt/fantasy_footballer --project-dir ./dbt/fantasy_footballer --target app
