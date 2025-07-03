#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for handling image restoration using Real-ESRGAN.
This module uses the 'depression' conda environment.
"""

import os
import subprocess
import uuid
import shutil
from pathlib import Path


class RestoreImage:
    """Class to handle image restoration using Real-ESRGAN."""
    
    def __init__(self):
        """Initialize the RestoreImage class."""
        # Check if Real-ESRGAN directory exists
        if not os.path.exists("Real-ESRGAN"):
            raise FileNotFoundError("Real-ESRGAN directory not found. Please run setup first.")
        
        # Create output directory if not exists
        os.makedirs("output", exist_ok=True)
        os.makedirs("input", exist_ok=True)

    def restore_image(self, input_path, output_dir="output", model_name="RealESRGAN_x4plus", 
                     outscale=2.0, face_enhance=True):
        """Restore an image using Real-ESRGAN.
        
        Args:
            input_path: Path to input image or directory
            output_dir: Directory to save output images
            model_name: Name of the Real-ESRGAN model to use
            outscale: Output scale factor
            face_enhance: Whether to enhance faces in the image
        
        Returns:
            Path to the output image
        """
        # Prepare paths
        input_path = os.path.abspath(input_path)
        output_dir = os.path.abspath(output_dir)
        
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Change to Real-ESRGAN directory
        os.chdir("Real-ESRGAN")
        
        try:
            # Check if we're already in the depression environment
            in_conda_env = 'CONDA_DEFAULT_ENV' in os.environ and os.environ['CONDA_DEFAULT_ENV'] == 'depression'
            
            if in_conda_env:
                # Build command for direct execution
                cmd = [
                    "python", "inference_realesrgan.py",
                    "-n", model_name,
                    "-i", input_path,
                    "--outscale", str(outscale),
                    "-o", output_dir
                ]
            else:
                # Build command to run through conda
                cmd = [
                    "conda", "run", "-n", "depression",
                    "python", "inference_realesrgan.py",
                    "-n", model_name,
                    "-i", input_path,
                    "--outscale", str(outscale),
                    "-o", output_dir
                ]
            
            # Add face enhancement if requested
            if face_enhance:
                cmd.append("--face_enhance")
            
            # Run the command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Real-ESRGAN process failed: {stderr.decode('utf-8')}")
            
            # Get the output filename
            if os.path.isdir(input_path):
                # For directory input, we'd need to track files before and after
                # For now, just return the output directory
                return output_dir
            else:
                # For single file, determine output path
                input_filename = os.path.basename(input_path)
                base_name, _ = os.path.splitext(input_filename)
                output_filename = f"{base_name}_out.png"  # Real-ESRGAN adds "_out" suffix
                output_path = os.path.join(output_dir, output_filename)
                
                # Verify output exists
                if not os.path.exists(output_path):
                    raise FileNotFoundError(f"Expected output file not found: {output_path}")
                
                return output_path
                
        finally:
            # Change back to original directory
            os.chdir("..")
    
    @staticmethod
    def get_supported_models():
        """Get list of supported models.
        
        Returns:
            List of supported model names
        """
        return [
            "RealESRGAN_x4plus",       # Default model, good for general use
            "RealESRGAN_x4plus_anime_6B",  # Specialized for anime/cartoon images
            # Add more models as they become available
        ]
