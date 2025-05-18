#!/bin/bash

# Use LEETCODE_SCRAPER_HOME if set, otherwise use the script's directory
if [ -n "$LEETCODE_SCRAPER_HOME" ]; then
    PROJECT_DIR="$LEETCODE_SCRAPER_HOME"
else
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

CONFIG_FILE="$PROJECT_DIR/.scraper_config"
LOG_FILE="$PROJECT_DIR/cron.log"

log() {
    echo "[$(date)] [GIT] $1" >> "$LOG_FILE"
}

log "🔁 Starting Git push..."

if [ ! -f "$CONFIG_FILE" ]; then
    log "❌ Missing .scraper_config"
    exit 1
fi

source "$CONFIG_FILE"
REPO_FOLDER=$(basename "$REPO_URL" .git)
cd "$PROJECT_DIR/$REPO_FOLDER" || { log "❌ Cannot cd into $REPO_FOLDER"; exit 1; }

git add .
DATE_STRING=$(date)
git commit -m "🤖 Auto-update LeetCode submissions on $DATE_STRING" 2>/dev/null

if [ $? -ne 0 ]; then
    log "ℹ️ Nothing to commit."
else
    git remote set-url origin "https://$GITHUB_TOKEN@${REPO_URL#https://}"
    PUSH_OUTPUT=$(git push origin main 2>&1)
    PUSH_EXIT=$?

    if [ $PUSH_EXIT -eq 0 ]; then
        log "✅ Push successful."
    else
        log "❌ Push failed."
    fi

    log "📄 Push output:"
    log "$PUSH_OUTPUT"
fi
