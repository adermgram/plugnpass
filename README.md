# PlugNPass

iPhone File Transfer Utility for Linux

## Description

PlugNPass (pronounced "Plug and Pass") is a simple, user-friendly utility for transferring files between Linux computers and iOS devices (iPhone, iPad). It provides an easy graphical interface for accessing your iOS device's media and documents.

## Features

- **Media Access**: Browse and download photos, videos, and music from your iOS device
- **Document Transfer**: Upload and download files to/from app document folders
- **Multiple File Support**: Select and download multiple files at once
- **File Filtering**: Automatically hides system files for a cleaner view
- **Search**: Easily find files by name
- **Multiple Apps**: Access documents from various iOS apps

## Installation

### Method 1: Using the .deb package (Recommended for Ubuntu/Debian)

Download the .deb package and install with:

```bash
sudo apt install ./plugnpass_1.0.0_all.deb
```

This will automatically install all dependencies and set up the application.

### Method 2: Manual Installation

#### Prerequisites

You need the following packages installed:

```bash
sudo apt install ifuse libimobiledevice-utils usbmuxd fuse python3 python3-tk
```

#### Setup

1. Clone or download this repository:
   ```
   git clone https://github.com/adermgram/plugnpass.git
   cd plugnpass
   ```

2. Run the installer:
   ```
   ./install.sh
   ```

The installer will:
- Make the app executable
- Create a launcher in your bin directory
- Create a desktop entry for easy access
- Set up necessary permissions

## Usage

1. Connect your iPhone/iPad via USB
2. Launch PlugNPass from your applications menu or run `plugnpass` in terminal
3. Click "Mount Media" to access photos and videos (read-only)
4. Click "Mount Documents" to access app documents (read-write)
5. Select files to download or use upload button to send files to your device

## Troubleshooting

- **Device Not Found**: Make sure your device is unlocked and trusted your computer
- **Mount Errors**: Use the "Reset Mount Point" or "Deep Clean Mount" buttons
- **Permission Issues**: Ensure proper permissions with `sudo usermod -aG fuse YOUR_USERNAME`

## How It Works

PlugNPass uses the libimobiledevice and ifuse libraries to safely communicate with your iOS device without needing iTunes. The application mounts your device's filesystem locally, allowing standard file operations.

## License

MIT License

## Acknowledgments

- libimobiledevice project (https://libimobiledevice.org/)
- ifuse project (https://github.com/libimobiledevice/ifuse)

---

© 2025 