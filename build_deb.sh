#!/bin/bash
# Build .deb package for PlugNPass

echo "====================================="
echo "  PlugNPass .deb Package Builder"
echo "====================================="
echo ""

# Check for required tools
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo "Error: dpkg-buildpackage not found"
    echo "Please install the build tools with:"
    echo "  sudo apt install build-essential devscripts debhelper dh-python"
    exit 1
fi

# Clean any previous build artifacts
echo "Cleaning previous build files..."
rm -rf debian/plugnpass
rm -f ../plugnpass_*.deb
rm -f ../plugnpass_*.changes
rm -f ../plugnpass_*.buildinfo

# Build the package
echo "Building package..."
dpkg-buildpackage -us -uc -b -d

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Build successful!"
    echo ""
    echo "Package created:"
    ls -lh ../plugnpass_*.deb
    echo ""
    echo "You can install it with:"
    echo "  sudo apt install ../plugnpass_*.deb"
    echo ""
else
    echo ""
    echo "Build failed!"
    echo ""
    echo "Please check the output above for errors."
    exit 1
fi

# Option to install
echo "Would you like to install the package now? (y/N)"
read -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing package..."
    
    # Check for existing installations and remove them first
    if dpkg -l | grep -q "plugnpass"; then
        echo "Removing previous installation..."
        sudo apt remove -y plugnpass
    fi
    
    # Check for stray launchers in user's bin directory
    USER_LAUNCHER="$HOME/bin/plugnpass"
    if [ -f "$USER_LAUNCHER" ]; then
        echo "Removing old user launcher script..."
        rm -f "$USER_LAUNCHER"
    fi
    
    # Install the new package
    echo "Installing new package..."
    sudo apt install ../plugnpass_*.deb
    
    # Verify installation
    if command -v plugnpass &> /dev/null; then
        echo ""
        echo "Installation successful!"
        plugnpass --version
    else
        echo ""
        echo "Installation might have issues. Please check your PATH."
    fi
fi 