#!/bin/bash

echo "🛠️  LeetCode Scraper Setup Starting..."

CONFIG_FILE=".scraper_config"

# Step 1: Setup virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate

    echo "⬆️ Upgrading pip..."
    pip install --upgrade pip

    # Step 2: Install dependencies
    echo "📚 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "✅ Virtual environment already exists."
    source venv/bin/activate
fi
source venv/bin/activate

# Step 3: Prompt user to login to LeetCode
echo ""
echo "🔐 Please log in to https://leetcode.com in Chrome (same profile you use normally)."
read -p "Press ENTER once you are logged in..."

# Step 4: Load repo info or ask user
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    echo "📄 Loaded saved config:"
    echo "   Repo URL: $REPO_URL"
else
    read -p "📡 Enter the HTTPS link to your GitHub repository (e.g., https://github.com/yourname/leetcode-solutions.git): " REPO_URL
    echo "REPO_URL=\"$REPO_URL\"" > "$CONFIG_FILE"
fi

repo_folder=$(basename "$REPO_URL" .git)

# Clone or reuse repo
if [ -d "$repo_folder" ]; then
    echo "⚠️  Folder $repo_folder already exists. Using existing folder."
    read -p "Do you want to re-clone the repository? (this will delete the existing folder) [y/N]: " reclone
    if [[ "$reclone" == "y" || "$reclone" == "Y" ]]; then
        echo "🗑️  Removing existing folder and re-cloning..."
        rm -rf "$repo_folder"
        git clone "$REPO_URL"
    else
        echo "🔁 Proceeding with existing folder."
    fi
else
    echo "🔄 Cloning repository..."
    git clone "$REPO_URL"
fi

# Add the repo folder to .gitignore
if ! grep -qx "$repo_folder/" .gitignore; then
    echo "$repo_folder/" >> .gitignore
    echo "📄 Added $repo_folder/ to .gitignore"
fi

# Step 5: Scrape submissions
echo "🧠 Running LeetCode scraper..."
xvfb-run -a python3 main.py "$repo_folder"

# Step 6: Push results to GitHub
cd "$repo_folder" || { echo "❌ Failed to enter repo folder."; exit 1; }
git add .
git commit -m "🤖 Auto-update LeetCode submissions on $(date)" || echo "ℹ️ No changes to commit."

# Use saved token or ask for it
if [ -z "$GITHUB_TOKEN" ]; then
    read -p "🔑 Enter your GitHub personal access token: " GITHUB_TOKEN
    echo "GITHUB_TOKEN=\"$GITHUB_TOKEN\"" >> "../$CONFIG_FILE"
else
    echo "🔁 Using saved GitHub token."
fi

git remote set-url origin "https://$GITHUB_TOKEN@${REPO_URL#https://}"
git push origin main

cd ..

# Step 7: Optional: Setup cron job
echo ""
read -p "⏱️  Do you want to run the scraper automatically? (y/n): " cron_choice
if [[ $cron_choice == "y" || $cron_choice == "Y" ]]; then
    read -p "🕐 Run how often? Choose: [m]inutes, [h]ours, [d]ays: " freq
    read -p "Enter frequency number (e.g., every 2 hours = 2): " interval

    venv_python="$(pwd)/venv/bin/python"
    project_dir="$(pwd)"
    cron_entry=""

    case $freq in
        m) cron_entry="*/$interval * * * * cd $project_dir && xvfb-run -a $venv_python main.py $repo_folder && cd $repo_folder && git add . && git commit -m '🤖 Auto-update via cron on \$(date)' || true && source ../$CONFIG_FILE && git remote set-url origin \"https://\$GITHUB_TOKEN@\${REPO_URL#https://}\" && git push origin main >> $project_dir/cron.log 2>&1" ;;
        h) cron_entry="0 */$interval * * * cd $project_dir && xvfb-run -a $venv_python main.py $repo_folder && cd $repo_folder && git add . && git commit -m '🤖 Auto-update via cron on \$(date)' || true && source ../$CONFIG_FILE && git remote set-url origin \"https://\$GITHUB_TOKEN@\${REPO_URL#https://}\" && git push origin main >> $project_dir/cron.log 2>&1" ;;
        d) cron_entry="0 0 */$interval * * cd $project_dir && xvfb-run -a $venv_python main.py $repo_folder && cd $repo_folder && git add . && git commit -m '🤖 Auto-update via cron on \$(date)' || true && source ../$CONFIG_FILE && git remote set-url origin \"https://\$GITHUB_TOKEN@\${REPO_URL#https://}\" && git push origin main >> $project_dir/cron.log 2>&1" ;;
        *) echo "❌ Invalid frequency"; exit 1 ;;
    esac

    (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    echo "✅ Cron job added. Scraper will run every $interval $freq and push updates to GitHub."
fi


echo ""
echo "✅ Setup complete!"
