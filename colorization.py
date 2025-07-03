#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for handling image colorization using DeOldify.
This module uses the 'depression' conda environment.
"""

import os
import traceback
import time
from pathlib import Path
import torch
import functools
import matplotlib.pyplot as plt
import warnings

# Import the logger
from logger import logger


class ColorizeImage:
    """Class to handle image colorization using DeOldify."""
    
    def __init__(self):
        """Initialize the ColorizeImage class."""
        # Check if DeOldify directory exists
        if not os.path.exists("DeOldify"):
            raise FileNotFoundError("DeOldify directory not found. Please run setup first.")
        
        # Create output directory if not exists
        os.makedirs("output", exist_ok=True)
        os.makedirs("input", exist_ok=True)

        # Path to add DeOldify to Python path
        self.deoldify_path = os.path.abspath("DeOldify")
        
        # The colorizer instance
        self.colorizer = None

    def _initialize_deoldify(self, artistic=True):
        """Initialize DeOldify colorizer if not already initialized.
        
        Args:
            artistic: Whether to use the artistic model (True) or stable model (False)
        """
        if self.colorizer is not None:
            return

        logger.info(f"Initializing DeOldify colorizer (artistic={artistic})")

        # Add DeOldify to path if not already
        import sys
        if self.deoldify_path not in sys.path:
            sys.path.insert(0, self.deoldify_path)
            
        # Create models directory in root if it doesn't exist
        models_dir = os.path.join(os.getcwd(), "models")
        os.makedirs(models_dir, exist_ok=True)
        
        # Check if model files need to be copied from DeOldify/models to the main models directory
        src_model_dir = os.path.join(self.deoldify_path, "models")
        model_name = "ColorizeArtistic_gen.pth" if artistic else "ColorizeStable_gen.pth"
        src_model_path = os.path.join(src_model_dir, model_name)
        dst_model_path = os.path.join(models_dir, model_name)
        
        # Copy the model file if it exists in DeOldify/models but not in the root models directory
        if os.path.exists(src_model_path) and not os.path.exists(dst_model_path):
            import shutil
            logger.info(f"Copying model file {model_name} to {models_dir}")
            shutil.copy2(src_model_path, dst_model_path)
            logger.info(f"Model file copied successfully")
        elif not os.path.exists(src_model_path) and not os.path.exists(dst_model_path):
            logger.error(f"Model file {model_name} not found in {src_model_dir}")
            logger.error("Please download the model files and place them in the DeOldify/models directory")
            raise FileNotFoundError(f"DeOldify model file {model_name} not found")

        # Need to set device first before importing other DeOldify modules
        from deoldify import device
        from deoldify.device_id import DeviceId

        # Check if CUDA is available
        if torch.cuda.is_available():
            logger.info("CUDA is available. Using GPU.")
            device.set(device=DeviceId.GPU0)
        else:
            logger.info("CUDA not available. Using CPU.")
            device.set(device=DeviceId.CPU)
        
        # Fix for PyTorch 2.6+ model loading issue by patching torch.load
        original_torch_load = torch.load
        torch.load = functools.partial(original_torch_load, weights_only=False)

        # Now import DeOldify visualization
        from deoldify.visualize import get_image_colorizer

        # Configure matplotlib and PyTorch
        plt.style.use('dark_background')
        torch.backends.cudnn.benchmark = True
        warnings.filterwarnings("ignore", category=UserWarning, message=".*?Your .*? set is empty.*?")

        # Create the colorizer instance
        self.colorizer = get_image_colorizer(artistic=artistic)
        logger.info("DeOldify colorizer initialized successfully")

    def colorize_image(self, input_path, artistic=True, render_factor=35, output_dir="output"):
        """Colorize an image using DeOldify.
        
        Args:
            input_path: Path to input image
            artistic: Whether to use artistic model (True) or stable model (False)
            render_factor: Render factor for colorization (higher = better quality but slower)
            output_dir: Directory to save output images
        
        Returns:
            Path to the output image
        
        Raises:
            Exception: If the colorization process fails
        """
        logger.info(f"Starting image colorization for: {input_path}")
        logger.info(f"Settings: artistic={artistic}, render_factor={render_factor}")
        
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
        
        # Store original directory to ensure we return to it
        original_dir = os.getcwd()
        
        try:
            # Initialize DeOldify if not already initialized
            self._initialize_deoldify(artistic=artistic)
            
            # Generate output path
            input_filename = os.path.basename(input_path)
            base_name, ext = os.path.splitext(input_filename)
            output_filename = f"{base_name}_colorized.png"
            output_path = os.path.join(output_dir, output_filename)
            
            # Run colorization
            logger.debug(f"Running colorization with render_factor={render_factor}")
            result_path = self.colorizer.plot_transformed_image(
                path=input_path,
                render_factor=render_factor,
                compare=False
            )
            
            # Copy result to our output directory if needed
            if result_path != output_path:
                import shutil
                logger.debug(f"Copying result from {result_path} to {output_path}")
                shutil.copy(result_path, output_path)
            
            # Verify output exists
            if not os.path.exists(output_path):
                error_msg = f"Expected output file not found: {output_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            logger.info(f"Image colorization complete. Output: {output_path}")
            logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")
            return output_path
                
        except Exception as e:
            # Log the full exception with traceback
            logger.error(f"Error during image colorization: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise the exception to be handled by the caller
            raise
            
        finally:
            # Change back to original directory if needed
            if os.getcwd() != original_dir:
                logger.debug(f"Changing back to original directory: {original_dir}")
                os.chdir(original_dir)
    
    @staticmethod
    def get_supported_render_factors():
        """Get list of supported render factors.
        
        Returns:
            List of supported render factor values
        """
        return list(range(10, 46, 5))  # 10, 15, 20, 25, 30, 35, 40, 45
