#!/bin/sh
# Put site/ online at https://toronto-coop-map.vercel.app (Vercel account ash-4456).
# Uploads a plain copy of site/ with no git history: Vercel blocks uploads whose
# commit author it can't match to the account.
# Run:  sh builder/deploy.sh   (after builder/publish.py)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp -R "$ROOT/site/." "$TMP/"
TOKEN="$(grep '^VERCEL_TOKEN=' "$ROOT/.env" | cut -d= -f2-)"
cd "$TMP"
npx --yes vercel@latest deploy --prod --yes --token "$TOKEN" --scope ash-4456 --name toronto-coop-map
echo "$(date '+%Y-%m-%d %H:%M:%S')  INFO   Deployed site/ to https://toronto-coop-map.vercel.app" >> "$ROOT/logs/run.log"
