#!/usr/bin/env python3
"""
LeetCode Submission Scraper Implementation

This module contains the core scraping functionality for extracting
LeetCode problem submissions and saving them as local files.

Author: Dhia Neifar
"""

import time
import re
import html
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, Set, Tuple, List, Optional, Any
from pathlib import Path
import xml.etree.ElementTree as ET
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager


class LeetCodeScraper:
    """
    Scraper for extracting LeetCode submissions and saving them locally.

    This class handles automated browsing of the LeetCode submissions page,
    extraction of accepted solutions, and saving them to the filesystem with
    organized filenames. It supports incremental scraping by tracking the
    last scrape timestamp.
    """

    def __init__(
            self,
            logger: logging.Logger,
            cookie_manager: Any,
            save_dir: str = "my-leetcode-solutions",
            state_file: str = ".lastscraped"
    ) -> None:
        """
        Initialize the LeetCode scraper with necessary components.

        Args:
            logger (logging.Logger): Logger instance for recording operations
            cookie_manager (Any): Cookie manager for authentication
            save_dir (str, optional): Directory to save solutions to. 
                                     Defaults to "my-leetcode-solutions".
            State_file (str, optional): File to store last scrape timestamp.
                                       Defaults to ".lastscraped".
        """
        self.logger: logging.Logger = logger
        self.cookie_manager: Any = cookie_manager
        self.save_dir: Path = Path(save_dir)
        self.state_file: Path = Path(state_file)

        # Track already saved submissions to avoid duplicates
        self.saved_keys: Set[Tuple[str, str]] = set()  # Set of (problem_id, language) tuples

        # Cache for problem metadata to avoid redundant lookups
        self.slug_to_id_title: Dict[str, Tuple[str, str]] = {}

        # WebDriver related attributes
        self.driver: Optional[webdriver.Chrome] = None
        self.main_window: Optional[str] = None

        # Load the last scrape timestamp
        self.last_scraped_time: Optional[datetime] = self.load_last_scraped_time()

    def load_last_scraped_time(self) -> Optional[datetime]:
        """
        Load the timestamp of the last successful scrape from the state file.

        Returns:
            Optional[datetime]: The last scrape timestamp if available, None otherwise
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as file:
                    timestamp_str = file.read().strip()
                    return datetime.fromisoformat(timestamp_str)
            except ValueError:
                self.logger.warning("Invalid timestamp format in state file. Starting fresh scrape.")
                return None
            except Exception as error:
                self.logger.error(f"Error reading last scrape time: {error}")
                return None

        self.logger.info("No previous scrape state found. Will scrape all available submissions.")
        return None

    def update_last_scraped_time(self) -> None:
        """
        Update the state file with the current timestamp after a successful scrape.
        """
        current_time = datetime.now()
        try:
            with open(self.state_file, "w") as file:
                file.write(current_time.isoformat())
            self.logger.info(f"Updated last scrape time: {current_time.isoformat()}")
        except Exception as error:
            self.logger.error(f"Failed to update scrape timestamp: {error}")

    def setup_driver(self) -> None:
        """
        Initialize and configure the Chrome WebDriver for scraping.

        This method sets up a Chrome browser instance with appropriate options
        for automated browsing, loads cookies for authentication, and navigates
        to the LeetCode submissions page.
        """
        self.logger.info("Setting up Chrome WebDriver...")

        # Configure Chrome options for headless operation
        options: Options = Options()
        options.add_argument('--window-position=2000,0')  # Position window off-screen
        options.add_argument('--start-minimized')  # Start minimized
        options.add_argument('--disable-gpu')  # Disable GPU acceleration
        options.add_argument('--no-sandbox')  # Required for some environments
        options.add_argument('--window-size=1920x1080')  # Set consistent window size

        # Initialize Chrome driver with configured options
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # Navigate to LeetCode home page
        self.driver.get("https://leetcode.com")
        time.sleep(2)  # Brief pause to ensure page loads

        # Store main window handle for navigation between tabs
        self.main_window = self.driver.current_window_handle

        # Load authentication cookies
        self.load_cookies()

    def load_cookies(self) -> None:
        """
        Load authentication cookies from the XML file into the WebDriver.

        Parses the cookie XML file and adds each cookie to the WebDriver session.
        Then navigates to the submissions page and waits for it to load.
        """
        try:
            # Parse cookies from XML file
            tree = ET.parse(self.cookie_manager.cookie_file)
            root = tree.getroot()

            # Add each cookie to the driver
            for cookie_elem in root.findall("cookie"):
                name_elem = cookie_elem.find("name")
                value_elem = cookie_elem.find("value")
                domain_elem = cookie_elem.find("domain")
                path_elem = cookie_elem.find("path")
                secure_elem = cookie_elem.find("secure")

                # Extract cookie values with proper null handling
                name = name_elem.text if name_elem is not None and name_elem.text else ""
                value = value_elem.text if value_elem is not None and value_elem.text else ""
                domain = domain_elem.text if domain_elem is not None and domain_elem.text else ""
                path = path_elem.text if path_elem is not None and path_elem.text else "/"
                secure_text = secure_elem.text if secure_elem is not None and secure_elem.text else "false"
                secure = secure_text.lower() == "true"

                # Skip invalid cookies
                if not name or not value:
                    self.logger.warning(f"Skipping invalid cookie: name={name}, value={value}")
                    continue

                # Create cookie dictionary and add to WebDriver
                cookie_dict = {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": path,
                    "secure": secure
                }
                self.driver.add_cookie(cookie_dict)

            self.logger.info("Cookies loaded into browser. Navigating to submissions page...")

            # Navigate to submissions page and wait for table to load
            self.driver.get("https://leetcode.com/submissions/")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
            )
            self.logger.info("Submission table loaded successfully.")

        except Exception as error:
            self.logger.error(f"Failed to load cookies: {error}")
            self.logger.error(f"Please check if user is logged in. Visit https://leetcode.com/ in Google Chrome.")
            raise

    def extract_code(self) -> str:
        """
        Extract submission code from the current submission page.

        Returns:
            str: The extracted code as a string, or empty string if extraction fails
        """
        try:
            # Get the page source and extract code using regex
            html_source = self.driver.page_source
            match = re.search(r"submissionCode:\s*'(.*?)',\s*\n", html_source, re.DOTALL)

            if not match:
                self.logger.warning("submissionCode not found in page source.")
                return ""

            # Get the raw code and decode it
            raw_code = match.group(1)
            decoded_code = html.unescape(raw_code.encode().decode("unicode_escape")).strip()
            return decoded_code

        except Exception as error:
            self.logger.error(f"Failed to extract code: {error}")
            return ""

    def extract_problem_id_and_title(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract problem ID and title from the problem page.

        Args:
            url (str): URL of the problem page

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing the problem ID 
                                                and title, or (None, None) if extraction fails
        """
        # Check cache first to avoid redundant lookups
        if url in self.slug_to_id_title:
            return self.slug_to_id_title[url]

        try:
            # Open problem page in a new tab
            self.driver.execute_script("window.open(arguments[0]);", url)
            time.sleep(1)  # Brief pause for tab to open

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)  # Wait for page to load

            # Extract problem ID and title using regex
            page_source = self.driver.page_source
            id_match = re.search(r'"questionFrontendId":"(\d+)"', page_source)
            title_match = re.search(r'"title":"([^"]+)"', page_source)

            # Close tab and switch back to main window
            self.driver.close()
            self.driver.switch_to.window(self.main_window)

            # Process extraction results
            if id_match and title_match:
                problem_id = id_match.group(1).zfill(4)  # Pad ID with leading zeros
                problem_title = title_match.group(1)

                # Cache the result for future lookups
                self.slug_to_id_title[url] = (problem_id, problem_title)
                return problem_id, problem_title
            else:
                self.logger.warning(f"Could not extract problem ID or title from {url}")
                return None, None

        except Exception as error:
            self.logger.error(f"Error extracting problem details: {error}")

            # Ensure we return to main window in case of error
            try:
                if self.driver.current_window_handle != self.main_window:
                    self.driver.close()
                    self.driver.switch_to.window(self.main_window)
            except:
                pass

            return None, None

    def save_solution(self, problem_id: str, title: str, language: str, code: str) -> None:
        """
        Save a solution to disk with a formatted filename.

        Args:
            problem_id (str): Problem ID (padded with zeros)
            title (str): Problem title
            language (str): Programming language of the solution
            code (str): Source code of the solution
        """
        # Map language identifier to file extension
        extension_map: Dict[str, str] = {
            "cpp": "cpp",
            "python3": "py",
            "c": "c",
            "java": "java",
            "javascript": "js",
            "typescript": "ts"
        }
        file_extension = extension_map.get(language, "txt")

        # Sanitize title for filename (replace invalid chars with underscores)
        sanitized_title = ''.join(
            c if c.isalnum() or c in ' -_.' else '_' for c in title
        )

        # Create filename with problem ID and title
        filename = f"{problem_id} - {sanitized_title}.{file_extension}"
        file_path = self.save_dir / filename

        # Write code to file
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(code)
            self.logger.info(f"Saved solution: {filename}")
        except Exception as error:
            self.logger.error(f"Failed to save solution '{filename}': {error}")

    def parse_relative_time(self, time_str: str) -> datetime:
        """
        Parse a relative time string (e.g., "2 hours ago") into a datetime object.

        Args:
            time_str (str): Relative time string from LeetCode's UI

        Returns:
            datetime: The calculated absolute datetime
        """
        # Normalize unicode spaces
        normalized_time_str = time_str.replace("\u00a0", " ")
        total_minutes = 0

        # Extract time values and units using regex
        matches = re.findall(r'(\d+)\s+(minute|hour|day|week|month|year)s?', normalized_time_str)

        if not matches:
            self.logger.warning(f"Could not parse relative time: \"{time_str}\"")
            # Default to current time if parsing fails
            return datetime.now()

        # Calculate total minutes based on each time unit
        for value_str, unit in matches:
            value = int(value_str)

            # Convert each unit to minutes
            if unit == "minute":
                total_minutes += value
            elif unit == "hour":
                total_minutes += value * 60
            elif unit == "day":
                total_minutes += value * 1440  # 24 * 60
            elif unit == "week":
                total_minutes += value * 10080  # 7 * 24 * 60
            elif unit == "month":
                total_minutes += value * 43800  # ~30 * 24 * 60
            elif unit == "year":
                total_minutes += value * 525600  # 365 * 24 * 60

        # Calculate absolute time by subtracting the delta from current time
        return datetime.now() - timedelta(minutes=total_minutes)

    def start(self) -> None:
        """
        Start the scraping process.

        This method orchestrates the entire scraping process:
        1. Sets up the WebDriver
        2. Iterates through submission pages
        3. Processes each submission row
        4. Extracts and saves accepted solutions
        5. Updates the last scrape timestamp
        """
        # Create the save directory if it doesn't exist
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the WebDriver
        self.setup_driver()

        # Track newest submission for updating the timestamp
        newest_timestamp: Optional[datetime] = None

        self.logger.info(f"Last scraped time: {self.last_scraped_time}")

        try:
            # Process submissions page by page
            while True:
                # Find all submission rows in the current page
                rows: List[WebElement] = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                self.logger.debug(f"Found {len(rows)} submission rows on current page")

                # Process each row (submission)
                for row in rows:
                    try:
                        # Extract columns
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) < 5:
                            self.logger.warning("Skipping row with insufficient columns.")
                            continue

                        # Extract and parse submission timestamp
                        timestamp_text_raw = cols[0].get_attribute("innerText").strip()
                        timestamp_text = unicodedata.normalize("NFKD", timestamp_text_raw).replace("\u00a0", " ")
                        timestamp_text = re.sub(r'\s+', ' ', timestamp_text).strip()

                        submission_time = self.parse_relative_time(timestamp_text)
                        self.logger.debug(
                            f"Row timestamp: \"{timestamp_text}\" parsed as {submission_time.isoformat()}")

                        # Stop if we've reached previously scraped submissions
                        if self.last_scraped_time and submission_time <= self.last_scraped_time:
                            self.logger.info("Reached previously scraped submissions. Stopping.")
                            self.driver.quit()
                            self.update_last_scraped_time()
                            return

                        # Extract submission details
                        question_elem = cols[1].find_element(By.TAG_NAME, "a")
                        problem_url = question_elem.get_attribute("href")
                        submission_link = cols[2].find_element(By.TAG_NAME, "a").get_attribute("href")
                        status = cols[2].text.strip()
                        language = cols[4].text.strip().lower()

                        # Track the newest submission timestamp
                        if not newest_timestamp or submission_time > newest_timestamp:
                            newest_timestamp = submission_time

                        # Only process accepted solutions in supported languages
                        supported_languages = ["cpp", "python3", "c", "java", "javascript", "typescript"]
                        if status != "Accepted" or language not in supported_languages:
                            continue

                        # Extract problem metadata
                        problem_id, problem_title = self.extract_problem_id_and_title(problem_url)
                        if not problem_id or not problem_title:
                            continue

                        # Skip if we've already saved this solution
                        solution_key = (problem_id, language)
                        if solution_key in self.saved_keys:
                            self.logger.info(f"Skipping duplicate submission for {problem_id} ({language})")
                            continue

                        # Navigate to the submission detail page
                        self.driver.execute_script("window.open(arguments[0]);", submission_link)
                        time.sleep(1)
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(2)

                        # Extract and save the code
                        code = self.extract_code()
                        if code:
                            self.save_solution(problem_id, problem_title, language, code)
                            self.saved_keys.add(solution_key)

                        # Close the submission detail tab and return to main window
                        self.driver.close()
                        self.driver.switch_to.window(self.main_window)
                        time.sleep(1)

                    except Exception as error:
                        self.logger.error(f"Error processing submission row: {error}")
                        # Ensure we're back at the main window in case of error
                        try:
                            if self.driver.current_window_handle != self.main_window:
                                self.driver.close()
                                self.driver.switch_to.window(self.main_window)
                        except Exception as window_error:
                            self.logger.critical(f"Error handling window recovery: {window_error}")
                            # If we can't get back to main window, exit
                            if self.driver:
                                self.driver.quit()
                            return

                # Try to navigate to next page if available
                try:
                    pager = self.driver.find_element(By.CSS_SELECTOR, ".lc-pager")
                    next_btn = pager.find_element(By.CLASS_NAME, "next")

                    # Check if there are more pages
                    if "disabled" in next_btn.get_attribute("class"):
                        self.logger.info("Reached last page of submissions.")
                        break

                    # Click next page button
                    link = next_btn.find_element(By.TAG_NAME, "a")
                    self.driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)  # Wait for page to load

                except Exception as navigation_error:
                    self.logger.info(f"No more pages or error navigating: {navigation_error}")
                    break

        finally:
            # Ensure cleanup happens even if errors occur
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

            # Update the last scrape timestamp
            self.update_last_scraped_time()