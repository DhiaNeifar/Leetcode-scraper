import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, log_dir: str = "runs"):
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"{timestamp}.log")

        self.logger = logging.getLogger("LeetCodeScraper")
        self.logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers in case of re-instantiation
        if not self.logger.handlers:
            fh = logging.FileHandler(log_file, mode='w')
            fh.setLevel(logging.DEBUG)

            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        self.logger.debug(f"Logger initialized with file: {log_file}")

    def get_logger(self):
        return self.logger
