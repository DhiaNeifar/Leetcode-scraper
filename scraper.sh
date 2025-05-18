#!/bin/bash

# Use LEETCODE_SCRAPER_HOME if set, otherwise default to script location
if [ -n "$LEETCODE_SCRAPER_HOME" ]; then
    PROJECT_DIR="$LEETCODE_SCRAPER_HOME"
else
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

CONFIG_FILE="$PROJECT_DIR/.scraper_config"
LOG_FILE="$PROJECT_DIR/cron.log"
PYTHON="$PROJECT_DIR/venv/bin/python"
XVFB_RUN="/usr/bin/xvfb-run"

log() {
    echo "[$(date)] [SCRAPER] $1" >> "$LOG_FILE"
}

log "🚀 Starting scraper..."

if [ ! -f "$CONFIG_FILE" ]; then
    log "❌ Missing .scraper_config"
    exit 1
fi

source "$CONFIG_FILE"
REPO_FOLDER=$(basename "$REPO_URL" .git)

if [ ! -f "$PROJECT_DIR/leetcode_cookies.xml" ]; then
    log "⚠️ WARNING: leetcode_cookies.xml not found. Auth may fail."
fi

"$XVFB_RUN" -a "$PYTHON" "$PROJECT_DIR/main.py" "$REPO_FOLDER"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    log "❌ Scraper failed with exit code $EXIT_CODE"
else
    log "✅ Scraper finished successfully."
fi
