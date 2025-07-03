def display_batch_results(self, progress_window, processed, total, errors):
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
    
    if errors:
        # Log the errors
        logger.warning(f"Batch processing had {len(errors)} errors")
        
        # Format error message
        error_msg = "\n".join(errors[:10])
        if len(errors) > 10:
            error_msg += f"\n...and {len(errors) - 10} more errors."
        
        # Create a more detailed error message with log file information
        log_file_path = get_log_file_path()
        error_details = (
            f"Processed {processed} of {total} images.\n\n"
            f"Errors:\n{error_msg}\n\n"
            f"See the log file for complete details:\n{log_file_path}\n\n"
            "Would you like to open the log file now?"
        )
        
        # Show error dialog with option to open log
        result = Messagebox.show_warning(
            "Batch Processing Results", 
            error_details,
            parent=self.root,
            buttons=["Yes:primary", "No:secondary"]
        )
        
        if result == "Yes":
            self.open_log_file(log_file_path)
    else:
        # Show success message if all images were processed successfully
        Messagebox.show_info(
            "Batch Processing Complete", 
            f"Successfully processed all {total} images.",
            parent=self.root
        )
