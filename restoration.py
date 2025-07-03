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
import traceback
import time
from pathlib import Path

# Import the logger
from logger import logger


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
        
        Raises:
            Exception: If the restoration process fails
        """
        logger.info(f"Starting image restoration for: {input_path}")
        logger.info(f"Settings: model={model_name}, outscale={outscale}, face_enhance={face_enhance}")
        
        start_time = time.time()
        
        # Prepare paths
        input_path = os.path.abspath(input_path)
        output_dir = os.path.abspath(output_dir)
        
        # Validate input path
        if not os.path.exists(input_path):
            error_msg = f"Input path does not exist: {input_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Output directory: {output_dir}")
        
        # Check if Real-ESRGAN directory exists
        if not os.path.exists("Real-ESRGAN"):
            error_msg = "Real-ESRGAN directory not found. Please run setup first."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Store original directory to ensure we return to it
        original_dir = os.getcwd()
        
        try:
            # Change to Real-ESRGAN directory
            logger.debug("Changing to Real-ESRGAN directory")
            os.chdir("Real-ESRGAN")
            
            # Check if we're already in the depression environment
            in_conda_env = 'CONDA_DEFAULT_ENV' in os.environ and os.environ['CONDA_DEFAULT_ENV'] == 'depression'
            logger.debug(f"Running in 'depression' conda environment: {in_conda_env}")
            
            if in_conda_env:
                # Build command for direct execution
                cmd = [
                    "python", "inference_realesrgan.py",
                    "-n", model_name,
                    "-i", input_path,
                    "--outscale", str(outscale),
                    "-o", output_dir,
                    "--fp32",  # Use FP32 precision (may be more stable)
                    "--ext", "jpg"  # Force JPG extension
                ]
            else:
                # Build command to run through conda
                cmd = [
                    "conda", "run", "-n", "depression",
                    "python", "inference_realesrgan.py",
                    "-n", model_name,
                    "-i", input_path,
                    "--outscale", str(outscale),
                    "-o", output_dir,
                    "--fp32",  # Use FP32 precision (may be more stable)
                    "--ext", "jpg"  # Force JPG extension
                ]
            
            # Add face enhancement if requested
            if face_enhance:
                cmd.append("--face_enhance")
            
            # Log the command being executed
            logger.debug(f"Executing command: {' '.join(cmd)}")                # Run the command with timeout to prevent hanging
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
                
                # Log output for debugging
                if stdout:
                    logger.debug(f"Command stdout: {stdout.decode('utf-8', errors='replace')}")
                if stderr:
                    logger.debug(f"Command stderr: {stderr.decode('utf-8', errors='replace')}")
                
                if process.returncode != 0:
                    error_msg = f"Real-ESRGAN process failed with return code {process.returncode}: {stderr.decode('utf-8', errors='replace')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # List output directory to see if files were created
                output_files = os.listdir(output_dir)
                logger.debug(f"Files in output directory after processing: {output_files}")
                
                # Check the output file more thoroughly
                try:
                    import cv2
                    import numpy as np
                    
                    # For single file, determine output path
                    if not os.path.isdir(input_path):
                        input_filename = os.path.basename(input_path)
                        base_name, _ = os.path.splitext(input_filename)
                        
                        # Check both possible extensions
                        for ext in ['.jpg', '.png']:
                            possible_output = os.path.join(output_dir, f"{base_name}_out{ext}")
                            if os.path.exists(possible_output):
                                logger.debug(f"Found output file: {possible_output}")
                                # Check file integrity
                                img = cv2.imread(possible_output)
                                if img is None:
                                    logger.warning(f"OpenCV can't read the output file (None): {possible_output}")
                                else:
                                    h, w, c = img.shape
                                    min_val = np.min(img)
                                    max_val = np.max(img)
                                    logger.debug(f"Output image valid: {w}x{h}, {c} channels, range: {min_val}-{max_val}")
                                    # Try re-saving the image to ensure it's valid
                                    debug_path = os.path.join(output_dir, "debug_resaved.jpg")
                                    cv2.imwrite(debug_path, img)
                                    logger.debug(f"Re-saved image to: {debug_path}")
                except Exception as e:
                    logger.error(f"Error validating output file: {e}")
                
            except subprocess.TimeoutExpired:
                process.kill()
                error_msg = "Real-ESRGAN process timed out after 5 minutes"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Get the output filename
            if os.path.isdir(input_path):
                # For directory input, we'd need to track files before and after
                # For now, just return the output directory
                logger.info(f"Batch processing complete. Output directory: {output_dir}")
                logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")
                return output_dir
            else:
                # For single file, determine possible output paths
                input_filename = os.path.basename(input_path)
                base_name, _ = os.path.splitext(input_filename)
                
                # Real-ESRGAN may output as .png or .jpg
                possible_extensions = ['.png', '.jpg', '.jpeg']
                output_path = None
                
                # List the directory to check what files were created
                output_files = os.listdir(output_dir)
                logger.debug(f"Files in output directory after processing: {output_files}")
                
                # Try to find the output file with any of the possible extensions
                for ext in possible_extensions:
                    temp_output_filename = f"{base_name}_out{ext}"
                    temp_output_path = os.path.join(output_dir, temp_output_filename)
                    logger.debug(f"Checking for output file: {temp_output_path}")
                    if os.path.exists(temp_output_path):
                        output_path = temp_output_path
                        file_size = os.path.getsize(temp_output_path)
                        logger.debug(f"Found output file: {output_path} (Size: {file_size} bytes)")
                        
                        # Try to open the file to verify it's a valid image
                        try:
                            from PIL import Image
                            img = Image.open(temp_output_path)
                            img_size = img.size
                            img_mode = img.mode
                            logger.debug(f"Image successfully opened: {img_size}, {img_mode}")
                            img.close()
                        except Exception as img_err:
                            logger.error(f"Error opening output image: {str(img_err)}")
                        break
                
                # If no output file was found, raise an error
                if output_path is None:
                    # Check if there are any files in the output directory that contain the base name
                    matching_files = [f for f in output_files if base_name in f]
                    if matching_files:
                        # If there are matching files, use the first one
                        output_path = os.path.join(output_dir, matching_files[0])
                        logger.debug(f"Using closest match for output file: {output_path}")
                    else:
                        error_msg = f"Expected output file not found for input: {input_filename}"
                        logger.error(error_msg)
                        raise FileNotFoundError(error_msg)
                
                logger.info(f"Image restoration complete. Output: {output_path}")
                logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")
                return output_path
                
        except Exception as e:
            # Log the full exception with traceback
            logger.error(f"Error during image restoration: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise the exception to be handled by the caller
            raise
            
        finally:
            # Change back to original directory
            logger.debug(f"Changing back to original directory: {original_dir}")
            os.chdir(original_dir)
    
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
