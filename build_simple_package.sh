#!/bin/bash
# Simple package builder for PlugNPass

echo "====================================="
echo "  PlugNPass Simple Package Builder"
echo "====================================="
echo ""

VERSION="1.0.0"
PKG_DIR="plugnpass-$VERSION"
PKG_FILE="$PKG_DIR.tar.gz"

# Create package directory
echo "Creating package directory..."
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/bin"
mkdir -p "$PKG_DIR/share/applications"
mkdir -p "$PKG_DIR/doc"

# Copy files
echo "Copying files..."
cp iphone_file_transfer.py "$PKG_DIR/bin/plugnpass"
cp README.md LICENSE "$PKG_DIR/doc/"
cp install.sh "$PKG_DIR/"

# Create desktop file
echo "Creating desktop file..."
cat > "$PKG_DIR/share/applications/plugnpass.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PlugNPass
Comment=iPhone File Transfer Utility for Linux
Exec=plugnpass
Icon=phone
Terminal=false
Categories=Utility;FileTools;
Keywords=iPhone;iOS;iPad;file;transfer;
EOF

# Create package
echo "Creating package..."
tar -czf "$PKG_FILE" "$PKG_DIR"

# Clean up
echo "Cleaning up..."
rm -rf "$PKG_DIR"

echo ""
echo "Package created: $PKG_FILE"
echo ""
echo "Users can install it with:"
echo "  tar -xzf $PKG_FILE"
echo "  cd $PKG_DIR"
echo "  ./install.sh"
echo "" 