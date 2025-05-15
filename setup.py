#!/usr/bin/env python3

from setuptools import setup

setup(
    name="plugnpass",
    version="1.0.0",
    author="adermgram",
    author_email="your.email@example.com",
    description="iPhone File Transfer Utility for Linux",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/adermgram/plugnpass",
    py_modules=["iphone_file_transfer"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        "tk",
    ],
    entry_points={
        "console_scripts": [
            "plugnpass=iphone_file_transfer:main",
        ],
    },
) 