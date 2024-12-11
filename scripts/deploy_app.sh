#!/bin/bash

fly secrets set STORAGE_SECRET="${STORAGE_SECRET}"
fly secrets set ENDPOINT="${ENDPOINT}"
fly secrets set REGION="${REGION}"
fly secrets set ACCESS_KEY="${ACCESS_KEY}"
fly secrets set SECRET_KEY="${SECRET_KEY}"
fly secrets set BUCKET_NAME="${BUCKET_NAME}"
fly secrets set LEAGUE_ID="${LEAGUE_ID}"
fly secrets set ESPN_S2="${ESPN_S2}"
fly secrets set SWID="${SWID}"
