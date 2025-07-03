#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple tool to check the Real-ESRGAN installation.
This script verifies that Real-ESRGAN is installed correctly.
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def check_realesrgan():
    """Check if Real-ESRGAN is installed correctly."""
    print("Checking Real-ESRGAN installation...")
    
    # Check if Real-ESRGAN directory exists
    if not os.path.exists("Real-ESRGAN"):
        print("❌ Error: Real-ESRGAN directory not found.")
        print("   Please run setup.py to install Real-ESRGAN.")
        return False
    
    # Check if conda is available
    if not shutil.which("conda"):
        print("❌ Error: Conda not found in PATH.")
        print("   Please install Anaconda or Miniconda.")
        return False
    
    # Check if 'depression' environment exists
    try:
        result = subprocess.run(
            ["conda", "env", "list"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if "depression" not in result.stdout:
            print("❌ Error: The 'depression' conda environment was not found.")
            print("   Please create it with: conda create -n depression python=3.8")
            return False
        
        print("✅ Found 'depression' conda environment!")
        
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to list conda environments.")
        return False
    
    # Check if required packages are installed
    print("\nChecking required packages in 'depression' environment...")
    required_packages = [
        "basicsr", "facexlib", "gfpgan", "torch", "numpy", "opencv-python", "pillow"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Check if package is installed
            result = subprocess.run(
                ["conda", "run", "-n", "depression", "pip", "list"],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            # For opencv-python, also check for opencv
            if package == "opencv-python":
                if "opencv-python" not in result.stdout and "opencv" not in result.stdout:
                    missing_packages.append(package)
            # For pillow, also check for PIL
            elif package == "pillow":
                if "pillow" not in result.stdout.lower() and "pil" not in result.stdout.lower():
                    missing_packages.append(package)
            else:
                if package not in result.stdout.lower():
                    missing_packages.append(package)
                
        except subprocess.CalledProcessError:
            print(f"⚠️ Warning: Failed to check if {package} is installed.")
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ The following packages are missing:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease run setup.py to install the missing packages.")
        return False
    
    print("✅ All required packages are installed!")
    
    # Try to run a simple inference command to verify Real-ESRGAN works
    print("\nTesting Real-ESRGAN...")
    
    # Create a small test image
    test_dir = Path("test_realesrgan")
    test_dir.mkdir(exist_ok=True)
    test_image = test_dir / "test.png"
    
    # Create a small test image if it doesn't exist
    if not test_image.exists():
        try:
            import numpy as np
            from PIL import Image
            
            # Create a small black and white image
            img = np.zeros((64, 64, 3), dtype=np.uint8)
            img[16:48, 16:48] = 255  # White square in the middle
            Image.fromarray(img).save(test_image)
            
            print(f"✅ Created test image: {test_image}")
        except Exception as e:
            print(f"❌ Error creating test image: {e}")
            return False
    
    # Change to Real-ESRGAN directory
    original_dir = os.getcwd()
    os.chdir("Real-ESRGAN")
    
    try:
        # Run a simple inference command
        print("Running test inference...")
        result = subprocess.run(
            ["conda", "run", "-n", "depression", "python", "inference_realesrgan.py", 
             "-n", "RealESRGAN_x4plus", "-i", str(Path("..") / test_dir / "test.png"),
             "-o", str(Path("..") / test_dir), "--outscale", "2"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # 1-minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ Error running Real-ESRGAN: {result.stderr}")
            return False
        
        # Check if output file exists
        output_file = Path("..") / test_dir / "test_out.png"
        if not os.path.exists(output_file):
            print(f"❌ Error: Output file not found: {output_file}")
            return False
        
        print(f"✅ Real-ESRGAN test successful! Output file: {output_file}")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Error: Real-ESRGAN inference timed out after 60 seconds.")
        return False
    except Exception as e:
        print(f"❌ Error testing Real-ESRGAN: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    if check_realesrgan():
        print("\n✅ Real-ESRGAN is installed and working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Real-ESRGAN installation has issues. Please run setup.py to fix them.")
        sys.exit(1)
