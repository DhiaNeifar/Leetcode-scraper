#!/bin/bash

echo "🛠️ LeetCode Scraper Setup Starting..."

CONFIG_FILE=".scraper_config"
LOG_FILE="setup.log"
VENV_DIR="venv"
PROJECT_DIR=$(pwd)

log() {
    echo "[$(date)] $1" | tee -a "$LOG_FILE"
}

# Step 1: Virtual environment
if [ ! -d "$VENV_DIR" ]; then
    log "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    log "⬆️ Upgrading pip..."
    pip install --upgrade pip
    log "📚 Installing dependencies..."
    pip install -r requirements.txt
else
    log "✅ Virtual environment already exists."
    source "$VENV_DIR/bin/activate"
fi

# Step 2: LeetCode login
echo ""
echo "🔐 Please log in to https://leetcode.com in Chrome."
read -p "Press ENTER once logged in..."

# Step 3: Config
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    log "📄 Loaded config: $REPO_URL"
else
    read -p "📡 Enter GitHub repo (e.g., https://github.com/user/leetcode-solutions.git): " REPO_URL
    echo "REPO_URL=\"$REPO_URL\"" > "$CONFIG_FILE"
fi

REPO_FOLDER=$(basename "$REPO_URL" .git)

# Step 4: GitHub Token
if grep -q 'GITHUB_TOKEN=' "$CONFIG_FILE"; then
    source "$CONFIG_FILE"
    log "🔁 Using saved GitHub token."
else
    read -p "🔑 Enter GitHub personal access token: " GITHUB_TOKEN
    echo "GITHUB_TOKEN=\"$GITHUB_TOKEN\"" >> "$CONFIG_FILE"
fi

# Step 5: Clone repo
if [ -d "$REPO_FOLDER" ]; then
    log "⚠️ Repo folder $REPO_FOLDER exists."
    read -p "Re-clone the repo? (deletes folder) [y/N]: " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        rm -rf "$REPO_FOLDER"
        git clone "$REPO_URL"
    fi
else
    git clone "$REPO_URL"
fi

# Step 6: Git ignore
if ! grep -qx "$REPO_FOLDER/" .gitignore; then
    echo "$REPO_FOLDER/" >> .gitignore
    log "📄 Added $REPO_FOLDER/ to .gitignore"
fi

# Step 7: Initial scrape and push
cd "$PROJECT_DIR" && bash scraper.sh
cd "$PROJECT_DIR" && bash github.sh

# Step 8: Setup cron jobs
read -p "⏱️ Setup cron jobs? (y/n): " setup_cron
if [[ "$setup_cron" == "y" || "$setup_cron" == "Y" ]]; then
    read -p "Scraper frequency ([m]inutes, [h]ours, [d]ays): " freq
    read -p "Scraper interval: " int

    case $freq in
        m) cron1="*/$int * * * *" ;;
        h) cron1="0 */$int * * *" ;;
        d) cron1="0 0 */$int * *" ;;
        *) log "❌ Invalid scraper freq"; exit 1 ;;
    esac

    next_int=$((int + 1))

    case $freq in
        m) cron2="*/$next_int * * * *" ;;
        h) cron2="0 */$next_int * * *" ;;
        d) cron2="0 0 */$next_int * *" ;;
        *) log "❌ Invalid push freq"; exit 1 ;;
    esac

    # Generate fully qualified commands for cron
    cron_entry1="$cron1 cd $PROJECT_DIR && /bin/bash scraper.sh >> $PROJECT_DIR/cron.log 2>&1"
    cron_entry2="$cron2 cd $PROJECT_DIR && /bin/bash github.sh >> $PROJECT_DIR/cron.log 2>&1"

    (crontab -l 2>/dev/null; echo "$cron_entry1"; echo "$cron_entry2") | crontab -
    log "✅ Cron jobs added"
fi

log "✅ Setup complete."
