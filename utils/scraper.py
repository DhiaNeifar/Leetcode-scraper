import os
import time
import re
import html
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import xml.etree.ElementTree as ET

class LeetCodeScraper:
    def __init__(self, logger, cookie_manager, save_dir="my-leetcode-solutions", state_file=".lastscraped"):
        self.logger = logger
        self.cookie_manager = cookie_manager
        self.save_dir = save_dir
        self.state_file = state_file
        self.saved_files = {}  # (pid, lang) -> datetime
        self.slug_to_id_title = {}
        self.last_scraped_time = self.load_last_scraped_time()

    def load_last_scraped_time(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                try:
                    return datetime.fromisoformat(f.read().strip())
                except ValueError:
                    self.logger.warning("Invalid timestamp in .lastscraped. Ignoring.")
        return None

    def update_last_scraped_time(self):
        with open(self.state_file, "w") as f:
            f.write(datetime.now().isoformat())
        self.logger.info(f"Updated last scrape time: {datetime.now().isoformat()}")

    def setup_driver(self):
        options = Options()
        options.add_argument('--window-position=2000,0')
        options.add_argument('--start-minimized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.get("https://leetcode.com")
        time.sleep(2)
        self.main_window = self.driver.current_window_handle
        self.load_cookies()

    def load_cookies(self):
        tree = ET.parse(self.cookie_manager.cookie_file)
        root = tree.getroot()
        for cookie in root.findall("cookie"):
            name = cookie.find("name").text or ""
            value = cookie.find("value").text or ""
            domain = cookie.find("domain").text or ""
            path = cookie.find("path").text or "/"
            secure = (cookie.find("secure").text or "false").lower() == "true"

            if not name or not value:
                self.logger.warning(f"Skipping invalid cookie: name={name}, value={value}")
                continue

            cookie_dict = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "secure": secure
            }
            self.driver.add_cookie(cookie_dict)

        self.logger.info("Cookies loaded into browser.")
        self.driver.get("https://leetcode.com/submissions/")
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
        self.logger.info("Submission table loaded.")

    def extract_code(self):
        try:
            html_source = self.driver.page_source
            match = re.search(r"submissionCode:\s*'(.*?)',\s*\n", html_source, re.DOTALL)
            if not match:
                self.logger.warning("submissionCode not found.")
                return ""
            raw_code = match.group(1)
            return html.unescape(raw_code.encode().decode("unicode_escape")).strip()
        except Exception as e:
            self.logger.error(f"Failed to extract code: {e}")
            return ""

    def extract_problem_id_and_title(self, url):
        if url in self.slug_to_id_title:
            return self.slug_to_id_title[url]

        self.driver.execute_script("window.open(arguments[0]);", url)
        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(2)
        page = self.driver.page_source
        id_match = re.search(r'"questionFrontendId":"(\d+)"', page)
        title_match = re.search(r'"title":"([^"]+)"', page)
        self.driver.close()
        self.driver.switch_to.window(self.main_window)

        if id_match and title_match:
            pid = id_match.group(1).zfill(4)
            title = title_match.group(1)
            self.slug_to_id_title[url] = (pid, title)
            return pid, title
        else:
            self.logger.warning(f"Could not extract ID/title from {url}")
            return None, None

    def save_solution(self, pid, title, lang, code):
        ext = {"cpp": "cpp", "python3": "py", "c": "c"}.get(lang, "txt")
        fname = f"{pid} - {''.join(c if c.isalnum() or c in ' -_.' else '_' for c in title)}.{ext}"
        path = os.path.join(self.save_dir, fname)

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        self.logger.info(f"Saved: {fname}")

    def parse_relative_time(self, time_str):
        time_str = time_str.replace("\u00a0", " ")
        total_minutes = 0

        match = re.findall(r'(\d+)\s+(minute|hour|day|week|month|year)s?', time_str)
        if not match:
            self.logger.warning(f"Could not parse timestamp: \"{time_str}\"")

        for value, unit in match:
            value = int(value)
            if unit == "minute":
                total_minutes += value
            elif unit == "hour":
                total_minutes += value * 60
            elif unit == "day":
                total_minutes += value * 1440
            elif unit == "week":
                total_minutes += value * 10080
            elif unit == "month":
                total_minutes += value * 43800
            elif unit == "year":
                total_minutes += value * 525600

        return datetime.now() - timedelta(minutes=total_minutes)

    def start(self):
        os.makedirs(self.save_dir, exist_ok=True)
        self.setup_driver()
        newest_timestamp = None

        self.logger.info(f"Last scraped time: {self.last_scraped_time}")

        while True:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            self.logger.debug(f"Found {len(rows)} submission rows")

            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 5:
                        self.logger.warning("Skipping row with insufficient columns.")
                        continue

                    timestamp_text = cols[0].get_attribute("innerText").strip()
                    submission_time = self.parse_relative_time(timestamp_text)
                    self.logger.debug(f"Row timestamp: \"{timestamp_text}\" parsed as {submission_time.isoformat()}")

                    if self.last_scraped_time and submission_time <= self.last_scraped_time:
                        self.logger.info("Reached previously scraped submissions. Stopping.")
                        self.driver.quit()
                        self.update_last_scraped_time()
                        return

                    question_elem = cols[1].find_element(By.TAG_NAME, "a")
                    problem_url = question_elem.get_attribute("href")
                    submission_link = cols[2].find_element(By.TAG_NAME, "a").get_attribute("href")
                    status = cols[2].text.strip()
                    lang = cols[4].text.strip()

                    if not newest_timestamp or submission_time > newest_timestamp:
                        newest_timestamp = submission_time

                    if status != "Accepted" or lang not in ["cpp", "python3", "c"]:
                        continue

                    pid, title = self.extract_problem_id_and_title(problem_url)
                    if not pid or not title:
                        continue

                    # Only save if newer than what we already stored for (pid, lang)
                    if (pid, lang) in self.saved_files and submission_time <= self.saved_files[(pid, lang)]:
                        self.logger.info(f"Skipping older or duplicate submission for {pid} ({lang})")
                        continue

                    self.driver.execute_script("window.open(arguments[0]);", submission_link)
                    time.sleep(1)
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    time.sleep(2)

                    code = self.extract_code()
                    if code:
                        self.save_solution(pid, title, lang, code)
                        self.saved_files[(pid, lang)] = submission_time

                    self.driver.close()
                    self.driver.switch_to.window(self.main_window)
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Error processing row: {e}")
                    try:
                        if self.driver.current_window_handle != self.main_window:
                            self.driver.close()
                            self.driver.switch_to.window(self.main_window)
                    except:
                        self.logger.critical("Main window closed. Exiting.")
                        self.driver.quit()
                        return

            try:
                pager = self.driver.find_element(By.CSS_SELECTOR, ".lc-pager")
                next_btn = pager.find_element(By.CLASS_NAME, "next")
                if "disabled" in next_btn.get_attribute("class"):
                    break
                link = next_btn.find_element(By.TAG_NAME, "a")
                self.driver.execute_script("arguments[0].click();", link)
                time.sleep(3)
            except:
                break

        self.driver.quit()
        self.update_last_scraped_time()
