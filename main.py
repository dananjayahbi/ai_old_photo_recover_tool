#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the AI Old Photo Restoration Tool.
"""

import os
import sys
import threading
import time
from pathlib import Path
from tkinter import filedialog

import cv2
import numpy as np
import ttkbootstrap as ttk
from PIL import Image, ImageTk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from restoration import RestoreImage


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
        menubar = ttk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = ttk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image...", command=self.open_image)
        file_menu.add_command(label="Open Folder...", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save Restored Image...", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = ttk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

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
        
        # Settings section
        settings_section = ttk.LabelFrame(control_frame, text="Restoration Settings", padding=10)
        settings_section.pack(fill=X, pady=(0, 10))
        
        # Scale factor setting
        scale_frame = ttk.Frame(settings_section)
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
            settings_section, 
            text="Enhance Faces", 
            variable=self.face_enhance_var,
            bootstyle="round-toggle"
        )
        face_enhance_cb.pack(fill=X, pady=(0, 10))
        
        # Model selection
        model_frame = ttk.Frame(settings_section)
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
        
        # Process section
        process_section = ttk.LabelFrame(control_frame, text="Process", padding=10)
        process_section.pack(fill=X, pady=(0, 10))
        
        ttk.Button(
            process_section, 
            text="Restore Image", 
            bootstyle="success", 
            command=self.process_image
        ).pack(fill=X, pady=(0, 5))
        
        ttk.Button(
            process_section, 
            text="Batch Process", 
            bootstyle="info", 
            command=self.batch_process
        ).pack(fill=X)
        
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
        
        # Create canvases for images
        self.before_canvas = ttk.Canvas(self.before_frame, background="#f0f0f0")
        self.before_canvas.pack(fill=BOTH, expand=YES)
        
        self.after_canvas = ttk.Canvas(self.after_frame, background="#f0f0f0")
        self.after_canvas.pack(fill=BOTH, expand=YES)
        
        # Split view for comparison
        self.compare_canvas = ttk.Canvas(self.compare_frame, background="#f0f0f0")
        self.compare_canvas.pack(fill=BOTH, expand=YES)
        
        # Default message when no image is loaded
        self.show_canvas_message(self.before_canvas, "No image loaded. Use 'Open Image' to load a photo.")
        self.show_canvas_message(self.after_canvas, "Restored image will appear here after processing.")
        self.show_canvas_message(self.compare_canvas, "Comparison view will be available after restoration.")

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
        canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 800
        canvas_height = canvas.winfo_height() or 600
        
        # Calculate scale to fit image in canvas
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        
        # Scale image
        if scale < 1:
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            display_image = image.resize((new_width, new_height), Image.LANCZOS)
        else:
            display_image = image
        
        # Convert to PhotoImage for tkinter
        photo = ImageTk.PhotoImage(display_image)
        
        # Keep a reference to prevent garbage collection
        canvas.image = photo
        
        # Calculate position for centering
        x = (canvas_width - display_image.width) // 2
        y = (canvas_height - display_image.height) // 2
        
        # Display the image
        canvas.create_image(x, y, anchor=NW, image=photo)

    def process_image(self):
        """Process the current image using Real-ESRGAN."""
        if self.input_path is None or self.current_input_image is None:
            Messagebox.show_warning("No Image", "Please open an image first.", parent=self.root)
            return
        
        self.status_var.set("Processing image...")
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)
        
        # Get parameters
        scale = self.scale_var.get()
        face_enhance = self.face_enhance_var.get()
        model_name = self.model_var.get()
        
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
                
                # Process the image
                output_path = self.restorer.restore_image(
                    input_path,
                    model_name=model_name,
                    outscale=scale,
                    face_enhance=face_enhance
                )
                
                # Update UI in the main thread
                self.root.after(0, lambda: self.display_result(output_path))
            
            except Exception as e:
                # Handle errors in the main thread
                self.root.after(0, lambda: self.handle_process_error(str(e)))
        
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
            
            # Display in After tab
            self.display_image(self.after_canvas, output_image)
            
            # Create comparison view
            self.create_comparison_view()
            
            # Switch to After tab
            self.view_notebook.select(1)
        
        except Exception as e:
            Messagebox.show_error("Error", f"Failed to load result: {str(e)}", parent=self.root)
            self.status_var.set("Error displaying result.")

    def handle_process_error(self, error_message):
        """Handle errors from the processing thread.
        
        Args:
            error_message: Error message to display
        """
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.status_var.set("Processing failed.")
        Messagebox.show_error("Processing Error", f"Failed to process image: {error_message}", parent=self.root)

    def create_comparison_view(self):
        """Create a side-by-side comparison of before and after images."""
        if self.current_input_image is None or self.current_output_image is None:
            return
        
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
        
        # Display in Compare tab
        self.display_image(self.compare_canvas, comparison)

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
                    errors.append(f"{filename}: {str(e)}")
            
            # Update UI in the main thread
            self.root.after(0, lambda: self.finish_batch(progress_window, processed, len(image_files), errors))
        
        # Start batch processing thread
        threading.Thread(target=batch_thread, daemon=True).start()

    def finish_batch(self, progress_window, processed, total, errors):
        """Finalize batch processing and show results.
        
        Args:
            progress_window: The progress dialog window
            processed: Number of successfully processed images
            total: Total number of images
            errors: List of error messages
        """
        progress_window.destroy()
        
        if errors:
            error_msg = "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n...and {len(errors) - 10} more errors."
            
            Messagebox.show_warning(
                "Batch Processing Results", 
                f"Processed {processed} of {total} images.\n\nErrors:\n{error_msg}",
                parent=self.root
            )
        else:
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
        Messagebox.show_info(
            "About AI Old Photo Restoration Tool", 
            "AI Old Photo Restoration Tool v1.0\n\n"
            "This application uses Real-ESRGAN technology to restore and enhance old photos.\n\n"
            "Built with Python, tkinter, and ttkbootstrap.\n\n"
            "© 2025 Your Name",
            parent=self.root
        )


def main():
    """Main entry point for the application."""
    # Set up theme
    root = ttk.Window(themename="cosmo")
    app = PhotoRestorationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
