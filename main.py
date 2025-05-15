import argparse
from utils.cookies import CookieManager
from utils.scraper import LeetCodeScraper
from utils.logger import Logger

def parse_args():
    parser = argparse.ArgumentParser(description="Run LeetCode submission scraper.")
    parser.add_argument("save_dir", type=str, help="Directory to save scraped submissions")
    return parser.parse_args()

def main(save_dir):
    logger = Logger().get_logger()
    logger.info("Starting LeetCode Scraper")

    cookie_manager = CookieManager(logger)
    cookies_loaded = cookie_manager.load_cookies()

    if not cookies_loaded:
        logger.error("Cookies could not be loaded. Exiting.")
        return

    scraper = LeetCodeScraper(logger, cookie_manager, save_dir=save_dir)
    scraper.start()

    logger.info("Scraper finished successfully.")

if __name__ == "__main__":
    args = parse_args()
    main(args.save_dir)
