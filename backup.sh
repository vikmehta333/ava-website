#!/bin/bash
# Weekly automated backup of the live WordPress site into this git repo.
# Invoked by LaunchAgent com.vlg.ava-backup. WordPress is source of truth.
set -euo pipefail

REPO="$HOME/ava-website"
cd "$REPO"

# Pull WordPress credentials from the ava-digital-agents env (source of truth).
ENV_FILE="$HOME/ava-digital-agents/.env"
if [ -f "$ENV_FILE" ]; then
  export WP_USER="$(grep -E '^WP_USER=' "$ENV_FILE" | cut -d= -f2-)"
  export WP_APP_PASSWORD="$(grep -E '^WP_APP_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)"
fi

/usr/bin/env python3 export_wp.py

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git -c user.name="Vik Mehta" -c user.email="vik@velocitylogicgroup.com" \
      commit -q -m "Automated backup of live site ($(date +%Y-%m-%d))"
  git push origin main
  echo "$(date): changes backed up and pushed"
else
  echo "$(date): no changes"
fi
