#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Launcher script for the AI Old Photo Restoration Tool.
This script checks if the environment is set up properly and runs the main application.
"""

import os
import subprocess
import sys
import shutil


def check_environment():
    """Check if the environment is set up properly."""
    # Check if conda is available
    if not shutil.which("conda"):
        print("Conda not found in PATH. Please install Anaconda or Miniconda.")
        return
    
    # Check if 'depression' conda environment exists
    try:
        result = subprocess.run(
            ["conda", "env", "list"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if "depression" not in result.stdout:
            print("The 'depression' conda environment was not found. Running setup...")
            run_setup()
            return
    except subprocess.CalledProcessError:
        print("Failed to check conda environments. Running setup...")
        run_setup()
        return
    
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
    
    # We're using the conda environment, so we don't need to try importing here
    # Just assume everything is set up correctly if we've made it this far


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
    
    # Run the main application using the conda environment
    main_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    
    if os.path.exists(main_script):
        print("Starting AI Old Photo Restoration Tool with conda environment 'depression'...")
        subprocess.call(["conda", "run", "-n", "depression", "python", main_script])
    else:
        print("Main script not found. Please check your installation.")


if __name__ == "__main__":
    main()
