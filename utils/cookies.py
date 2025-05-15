#!/usr/bin/env python3
"""
LeetCode Cookie Manager Module

This module handles the extraction, storage, and loading of browser cookies
for authentication with LeetCode.

Author: Dhia Neifar
"""

import os
import logging
from typing import Optional, Any, Dict, List
import browser_cookie3
import xml.etree.ElementTree as ET
from http.cookiejar import CookieJar


class CookieManager:
    """
    Manages browser cookies for LeetCode authentication.

    This class provides functionality to extract cookies from Chrome browser,
    save them to an XML file, and load them for use in authenticated requests.
    """

    def __init__(self, logger: logging.Logger, cookie_file: str = "leetcode_cookies.xml") -> None:
        """
        Initialize the CookieManager with a logger and cookie file path.

        Args:
            logger (logging.Logger): Logger instance for recording operations
            cookie_file (str, optional): Path to the XML file for storing cookies.
                                         Defaults to "leetcode_cookies.xml".
        """
        self.logger: logging.Logger = logger
        self.cookie_file: str = cookie_file

    def extract_cookies(self) -> Optional[CookieJar]:
        """
        Extract LeetCode cookies from the Chrome browser.

        Attempts to retrieve cookies specifically for the leetcode.com domain
        using the browser_cookie3 library.

        Returns:
            Optional[CookieJar]: Cookie jar containing LeetCode cookies if successful,
                                 None otherwise.
        """
        try:
            cookie_jar: CookieJar = browser_cookie3.chrome(domain_name="leetcode.com")
            self.logger.info("Successfully extracted LeetCode cookies from Chrome browser.")
            return cookie_jar
        except Exception as error:
            self.logger.error(f"Failed to extract cookies: {error}")
            return None

    def save_cookies_to_xml(self, cookie_jar: CookieJar) -> bool:
        """
        Save cookies from a cookie jar to an XML file.

        Creates an XML structure to store cookie attributes including
        name, value, domain, path, secure flag, and expiration.

        Args:
            cookie_jar (CookieJar): The cookie jar containing cookies to save

        Returns:
            bool: True if cookies were successfully saved, False otherwise
        """
        try:
            # Create XML root element
            root = ET.Element("cookies")

            # Add each cookie as a child element with attributes
            for cookie in cookie_jar:
                # Skip invalid cookies
                if not cookie.name or not cookie.value:
                    self.logger.warning(
                        f"Skipping invalid cookie with missing name/value: {cookie}"
                    )
                    continue

                # Create cookie element
                cookie_element = ET.SubElement(root, "cookie")

                # Add cookie attributes
                cookie_attributes = ["name", "value", "domain", "path", "secure", "expires"]
                for attribute in cookie_attributes:
                    attribute_value = getattr(cookie, attribute, "")
                    ET.SubElement(cookie_element, attribute).text = str(attribute_value)

            # Write XML to file
            tree = ET.ElementTree(root)
            with open(self.cookie_file, "wb") as file:
                tree.write(file, encoding="utf-8", xml_declaration=True)

            self.logger.info(f"Cookies successfully saved to {self.cookie_file} in XML format.")
            return True

        except Exception as error:
            self.logger.error(f"Failed to save cookies to XML: {error}")
            return False

    def load_cookies(self) -> bool:
        """
        Load cookies from XML file or extract from browser if file doesn't exist.

        Checks if the cookie file exists. If not, tries to extract cookies from
        the browser and save them. If the file exists, assumes cookies are valid.

        Returns:
            bool: True if cookies are available (either loaded or freshly extracted),
                  False if cookies couldn't be obtained
        """
        if not os.path.exists(self.cookie_file):
            self.logger.warning(f"Cookie file {self.cookie_file} does not exist. Attempting to extract fresh cookies.")
            cookie_jar = self.extract_cookies()

            if cookie_jar:
                save_result = self.save_cookies_to_xml(cookie_jar)
                return save_result

            self.logger.error("Failed to obtain cookies from browser. Authentication will likely fail.")
            return False

        self.logger.info(f"Using existing cookie file: {self.cookie_file}")
        # In a more robust implementation, we might want to validate the cookies here
        # (e.g., check expiration dates or attempt a test request)
        return True

    def get_cookies_dict(self) -> Dict[str, str]:
        """
        Convert stored cookies to a dictionary format for use in requests.

        Reads the cookie XML file and constructs a dictionary of cookie name-value pairs.

        Returns:
            Dict[str, str]: Dictionary of cookie name-value pairs
                           Empty dictionary if cookies cannot be loaded

        Note: This is a placeholder implementation. In a real implementation,
              you would parse the XML file and extract the actual cookies.
        """
        cookies_dict: Dict[str, str] = {}

        if not os.path.exists(self.cookie_file):
            self.logger.error("Cookie file does not exist. Cannot get cookies dictionary.")
            return cookies_dict

        try:
            tree = ET.parse(self.cookie_file)
            root = tree.getroot()

            for cookie_elem in root.findall("cookie"):
                name_elem = cookie_elem.find("name")
                value_elem = cookie_elem.find("value")

                if name_elem is not None and name_elem.text and value_elem is not None and value_elem.text:
                    cookies_dict[name_elem.text] = value_elem.text

            return cookies_dict

        except Exception as error:
            self.logger.error(f"Error parsing cookie file: {error}")
            return {}