#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Launcher script for the AI Old Photo Restoration Tool.
This script checks if the environment is set up properly and runs the main application.
"""

import os
import subprocess
import sys


def check_environment():
    """Check if the environment is set up properly."""
    # Check if Real-ESRGAN directory exists
    if not os.path.exists("Real-ESRGAN"):
        print("Real-ESRGAN directory not found. Running setup...")
        run_setup()
        return
    
    # Check if required directories exist
    for directory in ["input", "output"]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created {directory} directory.")
    
    # Try importing required packages
    try:
        import ttkbootstrap
        import PIL
        import cv2
        import numpy
    except ImportError:
        print("Required packages not found. Running setup...")
        run_setup()
        return


def run_setup():
    """Run the setup script."""
    setup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup.py")
    
    if os.path.exists(setup_script):
        subprocess.call([sys.executable, setup_script])
    else:
        print("Setup script not found. Please run setup.py manually.")


def main():
    """Run the main application."""
    # Check environment first
    check_environment()
    
    # Run the main application
    main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    
    if os.path.exists(main_script):
        subprocess.call([sys.executable, main_script])
    else:
        print("Main script not found. Please check your installation.")


if __name__ == "__main__":
    main()
