#!/bin/bash
# Constants refresh — reads TL;DR from Constants deck and regenerates constants_data.js
# Runs independently on Wednesdays (one day after main data refresh)

set -e

GDRIVE="$HOME/skills/gdrive"
DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Refreshing Constants..."

cd "$GDRIVE" && uv run gdrive-cli.py slides read \
    1Yt6WwNtNn53E5U0_iRgN6-eacen52ClndnZDbyAN3z0 \
    > /tmp/constants_slides.json 2>/dev/null

python3 "$DASHBOARD_DIR/refresh_constants.py"

echo "Done."
