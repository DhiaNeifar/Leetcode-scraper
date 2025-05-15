#!/usr/bin/env python3
"""
LeetCode Submission Scraper

This script automates the process of scraping programming submissions from LeetCode.
It handles authentication via cookies and exports submissions to a specified directory.

Author: Dhia Neifar
Version: 1.0.0
"""

import argparse
from typing import Dict, Any, Optional
from pathlib import Path

from utils.cookies import CookieManager
from utils.scraper import LeetCodeScraper
from utils.logger import Logger


def parse_command_line_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the scraper.

    Returns:
        argparse.Namespace: An object containing all parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="LeetCode Submission Scraper - Export your LeetCode submissions to local files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "save_dir",
        type=str,
        help="Directory path where scraped submissions will be saved"
    )

    return parser.parse_args()


def main(output_directory: str) -> None:
    """
    Main entry point for the LeetCode submission scraper.

    This function initializes the logger, loads authentication cookies,
    and starts the scraping process if authentication is successful.

    Args:
        output_directory (str): Path to directory where submissions will be saved

    Returns:
        None
    """
    # Initialize logging
    logger_instance = Logger()
    logger = logger_instance.get_logger()
    logger.info("Starting LeetCode Submission Scraper")

    # Convert string path to Path object
    output_path = Path(output_directory)

    # Create output directory if it doesn't exist
    if not output_path.exists():
        logger.info(f"Creating output directory: {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)

    # Initialize cookie manager and load authentication cookies
    cookie_manager = CookieManager(logger)
    authentication_successful = cookie_manager.load_cookies()

    if not authentication_successful:
        logger.error("Authentication failed: Cookies could not be loaded. Exiting.")
        return

    # Initialize and run the scraper
    submission_scraper = LeetCodeScraper(
        logger=logger,
        cookie_manager=cookie_manager,
        save_dir=str(output_path)
    )

    submission_scraper.start()
    logger.info("Scraper finished successfully.")


if __name__ == "__main__":
    args = parse_command_line_arguments()
    main(args.save_dir)