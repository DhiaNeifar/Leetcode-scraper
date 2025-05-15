import logging
import os

class Logger:
    def __init__(self, log_file: str = "scraper.log"):
        self.logger = logging.getLogger("LeetCodeScraper")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            # Create log directory if needed
            os.makedirs(os.path.dirname(log_file), exist_ok=True) if os.path.dirname(log_file) else None

            # File handler
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)

            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            # Add handlers
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def get_logger(self):
        return self.logger