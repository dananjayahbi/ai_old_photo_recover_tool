# AI Old Photo Restoration Tool

A modern GUI application for restoring old photos using Real-ESRGAN technology.

## Features

- User-friendly GUI built with tkinter and ttkbootstrap
- High-quality photo restoration using Real-ESRGAN
- Face enhancement option for improved facial details
- Custom upscale factor
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
- Clone the Real-ESRGAN repository
- Set up the necessary files and directories

## Usage

Run the application using:
```
conda run -n depression python main.py
```

Or use the provided convenience scripts:
- Windows: `run.bat`
- Linux/Mac: `bash run.sh`

## License

This project is under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) for the image restoration technology