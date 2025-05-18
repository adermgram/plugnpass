#!/bin/bash
# PlugNPass - Launcher Script

# Script version and configuration
SCRIPT_VERSION="1.0.1"
APP_PATH="/usr/share/plugnpass/iphone_file_transfer.py"
LOG_FILE="$HOME/.config/plugnpass/launcher.log"

# Create log directory if it doesn't exist
mkdir -p "$HOME/.config/plugnpass"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3 with: sudo apt install python3 python3-tk"
    log "ERROR: Python 3 not found"
    exit 1
fi

# Check for required packages
for cmd in ifuse idevice_id fusermount; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        echo "Please install the required packages with:"
        echo "  sudo apt install ifuse libimobiledevice-utils fuse"
        log "ERROR: Required command not found: $cmd"
        exit 1
    fi
done

# Check if the main script exists
if [ ! -f "$APP_PATH" ]; then
    echo "Error: PlugNPass installation is broken or incomplete."
    echo "The main application script was not found at: $APP_PATH"
    echo "Please try reinstalling the package with: sudo apt install --reinstall plugnpass"
    log "ERROR: Main script not found at $APP_PATH"
    exit 1
fi

# Launch the application
log "Launching PlugNPass"
python3 "$APP_PATH" "$@"
EXIT_CODE=$?

# Handle any errors
if [ $EXIT_CODE -ne 0 ]; then
    log "Application exited with code $EXIT_CODE"
    if [ $EXIT_CODE -eq 127 ]; then
        echo "Error: PlugNPass encountered a dependency error."
        echo "Please ensure all dependencies are properly installed."
    fi
fi

exit $EXIT_CODE 