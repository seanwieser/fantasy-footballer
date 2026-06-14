#!/bin/bash

fly secrets set STORAGE_SECRET="${STORAGE_SECRET}"
fly secrets set SEED_ENCRYPTION_KEY="${SEED_ENCRYPTION_KEY}"
fly secrets set ENDPOINT="${ENDPOINT}"
fly secrets set REGION="${REGION}"
fly secrets set APPLICATION_KEY_ID="${APPLICATION_KEY_ID}"
fly secrets set APPLICATION_KEY="${APPLICATION_KEY}"
fly secrets set BUCKET_NAME="${BUCKET_NAME}"
fly secrets set LEAGUE_ID="${LEAGUE_ID}"
fly secrets set ESPN_S2="${ESPN_S2}"
fly secrets set SWID="${SWID}"
