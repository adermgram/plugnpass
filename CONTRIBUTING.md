# Contributing to PlugNPass

Thank you for your interest in contributing to PlugNPass! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork to your local machine
3. Create a new branch for your changes
4. Make your changes and commit them
5. Push your changes to your fork
6. Submit a pull request

## Development Environment

To set up your development environment:

```bash
# Install dependencies
sudo apt install ifuse libimobiledevice-utils usbmuxd fuse python3 python3-tk

# Clone the repository
git clone https://github.com/adermgram/plugnpass.git
cd plugnpass

# Make the script executable
chmod +x iphone_file_transfer.py

# Run the application
./iphone_file_transfer.py
```

## Building Packages

To build a .deb package:

```bash
# Install build dependencies
sudo apt install build-essential devscripts debhelper dh-python

# Run the build script
./build_deb.sh
```

## Testing

Please test your changes thoroughly before submitting a pull request. Ensure that:

1. The application starts correctly
2. iPhone detection works
3. Mounting and unmounting work properly
4. File transfers (both upload and download) work correctly
5. UI elements function as expected

## Pull Request Process

1. Ensure your code follows the project's coding style
2. Update documentation to reflect your changes if necessary
3. Add a clear description of your changes in the pull request
4. Link any relevant issues in your pull request

## Reporting Issues

If you find a bug or have a feature request, please create an issue on GitHub with the following information:

1. A clear, descriptive title
2. A detailed description of the issue or feature request
3. Steps to reproduce the issue (for bugs)
4. Your operating system and version
5. The version of PlugNPass you're using

## License

By contributing to PlugNPass, you agree that your contributions will be licensed under the project's MIT license. 