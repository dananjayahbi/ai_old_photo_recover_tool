#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the AI Old Photo Restoration Tool.
This script verifies that all dependencies are installed correctly.
"""

import os
import sys
import subprocess
import shutil


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
    """Check if required packages are installed in the conda environment."""
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
    
    # First check if conda and the environment are available
    if not shutil.which("conda"):
        print_status("Dependencies check", "SKIP")
        print("  Conda not found, skipping dependency check.")
        return False
    
    # Check for each package in the conda environment
    for module_name, package_name in dependencies.items():
        try:
            # Run a Python command in the conda environment to check for the package
            cmd = f"import {module_name}; print({module_name}.__name__)"
            result = subprocess.run(
                ["conda", "run", "-n", "depression", "python", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                print_status(f"Package {package_name}", "OK")
            else:
                raise ImportError()
                
        except (ImportError, subprocess.CalledProcessError):
            print_status(f"Package {package_name}", "FAIL")
            print(f"  Install with: conda run -n depression pip install {package_name}")
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


def check_conda_environment():
    """Check if conda is available and the 'depression' environment exists."""
    # Check if conda is installed
    if not shutil.which("conda"):
        print_status("Conda installation", "FAIL")
        print("  Conda not found in PATH. Please install Anaconda or Miniconda.")
        return False
    
    print_status("Conda installation", "OK")
    
    # Check if 'depression' environment exists
    try:
        result = subprocess.run(
            ["conda", "env", "list"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if "depression" not in result.stdout:
            print_status("Conda environment 'depression'", "FAIL")
            print("  The 'depression' conda environment was not found.")
            print("  Create it with: conda create -n depression python=3.8")
            return False
        
        print_status("Conda environment 'depression'", "OK")
        
        # Check if we can run commands in the environment
        try:
            subprocess.run(
                ["conda", "run", "-n", "depression", "python", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print_status("Conda environment access", "OK")
        except subprocess.CalledProcessError:
            print_status("Conda environment access", "FAIL")
            print("  Cannot run commands in the 'depression' environment.")
            return False
        
        return True
    except subprocess.CalledProcessError:
        print_status("Conda environment check", "FAIL")
        print("  Failed to list conda environments.")
        return False


def main():
    """Run all checks."""
    print("\nAI Old Photo Restoration Tool - System Check\n")
    
    python_ok = check_python_version()
    print()
    
    conda_ok = check_conda_environment()
    print()
    
    deps_ok = check_dependencies() if conda_ok else False
    print()
    
    esrgan_ok = check_real_esrgan()
    print()
    
    dirs_ok = check_directories()
    print()
    
    if python_ok and conda_ok and deps_ok and esrgan_ok and dirs_ok:
        print("All checks passed! The system is ready to run the application.")
        print("Run the application with: conda run -n depression python main.py")
    else:
        print("Some checks failed. Please fix the issues and run this script again.")
    
    print()


if __name__ == "__main__":
    main()
