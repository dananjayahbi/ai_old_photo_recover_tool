# AI Old Photo Restoration Tool

A modern GUI application for restoring and colorizing old photos using Real-ESRGAN and DeOldify technologies.

## Features

- User-friendly GUI built with tkinter and ttkbootstrap
- Two powerful AI technologies in one tool:
  - **Restoration**: Enhance photo quality using Real-ESRGAN
  - **Colorization**: Convert black and white photos to color using DeOldify
- Advanced options for both restoration and colorization:
  - Face enhancement for improved facial details (Real-ESRGAN)
  - Custom upscale factor (Real-ESRGAN)
  - Artistic mode and render quality settings (DeOldify)
- Before/After comparison view
- Batch processing support

## Installation

1. Make sure you have Anaconda or Miniconda installed with the 'depression' conda environment:
```
# If you don't already have the environment, create it:
conda create -n depression python=3.8
```

2. Clone this repository:
```
git clone https://github.com/yourusername/ai_old_photo_recover_tool.git
cd ai_old_photo_recover_tool
```

3. Run the setup script to install dependencies and set up the environment:
```
python setup.py
```

This will:
- Install required packages in the 'depression' conda environment
- Clone the Real-ESRGAN repository for restoration
- Clone the DeOldify repository for colorization
- Set up the necessary files and directories

## Usage

Run the application using:
```
conda run -n depression python main.py
```

Or use the provided convenience scripts:
- Windows: `run.bat`
- Linux/Mac: `bash run.sh`

### Restoration Mode

Enhance the quality of old or damaged photos:
1. Select "Restore Image (Super Resolution)" mode
2. Adjust the scale factor (1.0-4.0)
3. Toggle "Enhance Faces" option if needed
4. Choose the appropriate model
5. Click "Process" to restore the image

### Colorization Mode

Convert black and white photos to color:
1. Select "Colorize Black & White Image" mode
2. Toggle "Artistic Mode" for more vivid colors (disable for more realistic but conservative colors)
3. Adjust render quality (higher values = better quality but slower processing)
4. Click "Process" to colorize the image

## License

This project is under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) for the image restoration technology