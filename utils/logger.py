#!/usr/bin/env python3
"""
LeetCode Scraper Logger Module

This module provides a configurable logging facility for the LeetCode scraper with
both file and console output capabilities.

Author: Dhia Neifar
"""

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


class Logger:
    """
    Configurable dual-output logger for the LeetCode scraper.

    This class sets up a logger with both file and console handlers, enabling
    different verbosity levels for each output method. All logs are written to
    timestamped log files in the specified directory, while only INFO-level and
    higher messages are displayed in the console.
    """

    def __init__(self, log_dir: str = "runs") -> None:
        """
        Initialize the logger with file and console handlers.

        Args:
            log_dir (str, optional): Directory where log files will be stored.
                                    Defaults to "runs".
        """
        # Create the log directory if it doesn't exist
        log_directory: Path = Path(log_dir)
        log_directory.mkdir(parents=True, exist_ok=True)

        # Generate a timestamped log filename
        timestamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path: Path = log_directory / f"{timestamp}.log"

        # Configure the logger
        self.logger: logging.Logger = logging.getLogger("LeetCodeScraper")
        self.logger.setLevel(logging.DEBUG)  # Set base level to DEBUG (most verbose)

        # Prevent duplicate handlers if Logger is instantiated multiple times
        if not self.logger.handlers:
            self._configure_handlers(log_file_path)

        self.logger.debug(f"Logger initialized with file: {log_file_path}")

    def _configure_handlers(self, log_file_path: Path) -> None:
        """
        Configure and attach file and console handlers to the logger.

        Sets up two handlers:
        1. File handler: Captures all logs (DEBUG and above) to the log file
        2. Console handler: Shows only INFO and above messages to the console

        Args:
            log_file_path (Path): Path to the log file
        """
        # Create and configure file handler for detailed logging
        file_handler: logging.FileHandler = logging.FileHandler(
            str(log_file_path),
            mode='w'  # 'w' mode overwrites existing file
        )
        file_handler.setLevel(logging.DEBUG)  # Capture all logs in file

        # Create and configure console handler for important messages only
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Show only INFO+ logs in console

        # Create a formatter for consistent log message formatting
        log_formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # Apply formatter to both handlers
        file_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        # Attach handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        Returns:
            logging.Logger: The configured logger instance ready for use
        """
        return self.logger