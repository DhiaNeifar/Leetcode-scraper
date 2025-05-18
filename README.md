# 📘 LeetCode Scraper

**LeetCode Scraper** is a Python automation tool that logs into your LeetCode account using saved cookies, scrapes your **Accepted** submissions, and saves them locally. The scraped solutions are automatically committed and pushed to a GitHub repository of your choice.

---

## 🔧 Features

- ✅ Scrapes only **Accepted** LeetCode submissions
- ✅ Saves code with clean, descriptive filenames: `0326 - Power of Three.py`
- ✅ Supports multiple languages: `Python3`, `C++`, `C`
- ✅ Avoids duplicates by tracking saved submissions
- ✅ Automatically commits and pushes changes to GitHub
- ✅ **Headless execution** using `xvfb-run` (runs without showing browser windows)
- ✅ Persistent logging: each run generates a new log file saved in the `runs/` folder
- ✅ Setup script handles everything from environment setup to automation

---

## 🧱 Motivation

This project was created as a personal alternative to popular but limited/free tools like:

- ❌ LeetHub
- ❌ LeetSync
- ❌ leetcode-cli

These tools either:
- Required third-party authentication and access to your GitHub repositories, or
- Simply did not work as expected in real-world usage.

LeetCode Scraper avoids all of this by:
- Running locally with **zero external dependencies**
- Giving **you full control** over your credentials and repositories
- Being easy to extend, understand, and trust

---

## ⚙️ How It Works

### 🔹 `install.sh` Script

The `install.sh` script is your entrypoint. It:

1. Creates a Python virtual environment (if not already created)
2. Installs all Python dependencies from `requirements.txt`
3. Prompts the user to log into LeetCode manually in Chrome
4. Clones your GitHub repository to store solutions
5. Runs the scraper using `xvfb-run` to hide the browser
6. Commits and pushes new submissions to GitHub
7. Optionally sets up a recurring job using `cron`

### 🔹 Logging with `runs/`
- All logs are stored under the `runs/` folder
- Each run generates a timestamped log file (e.g., `runs/2025-05-14T21:12:00.log`)
- Make sure `runs/` is in your `.gitignore`

### 🔹 Cookie Management
- The `utils/cookies.py` script handles exporting and formatting cookies
- Cookies are saved to `leetcode_cookies.xml`
- **Never share this file** — it gives full access to your LeetCode account

---

## 🚀 Getting Started

### 1. Clone this Repository
```bash
git clone https://github.com/your-username/leetcode-scraper.git
cd leetcode-scraper
```

### 2. Run the Setup Script
```bash
bash setup.sh
```

The script will:
- Set up the environment
- Ask for your GitHub repo URL
- Ask for a GitHub token
- Run the scraper
- Commit and push your submissions to GitHub

---

## 🔑 Setting Up Your GitHub Token

1. Visit: [GitHub Token Settings](https://github.com/settings/tokens)
2. Click **Generate new token (fine-grained)**
3. Choose the repository you want to give access to
4. Enable permissions:
   - **Contents** → ✅ Read and Write
   - **Metadata** → ✅ Required (default)
5. Copy the token and paste it when `setup.sh` prompts you

> The token is saved to `.scraper_config` and is **not shared with anyone**

---

## 🧠 How It Works Internally

### 🔸 `main.py`
- Parses the folder where submissions will be saved
- Loads cookies and invokes the `LeetCodeScraper` class

### 🔸 `utils/scraper.py`
- Uses Selenium and ChromeDriver to browse LeetCode
- Visits `/submissions/`, parses each row, extracts accepted solutions
- Downloads code using `submissionCode` and saves it in the repo folder
- Tracks `(problem_id, language)` pairs to avoid duplicates
- Stops when it hits a submission older than `.lastscraped`

### 🔸 `.scraper_config`
This file saves:
- Your GitHub repo URL
- Your personal GitHub token

### 🔸 `.lastscraped`
- Stores the timestamp of the most recent scrape
- Ensures next run only scrapes *newer* submissions

---

## ⏱️ Automating Scrapes with `cron`
After running `setup.sh`, you can choose to auto-run the scraper every X minutes/hours/days.

### Example Prompt:
```bash
🕐 Run how often? Choose: [m]inutes, [h]ours, [d]ays: h
Enter frequency number (e.g., every 2 hours = 2): 2
```
This sets up a `cron` job to run the scraper **every 2 hours**.

### 🔻 How to View or Remove Cron Jobs
```bash
crontab -l       # Show all cron jobs
crontab -e       # Edit cron jobs (delete the scraper line to stop it)
```

> Cron jobs won’t run while your machine is off. They resume on next uptime.

---

## 📁 Output
Submissions are saved under your GitHub repo in this format:
```
0326 - Power of Three.py
0697 - Degree of an Array.cpp
```

They are committed and pushed automatically.

---

## 📦 Dependencies
```
selenium
webdriver-manager
undetected-chromedriver
```

---

## 🔒 Security Reminder
- Do NOT commit your `leetcode_cookies.xml` file
- Make sure your `.gitignore` includes:
```
leetcode_cookies.xml
.scraper_config
runs/
```

---

## 📄 License
MIT License
