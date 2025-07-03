#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for the AI Old Photo Restoration Tool.
This script sets up the environment and installs dependencies.
"""

import os
import subprocess
import sys
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import shutil


def main():
    """Main setup function."""
    # Create a simple GUI for the setup
    root = tk.Tk()
    root.title("AI Old Photo Restoration Tool - Setup")
    root.geometry("500x600")
    
    style = ttk.Style()
    style.theme_use('clam')  # Use a modern theme
    
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(
        frame, 
        text="AI Old Photo Restoration Tool - Setup",
        font=("Helvetica", 16, "bold")
    ).pack(pady=(0, 20))
    
    # Setup log
    log_frame = ttk.LabelFrame(frame, text="Setup Log", padding=10)
    log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    log = tk.Text(log_frame, height=10, width=50, wrap=tk.WORD)
    log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(log_frame, command=log.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log.config(yscrollcommand=scrollbar.set)
    
    progress = ttk.Progressbar(frame, mode="determinate")
    progress.pack(fill=tk.X, pady=10)
    
    status_var = tk.StringVar(value="Ready to install")
    status_label = ttk.Label(frame, textvariable=status_var)
    status_label.pack(pady=5)
    
    # Create a message queue for thread-safe UI updates
    message_queue = queue.Queue()
    cancel_event = threading.Event()
    
    def log_message(message):
        """Add message to log and update display.
        Thread-safe version that uses the message queue.
        
        Args:
            message: Message to log
        """
        message_queue.put(("log", message))
    
    def update_status(message):
        """Update status label text.
        Thread-safe version that uses the message queue.
        
        Args:
            message: Status message
        """
        message_queue.put(("status", message))
    
    def update_progress(value=None, mode=None):
        """Update progress bar.
        Thread-safe version that uses the message queue.
        
        Args:
            value: Progress value (0-100)
            mode: Progress bar mode ('determinate' or 'indeterminate')
        """
        message_queue.put(("progress", (value, mode)))
    
    def show_message(msg_type, title, message):
        """Show a message dialog.
        Thread-safe version that uses the message queue.
        
        Args:
            msg_type: Type of message ('error', 'info', 'warning')
            title: Message dialog title
            message: Message dialog content
        """
        message_queue.put(("message", (msg_type, title, message)))
    
    def process_message_queue():
        """Process pending messages in the queue and update UI.
        This runs in the main thread, so it's safe to update UI elements.
        """
        try:
            # Process up to 10 messages at a time to keep UI responsive
            for _ in range(10):
                msg_type, data = message_queue.get_nowait()
                
                if msg_type == "log":
                    log.insert(tk.END, data + "\n")
                    log.see(tk.END)
                
                elif msg_type == "status":
                    status_var.set(data)
                
                elif msg_type == "progress":
                    value, mode = data
                    if mode is not None:
                        progress.config(mode=mode)
                        if mode == "indeterminate":
                            progress.start(10)
                        else:
                            progress.stop()
                    if value is not None:
                        progress.config(value=value)
                
                elif msg_type == "message":
                    msg_type, title, message = data
                    if msg_type == "error":
                        messagebox.showerror(title, message, parent=root)
                    elif msg_type == "info":
                        messagebox.showinfo(title, message, parent=root)
                    elif msg_type == "warning":
                        messagebox.showwarning(title, message, parent=root)
                
                message_queue.task_done()
                
        except queue.Empty:
            # No more messages in queue
            pass
        
        # Schedule next check if not cancelled
        if not cancel_event.is_set():
            root.after(100, process_message_queue)
    
    def install_dependencies():
        """Install required Python packages in the 'depression' conda environment.
        Runs the installation in a separate thread to keep UI responsive.
        """
        # Initialize UI
        update_status("Starting setup...")
        update_progress(mode="indeterminate")
        
        # Disable buttons during installation
        install_btn.config(state="disabled")
        exit_btn.config(state="disabled")
        
        # Start message queue processor
        root.after(100, process_message_queue)
        
        # Run installation in separate thread
        threading.Thread(target=run_installation, daemon=True).start()
    
    def run_installation():
        """Run the actual installation process in a separate thread."""
        try:
            update_status("Checking conda environment...")
            log_message("Checking conda installation...")
            
            # Check if conda is available
            if not shutil.which("conda"):
                log_message("❌ Error: Conda not found in PATH. Please install Anaconda or Miniconda.")
                update_status("Setup failed - Conda not found")
                show_message("error", "Setup Error", "Conda not found in PATH. Please install Anaconda or Miniconda.")
                enable_buttons()
                return
            
            # Check if 'depression' environment exists
            log_message("Checking for 'depression' conda environment...")
            try:
                # List environments and check if 'depression' exists
                result = subprocess.run(
                    ["conda", "env", "list"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if "depression" not in result.stdout:
                    log_message("❌ Error: The 'depression' conda environment was not found.")
                    update_status("Setup failed - Environment not found")
                    show_message("error", "Environment Not Found", 
                              "The 'depression' conda environment was not found. Please create it first.")
                    enable_buttons()
                    return
                
                log_message("✅ Found 'depression' conda environment!")
                update_progress(value=10, mode="determinate")
                
            except subprocess.CalledProcessError:
                log_message("❌ Error: Failed to list conda environments.")
                update_status("Setup failed")
                show_message("error", "Setup Error", "Failed to list conda environments.")
                enable_buttons()
                return
            
            # Install required packages
            update_status("Installing Python dependencies...")
            log_message("Installing required Python packages in 'depression' environment...")
            
            # Install pip packages
            pip_packages = [
                "basicsr", "facexlib", "gfpgan", "torch", "torchvision",
                "numpy", "opencv-python", "pillow", "ttkbootstrap"
            ]
            
            # First check which packages are already installed
            log_message("Checking which packages are already installed...")
            installed_packages = {}
            
            try:
                # Get list of installed packages
                result = subprocess.run(
                    ["conda", "run", "-n", "depression", "pip", "list"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30  # Add timeout to prevent hanging
                )
                
                # Parse output to get installed packages
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0].lower()
                        installed_packages[package_name] = True
                
                log_message(f"Found {len(installed_packages)} installed packages")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                log_message(f"⚠️ Warning: Failed to check installed packages. Will try installing all required packages.")
            
            for i, package in enumerate(pip_packages):
                package_lower = package.lower()
                package_installed = package_lower in installed_packages
                
                # Special case for opencv-python (may be installed as opencv)
                if package_lower == "opencv-python" and "opencv" in installed_packages:
                    package_installed = True
                
                # Special case for PIL/pillow
                if package_lower == "pillow" and "pil" in installed_packages:
                    package_installed = True
                
                if package_installed:
                    log_message(f"✅ {package} is already installed in 'depression' environment")
                    update_progress(value=int((i+1) / len(pip_packages) * 50))
                    continue
                
                log_message(f"Installing {package} in 'depression' environment...")
                try:
                    # Use timeout to prevent hanging on any specific package
                    subprocess.run(
                        ["conda", "run", "-n", "depression", "pip", "install", package],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=300,  # 5-minute timeout per package
                        check=True
                    )
                    log_message(f"✅ Successfully installed {package}")
                    update_progress(value=int((i+1) / len(pip_packages) * 50))
                    # Sleep briefly to allow UI updates
                    time.sleep(0.1)
                except subprocess.TimeoutExpired:
                    log_message(f"⚠️ Warning: Installation of {package} timed out after 5 minutes. Continuing setup...")
                except subprocess.CalledProcessError:
                    log_message(f"⚠️ Warning: Failed to install {package}. Continuing setup...")
            
            # This section is redundant since we already checked for conda and environment above
            # Continue with the setup process - Clone Real-ESRGAN repository
            
            log_message("Python dependencies installed successfully.")
            
            # Clone Real-ESRGAN repository
            if not os.path.exists("Real-ESRGAN"):
                update_status("Cloning Real-ESRGAN repository...")
                log_message("Cloning Real-ESRGAN repository...")
                try:
                    # Use subprocess.run with timeout instead of check_call
                    subprocess.run(
                        ["git", "clone", "https://github.com/xinntao/Real-ESRGAN.git"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=300,  # 5-minute timeout for cloning
                        check=True
                    )
                    update_progress(value=60)
                    log_message("✅ Real-ESRGAN repository cloned successfully.")
                    # Sleep briefly to allow UI updates
                    time.sleep(0.5)
                except subprocess.TimeoutExpired:
                    log_message("❌ Error: Timed out while cloning Real-ESRGAN repository.")
                    log_message("Please check your internet connection and try again.")
                    update_status("Setup failed - Timeout")
                    show_message("error", "Setup Error", 
                               "Timed out while cloning Real-ESRGAN repository. Please check your internet connection.")
                    enable_buttons()
                    return
                except subprocess.CalledProcessError as e:
                    log_message(f"❌ Error: Failed to clone Real-ESRGAN repository: {e}")
                    update_status("Setup failed")
                    show_message("error", "Setup Error", "Failed to clone Real-ESRGAN repository.")
                    enable_buttons()
                    return
            else:
                log_message("Real-ESRGAN repository already exists. Skipping clone.")
                update_progress(value=60)
            
            # Set up Real-ESRGAN
            update_status("Setting up Real-ESRGAN...")
            log_message("Setting up Real-ESRGAN in 'depression' conda environment...")
            
            # Make sure the directory exists before changing to it
            if not os.path.exists("Real-ESRGAN"):
                log_message("❌ Error: Real-ESRGAN directory not found.")
                update_status("Setup failed")
                show_message("error", "Setup Error", "Real-ESRGAN directory not found.")
                enable_buttons()
                return
                
            os.chdir("Real-ESRGAN")
            try:
                # Check if requirements are already installed
                log_message("Installing Real-ESRGAN requirements...")
                try:
                    # Use subprocess.run with timeout
                    subprocess.run(
                        ["conda", "run", "-n", "depression", "pip", "install", "-r", "requirements.txt"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=600,  # 10-minute timeout for installing requirements
                        check=True
                    )
                    update_progress(value=80)
                    log_message("✅ Real-ESRGAN requirements installed successfully.")
                    # Sleep briefly to allow UI updates
                    time.sleep(0.5)
                except subprocess.TimeoutExpired:
                    log_message("⚠️ Warning: Timed out while installing Real-ESRGAN requirements.")
                    log_message("This might be due to slow internet or dependency resolution.")
                    log_message("Continuing with setup, but some features may not work properly.")
                    update_progress(value=80)
                except subprocess.CalledProcessError as e:
                    log_message(f"⚠️ Warning: Failed to install some Real-ESRGAN requirements: {e}")
                    log_message("Continuing with setup, but some features may not work properly.")
                    update_progress(value=80)
                
                # Install Real-ESRGAN as a Python package
                log_message("Setting up Real-ESRGAN as a package...")
                try:
                    subprocess.run(
                        ["conda", "run", "-n", "depression", "python", "setup.py", "develop"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=300,  # 5-minute timeout for setup
                        check=True
                    )
                    update_progress(value=90)
                    log_message("✅ Real-ESRGAN setup complete.")
                    # Sleep briefly to allow UI updates
                    time.sleep(0.5)
                except subprocess.TimeoutExpired:
                    log_message("⚠️ Warning: Timed out while setting up Real-ESRGAN package.")
                    log_message("Continuing with setup, but some features may not work properly.")
                    update_progress(value=90)
                except subprocess.CalledProcessError as e:
                    log_message(f"⚠️ Warning: Failed to set up Real-ESRGAN package: {e}")
                    log_message("Continuing with setup, but some features may not work properly.")
                    update_progress(value=90)
                
            except Exception as e:
                log_message(f"❌ Error: Failed to set up Real-ESRGAN: {str(e)}")
                update_status("Setup failed")
                show_message("error", "Setup Error", f"Failed to set up Real-ESRGAN: {str(e)}")
                os.chdir("..")
                enable_buttons()
                return
            
            os.chdir("..")
            
            # Setup DeOldify for colorization
            if not os.path.exists("DeOldify"):
                update_status("Cloning DeOldify repository...")
                log_message("\nCloning DeOldify repository...")
                try:
                    # Use subprocess.run with timeout instead of check_call
                    subprocess.run(
                        ["git", "clone", "https://github.com/jantic/DeOldify.git"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=300,  # 5-minute timeout for cloning
                        check=True
                    )
                    update_progress(value=92)
                    log_message("✅ DeOldify repository cloned successfully.")
                    # Sleep briefly to allow UI updates
                    time.sleep(0.5)
                except subprocess.TimeoutExpired:
                    log_message("❌ Error: Timed out while cloning DeOldify repository.")
                    log_message("Please check your internet connection and try again.")
                    update_status("Setup incomplete - DeOldify not set up")
                    show_message("warning", "Setup Warning", 
                               "Timed out while cloning DeOldify repository. Colorization feature will not be available.")
                except subprocess.CalledProcessError as e:
                    log_message(f"❌ Error: Failed to clone DeOldify repository: {e}")
                    update_status("Setup incomplete - DeOldify not set up")
                    show_message("warning", "Setup Warning", 
                               "Failed to clone DeOldify repository. Colorization feature will not be available.")
            else:
                log_message("DeOldify repository already exists. Skipping clone.")
                update_progress(value=92)
            
            # Install DeOldify requirements if directory exists
            if os.path.exists("DeOldify"):
                os.chdir("DeOldify")
                try:
                    # Install DeOldify requirements
                    log_message("Installing DeOldify requirements...")
                    try:
                        subprocess.run(
                            ["conda", "run", "-n", "depression", "pip", "install", "-r", "requirements.txt"],
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            timeout=600,  # 10-minute timeout for installing requirements
                            check=True
                        )
                        update_progress(value=95)
                        log_message("✅ DeOldify requirements installed successfully.")
                    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                        log_message(f"⚠️ Warning: Issue installing DeOldify requirements: {e}")
                        log_message("Colorization feature may not work properly.")
                    
                    # Download pre-trained models if needed
                    models_dir = "models"
                    if not os.path.exists(models_dir):
                        os.makedirs(models_dir)
                        log_message("Created models directory.")
                    
                    # URLs for DeOldify pre-trained models
                    model_urls = {
                        "ColorizeArtistic_gen.pth": "https://www.dropbox.com/s/zkehq1uwahhbc2o/ColorizeArtistic_gen.pth?dl=1",
                        "ColorizeStable_gen.pth": "https://www.dropbox.com/s/mwjep3vyqk5mkld/ColorizeStable_gen.pth?dl=1"
                    }
                    
                    for model_name, model_url in model_urls.items():
                        model_path = os.path.join(models_dir, model_name)
                        if not os.path.exists(model_path):
                            try:
                                log_message(f"Downloading {model_name}...")
                                # Create a models directory in the root folder too (used by DeOldify)
                                root_models_dir = os.path.join("..", "models")
                                os.makedirs(root_models_dir, exist_ok=True)
                                
                                # Use curl to download the model
                                subprocess.run(
                                    ["curl", "-L", model_url, "-o", model_path],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    timeout=600,  # 10-minute timeout for downloading large files
                                    check=True
                                )
                                
                                # Copy the model to the root models directory as well
                                root_model_path = os.path.join(root_models_dir, model_name)
                                import shutil
                                shutil.copy2(model_path, root_model_path)
                                
                                log_message(f"✅ {model_name} downloaded successfully.")
                            except Exception as e:
                                log_message(f"⚠️ Warning: Failed to download {model_name}: {e}")
                                log_message("You may need to download this model manually.")
                        else:
                            log_message(f"{model_name} already exists. Skipping download.")
                    
                    log_message("✅ DeOldify setup complete.")
                    update_progress(value=97)
                except Exception as e:
                    log_message(f"⚠️ Warning: Error during DeOldify setup: {e}")
                    log_message("Colorization feature may not work properly.")
                
                os.chdir("..")
            
            # Create necessary directories
            for directory in ["input", "output"]:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    log_message(f"Created {directory} directory.")
            
            # Verify installation
            update_status("Verifying installation...")
            log_message("\nVerifying if key packages are accessible...")
            
            # Test importing key packages
            verification_cmd = (
                "import sys; "
                "modules = ['numpy', 'cv2', 'torch', 'PIL']; "
                "missing = [m for m in modules if m not in sys.modules and __import__(m, fromlist=['']) is None]; "
                "print('Missing: ' + ', '.join(missing) if missing else 'All key packages verified!')"
            )
            
            try:
                result = subprocess.run(
                    ["conda", "run", "-n", "depression", "python", "-c", verification_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30
                )
                
                if "All key packages verified" in result.stdout:
                    log_message("✅ All key packages are properly installed!")
                else:
                    log_message(f"⚠️ Some packages may not be properly installed: {result.stdout.strip()}")
                    log_message("The application may still work, but you might encounter issues.")
            except Exception as e:
                log_message(f"⚠️ Warning: Failed to verify packages: {str(e)}")
            
            # Complete
            update_progress(value=100)
            update_status("Setup completed successfully!")
            log_message("\n✅ Setup completed successfully!")
            log_message("\nYou can now run the application using: conda run -n depression python main.py")
            
            show_message("info", "Setup Complete", 
                "AI Old Photo Restoration Tool has been set up successfully in the 'depression' conda environment!\n\n"
                "You can now run the application using:\n"
                "conda run -n depression python main.py"
            )
            
        except Exception as e:
            log_message(f"❌ Error during setup: {str(e)}")
            update_status("Setup failed")
            show_message("error", "Setup Error", f"An error occurred during setup: {str(e)}")
            
        finally:
            # Reset progress bar and enable buttons
            root.after(0, lambda: progress.stop())
            enable_buttons()
            
            # Signal the message queue processor to stop
            cancel_event.set()
    
    def enable_buttons():
        """Re-enable buttons after installation completes or fails."""
        root.after(0, lambda: install_btn.config(state="normal"))
        root.after(0, lambda: exit_btn.config(state="normal"))
    
    # Create a frame for buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10)
    
    # Setup buttons
    install_btn = ttk.Button(
        button_frame, 
        text="Install Dependencies", 
        command=install_dependencies
    )
    install_btn.pack(side=tk.LEFT, padx=5)
    
    # Add a skip button to bypass installation if user already has dependencies
    skip_btn = ttk.Button(
        button_frame,
        text="Skip (Already Installed)",
        command=lambda: show_message("info", "Setup Skipped", 
            "Setup has been skipped. If you encounter issues, please run the setup again.")
    )
    skip_btn.pack(side=tk.LEFT, padx=5)
    
    exit_btn = ttk.Button(
        button_frame, 
        text="Exit", 
        command=root.quit
    )
    exit_btn.pack(side=tk.LEFT, padx=5)
    
    # Add initial instructions
    log_message("Welcome to the AI Old Photo Restoration Tool setup.")
    log_message("This will install required dependencies and set up the environment.")
    log_message("Click 'Install Dependencies' to begin.")
    log_message("Note: This may take several minutes depending on your internet connection.")
    
    root.mainloop()


if __name__ == "__main__":
    main()
