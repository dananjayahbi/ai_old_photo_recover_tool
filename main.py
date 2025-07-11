#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the AI Old Photo Restoration Tool.
This application uses the 'depression' conda environment.
"""

import os
import sys
import threading
import time
import shutil
import subprocess
import traceback
from pathlib import Path
from tkinter import filedialog

# Import the logger first to set it up before anything else
try:
    from logger import logger, get_log_file_path
    logger.info("Starting AI Old Photo Restoration Tool")
except Exception as e:
    print(f"Failed to initialize logger: {e}")
    # Set up a basic logger if the custom logger fails
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ai_photo_restore_fallback")
    logger.warning("Using fallback logger due to initialization error")

# Check if running within the depression conda environment
def is_in_conda_env():
    """Check if we're running inside the conda environment."""
    return 'CONDA_DEFAULT_ENV' in os.environ and os.environ['CONDA_DEFAULT_ENV'] == 'depression'

# If not in the correct environment, try to restart in it
if not is_in_conda_env():
    if shutil.which('conda'):
        print("Restarting in 'depression' conda environment...")
        try:
            subprocess.call(['conda', 'run', '-n', 'depression', 'python'] + sys.argv)
            sys.exit(0)
        except Exception as e:
            print(f"Failed to restart in conda environment: {e}")
            sys.exit(1)
    else:
        print("Conda not found. Please run with: conda run -n depression python main.py")
        sys.exit(1)

# Now we're sure we're in the right environment, import everything else
import cv2
import numpy as np
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from restoration import RestoreImage
from colorization import ColorizeImage


class PhotoRestorationApp:
    """Main application class for the Old Photo Restoration Tool."""
    
    def __init__(self, root):
        """Initialize the application.
        
        Args:
            root: The root Tk window
        """
        self.root = root
        self.root.title("AI Old Photo Restoration Tool")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set icon
        # self.root.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
        
        # Instance variables
        self.input_path = None
        self.output_path = None
        self.current_input_image = None
        self.current_output_image = None
        self.restorer = RestoreImage()
        self.colorizer = ColorizeImage()
        
        # Processing mode: 'restore' or 'colorize'
        self.processing_mode = 'restore'
        
        # Zoom and pan variables for comparison view
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_x = 0
        self.last_y = 0
        
        # Build the interface
        self.create_menu()
        self.create_main_frame()
        
        # Check if Real-ESRGAN repository exists
        if not os.path.exists("Real-ESRGAN"):
            self.check_esrgan_dialog()

    def check_esrgan_dialog(self):
        """Show a dialog to check/clone Real-ESRGAN repository."""
        result = Messagebox.yesno(
            "Real-ESRGAN Not Found", 
            "Real-ESRGAN repository is required but not found. Would you like to download it now?",
            parent=self.root
        )
        
        if result == "Yes":
            self.clone_esrgan_repo()
        else:
            Messagebox.show_error(
                "Required Dependency Missing", 
                "The application cannot run without Real-ESRGAN.",
                parent=self.root
            )
            self.root.quit()

    def clone_esrgan_repo(self):
        """Clone the Real-ESRGAN repository."""
        progress = ttk.Toplevel(self.root)
        progress.title("Downloading Real-ESRGAN")
        progress.geometry("400x150")
        
        ttk.Label(progress, text="Downloading and setting up Real-ESRGAN...", 
                 font=("Helvetica", 12)).pack(pady=10)
        
        pb = ttk.Progressbar(progress, bootstyle="success", mode="indeterminate")
        pb.pack(fill=X, padx=20, pady=10)
        pb.start(10)
        
        status_var = ttk.StringVar(value="Cloning repository...")
        status_label = ttk.Label(progress, textvariable=status_var)
        status_label.pack(pady=5)
        
        def setup_thread():
            try:
                # Clone the repository
                status_var.set("Cloning Real-ESRGAN repository...")
                os.system("git clone https://github.com/xinntao/Real-ESRGAN.git")
                
                # Install requirements
                status_var.set("Installing dependencies...")
                os.system("pip install basicsr")
                os.system("pip install facexlib")
                os.system("pip install gfpgan")
                os.chdir("Real-ESRGAN")
                os.system("pip install -r requirements.txt")
                os.system("python setup.py develop")
                os.chdir("..")
                
                # Complete
                status_var.set("Setup completed successfully!")
                time.sleep(1)
                progress.destroy()
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
                time.sleep(3)
                progress.destroy()
                Messagebox.show_error("Setup Failed", f"Failed to set up Real-ESRGAN: {str(e)}")
        
        threading.Thread(target=setup_thread, daemon=True).start()

    def create_menu(self):
        """Create the application menu."""
        menu = ttk.Menu(self.root)
        self.root.config(menu=menu)
        
        # File menu
        file_menu = ttk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.open_image)
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = ttk.Menu(menu, tearoff=0)
        menu.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        
        # Help menu
        help_menu = ttk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="View Logs", command=self.open_log_file)
        
        # Bind keyboard shortcuts
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())  # Also bind to = key (same key as + without shift)
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())

    def create_main_frame(self):
        """Create the main application frame and widgets."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_container, text="Controls", padding=10)
        control_frame.pack(side=LEFT, fill=Y, padx=(0, 10))
        
        # Input section
        input_section = ttk.LabelFrame(control_frame, text="Input", padding=10)
        input_section.pack(fill=X, pady=(0, 10))
        
        ttk.Button(
            input_section, 
            text="Open Image", 
            bootstyle="primary", 
            command=self.open_image
        ).pack(fill=X, pady=(0, 5))
        
        ttk.Button(
            input_section, 
            text="Open Folder", 
            bootstyle="secondary", 
            command=self.open_folder
        ).pack(fill=X)
        
        # Processing mode selection
        mode_section = ttk.LabelFrame(control_frame, text="Processing Mode", padding=10)
        mode_section.pack(fill=X, pady=(0, 10))
        
        self.mode_var = ttk.StringVar(value="restore")
        
        def on_mode_change():
            selected_mode = self.mode_var.get()
            self.processing_mode = selected_mode
            
            # Show/hide appropriate settings based on mode
            if selected_mode == "restore":
                restoration_settings_frame.pack(fill=X, pady=(0, 10))
                colorization_settings_frame.pack_forget()
            else:  # colorize
                restoration_settings_frame.pack_forget()
                colorization_settings_frame.pack(fill=X, pady=(0, 10))
        
        # Restoration mode option
        ttk.Radiobutton(
            mode_section,
            text="Restore Image (Super Resolution)",
            variable=self.mode_var,
            value="restore",
            bootstyle="primary-toolbutton",
            command=on_mode_change
        ).pack(fill=X, pady=(0, 5))
        
        # Colorization mode option
        ttk.Radiobutton(
            mode_section,
            text="Colorize Black & White Image",
            variable=self.mode_var,
            value="colorize",
            bootstyle="success-toolbutton",
            command=on_mode_change
        ).pack(fill=X)
        
        # Restoration Settings
        restoration_settings_frame = ttk.LabelFrame(control_frame, text="Restoration Settings", padding=10)
        restoration_settings_frame.pack(fill=X, pady=(0, 10))
        
        # Scale factor setting
        scale_frame = ttk.Frame(restoration_settings_frame)
        scale_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(scale_frame, text="Scale Factor:").pack(side=LEFT)
        
        self.scale_var = ttk.DoubleVar(value=2.0)
        scale_cb = ttk.Spinbox(
            scale_frame, 
            from_=1.0, 
            to=4.0, 
            increment=0.5, 
            textvariable=self.scale_var,
            width=5
        )
        scale_cb.pack(side=RIGHT)
        
        # Face enhancement option
        self.face_enhance_var = ttk.BooleanVar(value=True)
        face_enhance_cb = ttk.Checkbutton(
            restoration_settings_frame, 
            text="Enhance Faces", 
            variable=self.face_enhance_var,
            bootstyle="round-toggle"
        )
        face_enhance_cb.pack(fill=X, pady=(0, 10))
        
        # Model selection
        model_frame = ttk.Frame(restoration_settings_frame)
        model_frame.pack(fill=X)
        ttk.Label(model_frame, text="Model:").pack(side=LEFT)
        
        self.model_var = ttk.StringVar(value="RealESRGAN_x4plus")
        model_cb = ttk.Combobox(
            model_frame, 
            values=["RealESRGAN_x4plus", "RealESRGAN_x4plus_anime_6B"], 
            textvariable=self.model_var,
            state="readonly",
            width=20
        )
        model_cb.pack(side=RIGHT)
        
        # Colorization Settings
        colorization_settings_frame = ttk.LabelFrame(control_frame, text="Colorization Settings", padding=10)
        # Don't pack this initially - only show when colorize mode is selected
        
        # Artistic mode option
        self.artistic_var = ttk.BooleanVar(value=True)
        artistic_cb = ttk.Checkbutton(
            colorization_settings_frame, 
            text="Artistic Mode", 
            variable=self.artistic_var,
            bootstyle="round-toggle"
        )
        artistic_cb.pack(fill=X, pady=(0, 10))
        
        # Render factor setting
        render_frame = ttk.Frame(colorization_settings_frame)
        render_frame.pack(fill=X)
        ttk.Label(render_frame, text="Render Quality:").pack(side=LEFT)
        
        self.render_var = ttk.IntVar(value=35)
        render_cb = ttk.Combobox(
            render_frame, 
            values=[10, 15, 20, 25, 30, 35, 40, 45], 
            textvariable=self.render_var,
            state="readonly",
            width=5
        )
        render_cb.pack(side=RIGHT)
        
        # Process section
        process_section = ttk.LabelFrame(control_frame, text="Process", padding=10)
        process_section.pack(fill=X, pady=(0, 10))
        
        self.process_button = ttk.Button(
            process_section, 
            text="Process Image", 
            bootstyle="success", 
            command=self.process_image
        )
        self.process_button.pack(fill=X, pady=(0, 5))
        
        self.batch_button = ttk.Button(
            process_section, 
            text="Batch Process", 
            bootstyle="info", 
            command=self.batch_process
        )
        self.batch_button.pack(fill=X)
        
        # Status section
        status_section = ttk.LabelFrame(control_frame, text="Status", padding=10)
        status_section.pack(fill=X)
        
        self.status_var = ttk.StringVar(value="Ready")
        ttk.Label(status_section, textvariable=self.status_var).pack(fill=X)
        
        self.progress = ttk.Progressbar(status_section, bootstyle="success")
        self.progress.pack(fill=X, pady=(5, 0))
        
        # Right panel - Image display
        image_frame = ttk.Frame(main_container)
        image_frame.pack(side=RIGHT, fill=BOTH, expand=YES)
        
        # Create a notebook for before/after views
        self.view_notebook = ttk.Notebook(image_frame)
        self.view_notebook.pack(fill=BOTH, expand=YES)
        
        # Before tab
        self.before_frame = ttk.Frame(self.view_notebook)
        self.view_notebook.add(self.before_frame, text="Before")
        
        # After tab
        self.after_frame = ttk.Frame(self.view_notebook)
        self.view_notebook.add(self.after_frame, text="After")
        
        # Compare tab
        self.compare_frame = ttk.Frame(self.view_notebook)
        self.view_notebook.add(self.compare_frame, text="Compare")
        
        # Controls frame for comparison view
        self.compare_controls = ttk.Frame(self.compare_frame)
        self.compare_controls.pack(side=TOP, fill=X, pady=(5, 0), padx=5)
        
        # Zoom controls
        zoom_label = ttk.Label(self.compare_controls, text="Zoom:")
        zoom_label.pack(side=LEFT, padx=(0, 5))
        
        self.zoom_out_btn = ttk.Button(
            self.compare_controls, 
            text="−", 
            width=3, 
            bootstyle="secondary-outline",
            command=self.zoom_out
        )
        self.zoom_out_btn.pack(side=LEFT)
        
        self.zoom_level_var = ttk.StringVar(value="100%")
        zoom_level_label = ttk.Label(self.compare_controls, textvariable=self.zoom_level_var, width=6)
        zoom_level_label.pack(side=LEFT, padx=5)
        
        self.zoom_in_btn = ttk.Button(
            self.compare_controls, 
            text="+", 
            width=3, 
            bootstyle="secondary-outline",
            command=self.zoom_in
        )
        self.zoom_in_btn.pack(side=LEFT)
        
        self.reset_zoom_btn = ttk.Button(
            self.compare_controls, 
            text="Reset View", 
            bootstyle="secondary",
            command=self.reset_zoom
        )
        self.reset_zoom_btn.pack(side=LEFT, padx=10)
        
        # Create canvases for images
        self.before_canvas = ttk.Canvas(self.before_frame, background="#f0f0f0")
        self.before_canvas.pack(fill=BOTH, expand=YES)
        # Bind canvas resize event
        self.before_canvas.bind("<Configure>", lambda e, canvas=self.before_canvas: self.on_canvas_resize(e, canvas))
        
        self.after_canvas = ttk.Canvas(self.after_frame, background="#f0f0f0")
        self.after_canvas.pack(fill=BOTH, expand=YES)
        # Bind canvas resize event
        self.after_canvas.bind("<Configure>", lambda e, canvas=self.after_canvas: self.on_canvas_resize(e, canvas))
        
        # Split view for comparison
        self.compare_canvas = ttk.Canvas(self.compare_frame, background="#f0f0f0", cursor="hand2")
        self.compare_canvas.pack(fill=BOTH, expand=YES)
        # Bind canvas resize event
        self.compare_canvas.bind("<Configure>", lambda e, canvas=self.compare_canvas: self.on_canvas_resize(e, canvas))
        
        # Bind mouse wheel for zooming
        self.compare_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.compare_canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.compare_canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        
        # Bind mouse events for panning
        self.compare_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.compare_canvas.bind("<B1-Motion>", self.pan_image)
        self.compare_canvas.bind("<ButtonRelease-1>", self.stop_pan)
        
        # Default message when no image is loaded
        self.show_canvas_message(self.before_canvas, "No image loaded. Use 'Open Image' to load a photo.")
        self.show_canvas_message(self.after_canvas, "Restored image will appear here after processing.")
        self.show_canvas_message(
            self.compare_canvas, 
            "Comparison view will be available after restoration.\n\n"
            "Zoom Controls:\n"
            "• Use the zoom buttons above\n"
            "• Mouse wheel to zoom in/out\n"
            "• Ctrl++ or Ctrl+- keyboard shortcuts\n"
            "• Click and drag to pan when zoomed in"
        )

    def on_canvas_resize(self, event, canvas):
        """Handle canvas resize events to keep images centered.
        
        Args:
            event: The resize event
            canvas: The canvas being resized
        """
        # If canvas has an image, recenter it
        if hasattr(canvas, 'image') and canvas.image:
            # Get the current image
            photo = canvas.image
            
            # Center the image using the updated canvas dimensions
            x = event.width // 2
            y = event.height // 2
            
            # Clear and redraw the image centered
            canvas.delete("all")
            canvas.create_image(x, y, anchor=CENTER, image=photo)
        elif hasattr(canvas, 'original_image') and canvas.original_image:
            # We have the original image but it needs to be redisplayed
            # (this handles cases where window was resized but the image wasn't showing)
            if canvas == self.compare_canvas:
                # Use zoomed display for comparison view
                self.display_comparison_with_zoom()
            else:
                # Regular display for other canvases
                self.display_image(canvas, canvas.original_image)
        else:
            # Just show the default message
            if canvas == self.before_canvas:
                self.show_canvas_message(canvas, "No image loaded. Use 'Open Image' to load a photo.")
            elif canvas == self.after_canvas:
                self.show_canvas_message(canvas, "Restored image will appear here after processing.")
            else:
                self.show_canvas_message(canvas, "Comparison view will be available after restoration.")

    def show_canvas_message(self, canvas, message):
        """Show a message on the canvas when no image is displayed.
        
        Args:
            canvas: The canvas to show the message on
            message: The message to display
        """
        canvas.delete("all")
        canvas.create_text(
            canvas.winfo_width() / 2 or 400, 
            canvas.winfo_height() / 2 or 300,
            text=message,
            fill="gray",
            font=("Helvetica", 14)
        )

    def open_image(self):
        """Open a single image file."""
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.input_path = file_path
            self.load_image(file_path)
            self.status_var.set(f"Loaded: {os.path.basename(file_path)}")

    def open_folder(self):
        """Open a folder with multiple images."""
        folder_path = filedialog.askdirectory(title="Select folder with images")
        
        if folder_path:
            # Check if the folder contains valid images
            valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
            image_files = [f for f in os.listdir(folder_path) 
                           if os.path.isfile(os.path.join(folder_path, f)) 
                           and f.lower().endswith(valid_extensions)]
            
            if not image_files:
                Messagebox.show_warning(
                    "No Images Found", 
                    "The selected folder does not contain any supported image files.",
                    parent=self.root
                )
                return
            
            # Load the first image
            self.input_path = folder_path
            first_image = os.path.join(folder_path, image_files[0])
            self.load_image(first_image)
            self.status_var.set(f"Loaded folder with {len(image_files)} images.")

    def load_image(self, image_path):
        """Load and display an image on the before canvas.
        
        Args:
            image_path: Path to the image file
        """
        try:
            # Load image with PIL for better compatibility
            image = Image.open(image_path)
            self.current_input_image = image.copy()
            
            # Store image information for resize handling
            self.before_canvas.original_image = self.current_input_image
            
            # Resize for display if needed
            self.display_image(self.before_canvas, image)
            
            # Reset the after canvas
            self.show_canvas_message(self.after_canvas, "Restored image will appear here after processing.")
            self.show_canvas_message(self.compare_canvas, "Comparison view will be available after restoration.")
            
            # Switch to Before tab
            self.view_notebook.select(0)
            
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to load image: {str(e)}", parent=self.root)
            self.status_var.set("Error loading image.")

    def display_image(self, canvas, image):
        """Display an image on the specified canvas, properly scaled.
        
        Args:
            canvas: The canvas to display the image on
            image: PIL Image object to display
        """
        try:
            canvas.delete("all")
            
            # Verify image is valid
            if image is None:
                self.show_canvas_message(canvas, "No image to display")
                return
                
            # Force load the image to catch errors early
            image.load()
            
            # Check image dimensions
            img_width, img_height = image.size
            if img_width <= 0 or img_height <= 0:
                self.show_canvas_message(canvas, f"Invalid image dimensions: {image.size}")
                logger.error(f"Cannot display image with invalid dimensions: {image.size}")
                return
            
            # Get canvas dimensions
            canvas_width = canvas.winfo_width() or 800
            canvas_height = canvas.winfo_height() or 600
            
            # Calculate scale to fit image in canvas
            scale = min(canvas_width / max(img_width, 1), canvas_height / max(img_height, 1))
            
            # Scale image
            try:
                if scale < 1:
                    new_width = max(int(img_width * scale), 1)
                    new_height = max(int(img_height * scale), 1)
                    display_image = image.resize((new_width, new_height), Image.LANCZOS)
                else:
                    display_image = image
            except Exception as resize_err:
                logger.error(f"Error resizing image: {resize_err}, trying simpler resize method")
                # Fallback to simpler resize method
                if scale < 1:
                    new_width = max(int(img_width * scale), 1)
                    new_height = max(int(img_height * scale), 1)
                    display_image = image.resize((new_width, new_height), Image.NEAREST)
                else:
                    display_image = image
            
            # Convert to PhotoImage for tkinter
            try:
                photo = ImageTk.PhotoImage(display_image)
                
                # Keep a reference to prevent garbage collection
                canvas.image = photo
                
                # Center the image using the CENTER anchor
                x = canvas_width // 2
                y = canvas_height // 2
                
                # Display the image centered in the canvas
                canvas.create_image(x, y, anchor=CENTER, image=photo)
            except Exception as img_err:
                logger.error(f"Error creating PhotoImage: {img_err}")
                self.show_canvas_message(canvas, f"Error displaying image: {str(img_err)}")
                
        except Exception as e:
            logger.error(f"Error in display_image: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.show_canvas_message(canvas, f"Error displaying image: {str(e)}")

    def process_image(self):
        """Process the current image based on selected mode (restore or colorize)."""
        if self.input_path is None or self.current_input_image is None:
            Messagebox.show_warning("No Image", "Please open an image first.", parent=self.root)
            return
        
        # Update UI based on selected mode
        mode = self.processing_mode
        if mode == "restore":
            self.status_var.set("Restoring image...")
        else:
            self.status_var.set("Colorizing image...")
            
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        
        # Create a thread to run the process
        def process_thread():
            try:
                # Save input to temp if it's not a file
                input_path = self.input_path
                if os.path.isdir(input_path):
                    # Assuming self.current_input_image is already loaded
                    temp_input = os.path.join("input", "temp_input.png")
                    os.makedirs("input", exist_ok=True)
                    self.current_input_image.save(temp_input)
                    input_path = temp_input
                
                # Process based on selected mode
                if mode == "restore":
                    # Get restoration parameters
                    scale = self.scale_var.get()
                    face_enhance = self.face_enhance_var.get()
                    model_name = self.model_var.get()
                    
                    logger.debug(f"Restoring with parameters: model={model_name}, scale={scale}, face_enhance={face_enhance}")
                    
                    # Process with Real-ESRGAN
                    output_path = self.restorer.restore_image(
                        input_path,
                        model_name=model_name,
                        outscale=scale,
                        face_enhance=face_enhance
                    )
                else:
                    # Get colorization parameters
                    artistic = self.artistic_var.get()
                    render_factor = self.render_var.get()
                    
                    logger.debug(f"Colorizing with parameters: artistic={artistic}, render_factor={render_factor}")
                    
                    # Process with DeOldify
                    output_path = self.colorizer.colorize_image(
                        input_path,
                        artistic=artistic,
                        render_factor=render_factor
                    )
                
                # Update UI in the main thread
                self.root.after(0, lambda: self.display_result(output_path))
            
            except Exception as e:
                # Log the full exception with traceback
                error_message = str(e)
                logger.error(f"Error during single image processing: {error_message}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Handle errors in the main thread
                self.root.after(0, lambda error=error_message: self.handle_process_error(error))
        
        # Start the processing thread
        threading.Thread(target=process_thread, daemon=True).start()

    def display_result(self, output_path):
        """Display the processed image result.
        
        Args:
            output_path: Path to the output image file
        """
        self.progress.stop()
        self.progress.configure(mode="determinate", value=100)
        self.status_var.set("Processing completed.")
        
        try:
            # Load the output image
            output_image = Image.open(output_path)
            self.current_output_image = output_image.copy()
            self.output_path = output_path
            
            # Store image information for resize handling
            self.after_canvas.original_image = self.current_output_image
            
            # Display in After tab
            self.display_image(self.after_canvas, output_image)
            
            # Create comparison view
            self.create_comparison_view()
            
            # Switch to After tab
            self.view_notebook.select(1)
        
        except Exception as e:
            logger.error(f"Failed to load result: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            Messagebox.show_error("Error", f"Failed to load result: {str(e)}", parent=self.root)
            self.status_var.set("Error displaying result.")

    def handle_process_error(self, error_message):
        """Handle errors from the processing thread.
        
        Args:
            error_message: Error message to display
        """
        logger.error(f"Image processing error: {error_message}")
        
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status_var.set("Processing failed.")
        
        # Create a more detailed error message with log file information
        log_file_path = get_log_file_path()
        error_details = (
            f"Failed to process image: {error_message}\n\n"
            f"See the log file for more details:\n{log_file_path}\n\n"
            "Would you like to open the log file now?"
        )
        
        # Show error dialog with option to open log
        response = Messagebox.show_error(
            title="Processing Error", 
            message=error_details, 
            parent=self.root
        )
        
        # Ask if user wants to open log file in a separate dialog
        if Messagebox.yesno("View Log File", "Would you like to open the log file now?") == "Yes":
            self.open_log_file(log_file_path)

    def create_comparison_view(self):
        """Create a side-by-side comparison of before and after images."""
        if self.current_input_image is None or self.current_output_image is None:
            return
        
        try:
            # Create a new image with both before and after
            input_img = self.current_input_image.copy()
            output_img = self.current_output_image.copy()
            
            # Resize output to match input dimensions for fair comparison
            output_img = output_img.resize(input_img.size, Image.LANCZOS)
            
            # Create a combined image
            total_width = input_img.width * 2
            comparison = Image.new('RGB', (total_width, input_img.height))
            comparison.paste(input_img, (0, 0))
            comparison.paste(output_img, (input_img.width, 0))
            
            # Reset zoom and pan when creating a new comparison
            self.zoom_level = 1.0
            self.pan_x = 0
            self.pan_y = 0
            self._update_zoom_level_display()
            
            # Store comparison image for resize handling
            self.compare_canvas.original_image = comparison.copy()
            
            # Display in Compare tab with zoom support
            self.display_comparison_with_zoom()
        except Exception as e:
            logger.error(f"Error creating comparison view: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.show_canvas_message(self.compare_canvas, f"Error creating comparison: {str(e)}")

    def batch_process(self):
        """Process multiple images in a folder."""
        if not self.input_path or not os.path.isdir(self.input_path):
            Messagebox.show_warning(
                "No Folder Selected", 
                "Please select a folder with images first.",
                parent=self.root
            )
            return
        
        # Get output folder
        output_folder = filedialog.askdirectory(
            title="Select output folder for restored images"
        )
        
        if not output_folder:
            return
        
        # Get valid image files
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
        image_files = [f for f in os.listdir(self.input_path) 
                      if os.path.isfile(os.path.join(self.input_path, f)) 
                      and f.lower().endswith(valid_extensions)]
        
        if not image_files:
            Messagebox.show_warning(
                "No Images", 
                "No supported image files found in the selected folder.",
                parent=self.root
            )
            return
        
        # Create progress dialog
        progress_window = ttk.Toplevel(self.root)
        progress_window.title("Batch Processing")
        progress_window.geometry("400x200")
        
        ttk.Label(
            progress_window, 
            text=f"Processing {len(image_files)} images...", 
            font=("Helvetica", 12)
        ).pack(pady=10)
        
        progress_var = ttk.IntVar(value=0)
        progress_bar = ttk.Progressbar(
            progress_window, 
            variable=progress_var, 
            maximum=len(image_files),
            bootstyle="success"
        )
        progress_bar.pack(fill=X, padx=20, pady=10)
        
        current_file_var = ttk.StringVar(value="Starting...")
        ttk.Label(progress_window, textvariable=current_file_var).pack(pady=5)
        
        # Get parameters
        scale = self.scale_var.get()
        face_enhance = self.face_enhance_var.get()
        model_name = self.model_var.get()
        
        # Create cancel button and flag
        cancel_flag = {"cancelled": False}
        
        def cancel_batch():
            cancel_flag["cancelled"] = True
            current_file_var.set("Cancelling...")
        
        ttk.Button(
            progress_window, 
            text="Cancel", 
            command=cancel_batch, 
            bootstyle="danger"
        ).pack(pady=10)
        
        # Batch processing function
        def batch_thread():
            processed = 0
            errors = []
            
            for i, filename in enumerate(image_files):
                if cancel_flag["cancelled"]:
                    break
                
                input_path = os.path.join(self.input_path, filename)
                # Update progress UI
                current_file_var.set(f"Processing: {filename}")
                progress_var.set(i)
                
                try:
                    # Process the image
                    self.restorer.restore_image(
                        input_path,
                        output_dir=output_folder,
                        model_name=model_name,
                        outscale=scale,
                        face_enhance=face_enhance
                    )
                    processed += 1
                except Exception as e:
                    error_msg = f"{filename}: {str(e)}"
                    logger.error(f"Batch processing error: {error_msg}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    errors.append(error_msg)
            
            # Update UI in the main thread
            self.root.after(0, lambda: self.finish_batch(progress_window, processed, len(image_files), errors))
        
        # Start batch processing thread
        threading.Thread(target=batch_thread, daemon=True).start()

    def _show_success_message(self, total):
        """Show a success message after batch processing.
        
        Args:
            total: Total number of successfully processed images
        """
        Messagebox.show_info(
            "Batch Processing Complete", 
            f"Successfully processed all {total} images.",
            parent=self.root
        )
    
    def finish_batch(self, progress_window, processed, total, errors):
        """Finalize batch processing and show results.
        
        Args:
            progress_window: The progress dialog window
            processed: Number of successfully processed images
            total: Total number of images
            errors: List of error messages
        """
        progress_window.destroy()
        
        # Log the batch processing results
        logger.info(f"Batch processing completed: {processed} of {total} images processed successfully")
        
        # If there were errors, show them with an option to view logs
        if len(errors) > 0:
            logger.warning(f"Batch processing had {len(errors)} errors")
            
            # Format error message
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n...and {len(errors) - 10} more errors."
            
            # Create a more detailed error message with log file information
            log_file_path = get_log_file_path()
            
            # Show warning dialog
            msg = (f"Processed {processed} of {total} images with errors.\n\n"
                  f"Errors:\n{error_msg}\n\n"
                  f"See the log file for more details.")
            
            Messagebox.show_warning(
                "Batch Processing Results", 
                msg,
                parent=self.root
            )
            
            # Ask if user wants to view logs
            if Messagebox.okcancel(
                "View Logs",
                "Would you like to open the log file to see more details?",
                parent=self.root
            ):
                self.open_log_file(log_file_path)
        else:
            # Show success message if all images were processed successfully
            Messagebox.show_info(
                "Batch Processing Complete", 
                f"Successfully processed all {total} images.",
                parent=self.root
            )
        
        self.status_var.set(f"Batch processing completed: {processed}/{total} successful.")

    def save_image(self):
        """Save the restored image."""
        if self.current_output_image is None:
            Messagebox.show_warning("No Image", "No restored image available to save.", parent=self.root)
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Restored Image",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_output_image.save(file_path)
                self.status_var.set(f"Image saved to: {file_path}")
            except Exception as e:
                Messagebox.show_error("Save Error", f"Failed to save image: {str(e)}", parent=self.root)

    def show_about(self):
        """Show the about dialog."""
        about_text = (
            "AI Old Photo Restoration Tool\n\n"
            "A tool to restore and colorize old photos using AI.\n\n"
            "Features:\n"
            "• Photo restoration using Real-ESRGAN\n"
            "• Photo colorization using DeOldify\n"
            "• Side-by-side comparison with zoom\n"
            "• Batch processing\n\n"
            "Keyboard Shortcuts:\n"
            "Ctrl++ : Zoom in\n"
            "Ctrl+- : Zoom out\n"
            "Ctrl+0 : Reset zoom\n\n"
            "Mouse Controls:\n"
            "• Scroll wheel to zoom in/out\n"
            "• Click and drag to pan when zoomed in"
        )
        Messagebox.show_info("About", about_text, parent=self.root)
        
    def open_log_file(self, log_file=None):
        """Open the log file in the default text editor.
        
        Args:
            log_file: Optional path to the log file. If None, uses the current log file.
        """
        if log_file is None:
            log_file = get_log_file_path()
            
        if os.path.exists(log_file):
            try:
                import subprocess
                os.startfile(log_file) if os.name == 'nt' else subprocess.call(['xdg-open', log_file])
                logger.info(f"Opened log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to open log file: {str(e)}")
                Messagebox.show_error("Error", f"Failed to open log file: {str(e)}", parent=self.root)
        else:
            Messagebox.show_warning("File Not Found", f"Log file not found: {log_file}", parent=self.root)
    
    def zoom_in(self):
        """Zoom in on the comparison view."""
        self.zoom_level *= 1.2
        self._update_zoom_level_display()
        if hasattr(self.compare_canvas, 'original_image'):
            self.display_comparison_with_zoom()

    def zoom_out(self):
        """Zoom out on the comparison view."""
        self.zoom_level /= 1.2
        # Don't allow zoom below 20%
        if self.zoom_level < 0.2:
            self.zoom_level = 0.2
        self._update_zoom_level_display()
        if hasattr(self.compare_canvas, 'original_image'):
            self.display_comparison_with_zoom()
            
    def reset_zoom(self):
        """Reset zoom and pan to default."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._update_zoom_level_display()
        if hasattr(self.compare_canvas, 'original_image'):
            self.display_comparison_with_zoom()
            
    def _update_zoom_level_display(self):
        """Update the zoom level display."""
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_level_var.set(f"{zoom_percent}%")
            
    def on_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming.
        
        Args:
            event: The mouse wheel event
        """
        if not hasattr(self.compare_canvas, 'original_image'):
            return
            
        # Determine zoom direction based on event
        if event.num == 5 or event.delta < 0:  # Scroll down
            self.zoom_level /= 1.1
            if self.zoom_level < 0.2:
                self.zoom_level = 0.2
        elif event.num == 4 or event.delta > 0:  # Scroll up
            self.zoom_level *= 1.1
            
        self._update_zoom_level_display()
        self.display_comparison_with_zoom()
            
    def start_pan(self, event):
        """Start panning the image."""
        if self.zoom_level > 1.0:
            self.is_panning = True
            self.last_x = event.x
            self.last_y = event.y
            self.compare_canvas.config(cursor="fleur")  # Change cursor to indicate panning
            
    def stop_pan(self, event):
        """Stop panning the image."""
        self.is_panning = False
        self.compare_canvas.config(cursor="hand2")  # Reset cursor
            
    def pan_image(self, event):
        """Pan the image based on mouse movement."""
        if self.is_panning and hasattr(self.compare_canvas, 'original_image'):
            # Calculate movement
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            # Update pan coordinates
            self.pan_x += dx
            self.pan_y += dy
            
            # Update last position
            self.last_x = event.x
            self.last_y = event.y
            
            # Redisplay with new pan coordinates
            self.display_comparison_with_zoom()
            
    def display_comparison_with_zoom(self):
        """Display the comparison view with zoom and pan applied."""
        if not hasattr(self.compare_canvas, 'original_image'):
            return
            
        try:
            original = self.compare_canvas.original_image
            
            # Get canvas dimensions
            canvas_width = self.compare_canvas.winfo_width() or 800
            canvas_height = self.compare_canvas.winfo_height() or 600
            
            # Calculate dimensions based on zoom
            img_width, img_height = original.size
            new_width = int(img_width * self.zoom_level)
            new_height = int(img_height * self.zoom_level)
            
            # Resize image based on zoom level
            try:
                zoomed_image = original.resize((new_width, new_height), Image.LANCZOS)
            except Exception:
                # Fallback to simpler resize method
                zoomed_image = original.resize((new_width, new_height), Image.NEAREST)
                
            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(zoomed_image)
            
            # Keep a reference to prevent garbage collection
            self.compare_canvas.image = photo
            
            # Clear canvas
            self.compare_canvas.delete("all")
            
            # Center of canvas
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            
            # Calculate position with pan adjustment
            x = center_x + self.pan_x
            y = center_y + self.pan_y
            
            # Draw image
            self.compare_canvas.create_image(x, y, anchor=CENTER, image=photo)
            
        except Exception as e:
            logger.error(f"Error in display_comparison_with_zoom: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.show_canvas_message(self.compare_canvas, f"Error displaying zoomed image: {str(e)}")


def main():
    """Main entry point for the application."""
    # Set up theme
    root = ttk.Window(themename="cosmo")
    app = PhotoRestorationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
