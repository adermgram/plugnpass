#!/bin/bash
# PlugNPass installer script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="PlugNPass"
APP_SCRIPT="iphone_file_transfer.py"
LAUNCHER_NAME="plugnpass"
BIN_DIR="$HOME/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
CONFIG_DIR="$HOME/.config/plugnpass"

# Print header
echo "====================================="
echo "  $APP_NAME Installer"
echo "====================================="
echo ""

# Check requirements
echo "Checking requirements..."
missing_pkgs=()

check_command() {
    if ! command -v $1 &> /dev/null; then
        missing_pkgs+=("$2")
        return 1
    fi
    return 0
}

check_command ifuse "ifuse"
check_command idevice_id "libimobiledevice-utils"
check_command fusermount "fuse"
check_command python3 "python3"

if [ ${#missing_pkgs[@]} -gt 0 ]; then
    echo "The following packages are required but not installed:"
    for pkg in "${missing_pkgs[@]}"; do
        echo "  - $pkg"
    done
    echo ""
    echo "Please install them with:"
    echo "  sudo apt install ${missing_pkgs[*]}"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation aborted."
        exit 1
    fi
fi

# Create directories
echo "Creating directories..."
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$CONFIG_DIR"

# Make the app script executable
echo "Setting up application..."
chmod +x "$SCRIPT_DIR/$APP_SCRIPT"

# Create the launcher script
echo "Creating launcher..."
cat > "$BIN_DIR/$LAUNCHER_NAME" << EOF
#!/bin/bash
# $APP_NAME launcher script

# Path to the Python script
APP_PATH="$SCRIPT_DIR/$APP_SCRIPT"

# Make sure we have the required packages
check_requirements() {
    for cmd in ifuse idevice_id fusermount; do
        if ! command -v \$cmd &> /dev/null; then
            echo "Error: \$cmd is not installed."
            echo "Please install the required packages:"
            echo "  sudo apt install ifuse libimobiledevice-utils fuse"
            return 1
        fi
    done
    return 0
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3:"
    echo "  sudo apt install python3 python3-tk"
    exit 1
fi

# Check other requirements
if ! check_requirements; then
    exit 1
fi

# Run the app
python3 "\$APP_PATH" "\$@"
EOF

chmod +x "$BIN_DIR/$LAUNCHER_NAME"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$DESKTOP_DIR/$LAUNCHER_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=iPhone File Transfer Utility for Linux
Exec=$BIN_DIR/$LAUNCHER_NAME
Icon=phone
Terminal=false
Categories=Utility;FileTools;
Keywords=iPhone;iOS;iPad;file;transfer;
EOF

chmod +x "$DESKTOP_DIR/$LAUNCHER_NAME.desktop"

# Add bin directory to PATH if not already present
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Adding $BIN_DIR to your PATH..."
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
    echo "Please restart your terminal or run 'source ~/.bashrc' to update your PATH."
fi

# Set up mount point
MOUNT_PATH="$HOME/iPhoneMount"
echo "Setting up mount point at $MOUNT_PATH..."
mkdir -p "$MOUNT_PATH"

# Ensure user is in the fuse group
if ! groups | grep -q "fuse"; then
    echo "Note: You may need to add yourself to the fuse group with:"
    echo "  sudo usermod -aG fuse $USER"
    echo "  (This will require logging out and back in to take effect)"
fi

echo ""
echo "====================================="
echo "  Installation Complete!"
echo "====================================="
echo ""
echo "You can start $APP_NAME by:"
echo "  1. Running '$LAUNCHER_NAME' in terminal"
echo "  2. Finding '$APP_NAME' in your applications menu"
echo ""
echo "For help and troubleshooting, click the 'Help' button in the app."
echo ""

# Offer to start the application
read -p "Would you like to start $APP_NAME now? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    "$BIN_DIR/$LAUNCHER_NAME"
fi 