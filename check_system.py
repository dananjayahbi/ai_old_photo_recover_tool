#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the AI Old Photo Restoration Tool.
This script verifies that all dependencies are installed correctly.
"""

import os
import sys


def print_status(message, status):
    """Print a status message with color.
    
    Args:
        message: The message to print
        status: 'OK', 'FAIL', or 'WARN'
    """
    if status == 'OK':
        print(f"[  \033[92mOK\033[0m  ] {message}")
    elif status == 'FAIL':
        print(f"[ \033[91mFAIL\033[0m ] {message}")
    elif status == 'WARN':
        print(f"[ \033[93mWARN\033[0m ] {message}")
    else:
        print(f"[ {status} ] {message}")


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print_status(f"Python version: {sys.version}", "OK")
        return True
    else:
        print_status(f"Python version: {sys.version}", "FAIL")
        print("  Python 3.7 or higher is required.")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    dependencies = {
        "numpy": "numpy",
        "PIL": "pillow",
        "cv2": "opencv-python",
        "ttkbootstrap": "ttkbootstrap",
        "torch": "torch",
        "torchvision": "torchvision",
        "basicsr": "basicsr",
        "facexlib": "facexlib",
        "gfpgan": "gfpgan"
    }
    
    all_installed = True
    
    for module_name, package_name in dependencies.items():
        try:
            __import__(module_name)
            print_status(f"Package {package_name}", "OK")
        except ImportError:
            print_status(f"Package {package_name}", "FAIL")
            print(f"  Install with: pip install {package_name}")
            all_installed = False
    
    return all_installed


def check_real_esrgan():
    """Check if Real-ESRGAN is properly set up."""
    if not os.path.exists("Real-ESRGAN"):
        print_status("Real-ESRGAN repository", "FAIL")
        print("  Clone with: git clone https://github.com/xinntao/Real-ESRGAN.git")
        return False
    
    print_status("Real-ESRGAN repository", "OK")
    
    # Check if setup.py exists in the Real-ESRGAN directory
    if not os.path.exists(os.path.join("Real-ESRGAN", "setup.py")):
        print_status("Real-ESRGAN setup.py", "FAIL")
        print("  Real-ESRGAN repository may be incomplete.")
        return False
    
    print_status("Real-ESRGAN setup.py", "OK")
    return True


def check_directories():
    """Check if required directories exist."""
    directories = ["input", "output"]
    all_exist = True
    
    for directory in directories:
        if not os.path.exists(directory):
            print_status(f"Directory {directory}/", "WARN")
            print(f"  Creating {directory}/ directory.")
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"  Failed to create directory: {str(e)}")
                all_exist = False
        else:
            print_status(f"Directory {directory}/", "OK")
    
    return all_exist


def main():
    """Run all checks."""
    print("\nAI Old Photo Restoration Tool - System Check\n")
    
    python_ok = check_python_version()
    print()
    
    deps_ok = check_dependencies()
    print()
    
    esrgan_ok = check_real_esrgan()
    print()
    
    dirs_ok = check_directories()
    print()
    
    if python_ok and deps_ok and esrgan_ok and dirs_ok:
        print("All checks passed! The system is ready to run the application.")
        print("Run the application with: python main.py")
    else:
        print("Some checks failed. Please fix the issues and run this script again.")
    
    print()


if __name__ == "__main__":
    main()
