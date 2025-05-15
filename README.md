# 📘 LeetCode Scraper

**LeetCode Scraper** is a Python automation tool that logs into your LeetCode account, extracts your **Accepted** solutions, and saves them locally using a standardized filename format based on the problem ID and title. If new solutions are found, they are automatically committed and pushed to your GitHub repository.

---

## 🔧 Features

- ✅ Scrapes accepted submissions only  
- ✅ Saves code with clean filenames: `0326 - Power of Three.py`  
- ✅ Supports multiple languages (`Python3`, `C++`, `C`)  
- ✅ Avoids duplicates by tracking previously saved problems  
- ✅ Automatically commits and pushes new solutions to GitHub  
- ✅ (Planned) Background scraping without opening a visible browser  
- ✅ (Planned) Incremental scraping: skips already processed submissions  

---

## ⚙️ How It Works

This project is designed to work in **three stages**:

1. **Manual Login Required**  
   The user must log into LeetCode manually and export their session cookies. This is necessary because programmatic login is often blocked by LeetCode.

2. **Scheduled Execution (User-Cron)**  
   You are encouraged to schedule this script to run automatically (e.g., every hour) using tools like:
   - `cron` on Linux/macOS
   - Task Scheduler on Windows

3. **Smart Incremental Scraping (Planned)**  
   - On the **first run**, the script scrapes *all* your accepted submissions.
   - On **subsequent runs**, it will detect the last time it ran and only scrape **newer** submissions.

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

## 🚀 Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/<your-username>/leetcode-scraper.git
cd leetcode-scraper
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Export your LeetCode cookies

Manually export your LeetCode session cookies and save them in a file named:

```
leetcode_cookies.txt
```

> You can use a browser extension like **EditThisCookie** to export your cookies.

---

## 📁 Output

Your solutions will be saved in the `solutions/` directory using the following format:

```
0326 - Power of Three.py
```

Each new solution will:
- Replace any older version with the same title/language
- Trigger a Git commit and push (if configured)

---

## 🔄 Git Auto-Push

This project detects newly added solutions and automatically pushes them to your GitHub repository. Ensure you have:

```bash
git remote add origin https://github.com/<your-username>/leetcode-scraper.git
```

and that your local `git` is authenticated (e.g., using SSH or a GitHub token).

---

## 🧠 Notes

- This tool uses Selenium and requires Google Chrome.
- You **must be logged in** using cookies.
- The scraper paginates through all accepted submissions.
- A headless version (runs without a visible browser window) is planned.
- A persistent cache of previously scraped submissions will be added to improve performance on future runs.

---

## 📦 Dependencies

```
selenium
webdriver-manager
```

---

## 📄 License

This project is licensed under the MIT License.
