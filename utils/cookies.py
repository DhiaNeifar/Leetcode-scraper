import os
import browser_cookie3
import xml.etree.ElementTree as ET

class CookieManager:
    def __init__(self, logger, cookie_file="leetcode_cookies.xml"):
        self.logger = logger
        self.cookie_file = cookie_file

    def extract_cookies(self):
        try:
            cj = browser_cookie3.chrome(domain_name="leetcode.com")
            self.logger.info("Successfully extracted LeetCode cookies from Chrome.")
            return cj
        except Exception as e:
            self.logger.error(f"Failed to extract cookies: {e}")
            return None

    def save_cookies_to_xml(self, cj):
        root = ET.Element("cookies")
        for cookie in cj:
            if not cookie.name or not cookie.value:
                self.logger.warning(f"Skipping invalid cookie with missing name/value: {cookie}")
                continue

            item = ET.SubElement(root, "cookie")
            for attr in ["name", "value", "domain", "path", "secure", "expires"]:
                value = getattr(cookie, attr, "")
                ET.SubElement(item, attr).text = str(value)

        tree = ET.ElementTree(root)
        with open(self.cookie_file, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)
        self.logger.info(f"Cookies saved to {self.cookie_file} in XML format.")

    def load_cookies(self):
        if not os.path.exists(self.cookie_file):
            self.logger.warning("Cookie file does not exist. Trying to extract and save.")
            cj = self.extract_cookies()
            if cj:
                self.save_cookies_to_xml(cj)
                return True
            return False

        self.logger.info(f"Using existing cookie file: {self.cookie_file}")
        return True