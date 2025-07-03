#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for the AI Old Photo Restoration Tool.
This script sets up the environment and installs dependencies.
"""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


def main():
    """Main setup function."""
    # Create a simple GUI for the setup
    root = tk.Tk()
    root.title("AI Old Photo Restoration Tool - Setup")
    root.geometry("500x400")
    
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
    
    def log_message(message):
        """Add message to log and update display.
        
        Args:
            message: Message to log
        """
        log.insert(tk.END, message + "\n")
        log.see(tk.END)
        log.update()
    
    def install_dependencies():
        """Install required Python packages."""
        try:
            status_var.set("Installing Python dependencies...")
            progress.config(mode="indeterminate")
            progress.start(10)
            
            log_message("Installing required Python packages...")
            
            # Install pip packages
            pip_packages = [
                "basicsr", "facexlib", "gfpgan", "torch", "torchvision",
                "numpy", "opencv-python", "pillow", "ttkbootstrap"
            ]
            
            for i, package in enumerate(pip_packages):
                log_message(f"Installing {package}...")
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", package],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    progress.config(mode="determinate")
                    progress.config(value=int((i+1) / len(pip_packages) * 50))
                except subprocess.CalledProcessError:
                    log_message(f"⚠️ Warning: Failed to install {package}. Continuing setup...")
            
            log_message("Python dependencies installed successfully.")
            
            # Clone Real-ESRGAN repository
            if not os.path.exists("Real-ESRGAN"):
                status_var.set("Cloning Real-ESRGAN repository...")
                log_message("Cloning Real-ESRGAN repository...")
                try:
                    subprocess.check_call(
                        ["git", "clone", "https://github.com/xinntao/Real-ESRGAN.git"],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    progress.config(value=60)
                    log_message("Real-ESRGAN repository cloned successfully.")
                except subprocess.CalledProcessError:
                    log_message("❌ Error: Failed to clone Real-ESRGAN repository.")
                    status_var.set("Setup failed")
                    messagebox.showerror("Setup Error", "Failed to clone Real-ESRGAN repository.")
                    return
            else:
                log_message("Real-ESRGAN repository already exists.")
                progress.config(value=60)
            
            # Set up Real-ESRGAN
            status_var.set("Setting up Real-ESRGAN...")
            log_message("Setting up Real-ESRGAN...")
            
            os.chdir("Real-ESRGAN")
            try:
                # Install Real-ESRGAN requirements
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                progress.config(value=80)
                log_message("Real-ESRGAN requirements installed.")
                
                # Install Real-ESRGAN as a Python package
                subprocess.check_call(
                    [sys.executable, "setup.py", "develop"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                progress.config(value=90)
                log_message("Real-ESRGAN setup complete.")
                
            except subprocess.CalledProcessError:
                log_message("❌ Error: Failed to set up Real-ESRGAN.")
                status_var.set("Setup failed")
                messagebox.showerror("Setup Error", "Failed to set up Real-ESRGAN.")
                os.chdir("..")
                return
            
            os.chdir("..")
            
            # Create necessary directories
            for directory in ["input", "output"]:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    log_message(f"Created {directory} directory.")
            
            # Complete
            progress.config(value=100)
            status_var.set("Setup completed successfully!")
            log_message("\n✅ Setup completed successfully!")
            log_message("\nYou can now run the application using: python main.py")
            
            messagebox.showinfo(
                "Setup Complete", 
                "AI Old Photo Restoration Tool has been set up successfully!\n\n"
                "You can now run the application using: python main.py"
            )
            
        except Exception as e:
            log_message(f"❌ Error during setup: {str(e)}")
            status_var.set("Setup failed")
            messagebox.showerror("Setup Error", f"An error occurred during setup: {str(e)}")
            
        finally:
            progress.stop()
    
    # Setup button
    ttk.Button(
        frame, 
        text="Install Dependencies", 
        command=install_dependencies
    ).pack(pady=10)
    
    ttk.Button(
        frame, 
        text="Exit", 
        command=root.quit
    ).pack()
    
    # Add initial instructions
    log_message("Welcome to the AI Old Photo Restoration Tool setup.")
    log_message("This will install required dependencies and set up the environment.")
    log_message("Click 'Install Dependencies' to begin.")
    log_message("Note: This may take several minutes depending on your internet connection.")
    
    root.mainloop()


if __name__ == "__main__":
    main()
