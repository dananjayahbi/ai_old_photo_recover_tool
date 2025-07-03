#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logger module for the AI Old Photo Restoration Tool.
This module provides logging functionality for the application.
"""

import os
import logging
import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Set up logger
def setup_logger(name="ai_photo_restore"):
    """
    Set up and configure a logger.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create file handler
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file = logs_dir / f"{name}_{current_date}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create main logger instance
logger = setup_logger()

def get_log_file_path():
    """
    Get the path to the current log file.
    
    Returns:
        Path to the log file
    """
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    return os.path.abspath(os.path.join("logs", f"ai_photo_restore_{current_date}.log"))
