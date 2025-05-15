#!/usr/bin/env python3
# PlugNPass - iPhone File Transfer Utility for Linux
# Version 1.0.0
# Copyright (c) 2025 - Present
# Licensed under MIT License
# Description: Easy file transfer utility for iPhone and iPad devices on Linux

import os
import subprocess
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, Button, Label, Listbox, Scrollbar, END, Frame, StringVar, Entry
import traceback
import time
import socket
import platform

# Application information
APP_NAME = "PlugNPass"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "iPhone File Transfer Utility for Linux"

# Paths and configuration
MOUNT_PATH = os.path.expanduser("~/iPhoneMount")
CONFIG_DIR = os.path.expanduser("~/.config/plugnpass")
DEBUG = False  # Disable debug output for normal use

# Global state tracking
CURRENT_MOUNT_TYPE = None  # None, "media", or "documents"
CURRENT_APP_ID = None  # The app ID if in documents mode
APP_LOCK_FILE = os.path.expanduser("~/.plugnpass.lock")
LOG_FILE = os.path.join(CONFIG_DIR, "plugnpass.log")

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

def log_message(message, level="INFO"):
    """Log message to both console and log file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} [{level}] {message}"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")
        
    if DEBUG or level in ["ERROR", "WARNING"]:
        print(log_line)

def debug_log(message):
    """Print debug message if DEBUG is enabled"""
    if DEBUG:
        log_message(message, "DEBUG")

def check_requirements():
    """Check if all required tools are installed"""
    requirements = {
        "ifuse": "ifuse command is required to mount iPhone. Install with: sudo apt install ifuse",
        "idevice_id": "idevice_id command is required to detect iPhone. Install with: sudo apt install libimobiledevice-utils",
        "fusermount": "fusermount command is required to mount filesystem. Install with: sudo apt install fuse"
    }
    
    missing = []
    for cmd, msg in requirements.items():
        try:
            result = subprocess.run(["which", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                missing.append(msg)
        except Exception:
            missing.append(msg)
    
    return missing

def get_device_udid():
    """Get the UDID of the connected iPhone"""
    try:
        result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]  # Return the first device if multiple are connected
        return None
    except Exception as e:
        print(f"Error getting device UDID: {str(e)}")
        return None

def check_mount():
    return os.path.ismount(MOUNT_PATH)

def update_status(text):
    """Safely update status label"""
    try:
        if status_label.winfo_exists():
            status_label.config(text=text)
            root.update_idletasks()
    except Exception as e:
        print(f"Error updating status: {e}")

def get_app_list():
    """Get list of iOS apps that support file sharing"""
    try:
        debug_log("Fetching app list...")
        result = subprocess.run(["ifuse", "--list-apps"], capture_output=True, text=True)
        debug_log(f"ifuse --list-apps exit code: {result.returncode}")
        debug_log(f"ifuse --list-apps stdout: {result.stdout}")
        debug_log(f"ifuse --list-apps stderr: {result.stderr}")
        
        apps = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                debug_log(f"Processing app line: {line}")
                if not line.strip():
                    continue
                    
                parts = line.strip().split(',', 2)
                debug_log(f"Split parts: {parts}")
                
                if len(parts) >= 3:
                    app_id = parts[0].strip()
                    app_name = parts[2].strip().strip('"')
                    apps.append((app_id, app_name))
                    debug_log(f"Added app: {app_name} ({app_id})")
                else:
                    debug_log(f"Skipping invalid app line: {line}")
                    
        debug_log(f"Total apps found: {len(apps)}")
        return apps
    except Exception as e:
        debug_log(f"Error getting app list: {str(e)}")
        debug_log(traceback.format_exc())
        return []

def select_app_dialog():
    """Show dialog to select an app for file sharing"""
    debug_log("Opening app selection dialog")
    apps = get_app_list()
    if not apps:
        debug_log("No apps with file sharing found")
        messagebox.showerror("Error", "No apps with file sharing found")
        return None
        
    debug_log(f"Creating dialog with {len(apps)} apps")
    
    # Create a function to handle app selection with explicit app selection
    def show_app_dialog():
        nonlocal selected_app
        
        app_dialog = tk.Toplevel(root)
        app_dialog.title("Select App for File Sharing")
        app_dialog.geometry("400x300")
        app_dialog.transient(root)  # Set as transient to root
        app_dialog.grab_set()  # Make dialog modal
        app_dialog.protocol("WM_DELETE_WINDOW", lambda: app_dialog.destroy())  # Handle window closing
        
        Label(app_dialog, text="Select an app to access its Documents folder:").pack(pady=10)
        
        # Frame for the listbox
        list_frame = Frame(app_dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add scrollbar
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Create the listbox with scrollbar
        listbox = Listbox(list_frame, width=50, height=15, yscrollcommand=scrollbar.set, selectmode="single")
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Add double-click binding
        listbox.bind("<Double-1>", lambda event: on_select())
        
        # Populate the list
        for i, (app_id, app_name) in enumerate(apps):
            listbox.insert(END, f"{app_name} ({app_id})")
        
        # Select the first app by default
        if len(apps) > 0:
            listbox.selection_set(0)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                selected_app.append(apps[index])
                debug_log(f"Selected app: {apps[index][1]} ({apps[index][0]})")
                app_dialog.destroy()
            else:
                debug_log("No app selected")
                messagebox.showinfo("Selection Required", "Please select an app first")
        
        # Button frame
        button_frame = Frame(app_dialog)
        button_frame.pack(fill="x", pady=10)
        
        Button(button_frame, text="Select", command=on_select, width=10).pack(side="left", expand=True, padx=10)
        Button(button_frame, text="Cancel", command=lambda: app_dialog.destroy(), width=10).pack(side="right", expand=True, padx=10)
        
        # Center the dialog
        app_dialog.update_idletasks()
        width = app_dialog.winfo_width()
        height = app_dialog.winfo_height()
        x = (app_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (app_dialog.winfo_screenheight() // 2) - (height // 2)
        app_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Force focus on dialog
        app_dialog.focus_force()
        
        # Wait for dialog to close
        app_dialog.wait_window()
    
    # Use a list to store selection results
    selected_app = []
    
    # Show the dialog and get selection
    show_app_dialog()
    
    # Return selected app ID if something was selected
    if selected_app:
        debug_log(f"Returning selected app: {selected_app[0][1]} ({selected_app[0][0]})")
        return selected_app[0][0]  # Return the app ID
    else:
        debug_log("No app selected, dialog was canceled")
        return None

def reset_mount_point():
    """Reset the mount point directory by removing and recreating it"""
    debug_log(f"Resetting mount point directory: {MOUNT_PATH}")
    success = False
    
    # First unmount if mounted
    try:
        debug_log("Forcibly unmounting")
        # Try standard unmount first
        subprocess.run(["fusermount", "-u", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        # Then try with -z force option
        subprocess.run(["fusermount", "-uz", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        # Then try with sudo as a last resort
        subprocess.run(["sudo", "umount", "-f", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except Exception as e:
        debug_log(f"Unmount error (non-fatal): {e}")
    
    # Remove the directory forcefully
    try:
        # Ensure not mounted before removal attempts
        if not check_mount():
            # Try direct OS removal
            if os.path.exists(MOUNT_PATH):
                debug_log("Removing directory with shutil.rmtree")
                shutil.rmtree(MOUNT_PATH, ignore_errors=True)
            
            # Try with command line as fallback
            debug_log("Removing directory with rm command")
            subprocess.run(["rm", "-rf", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            # One more check
            if os.path.exists(MOUNT_PATH):
                debug_log("Directory still exists, trying with sudo")
                subprocess.run(["sudo", "rm", "-rf", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    except Exception as e:
        debug_log(f"Error removing mount directory (non-fatal): {e}")
    
    # Create a fresh directory
    try:
        debug_log("Creating fresh mount directory")
        # Try direct OS creation
        os.makedirs(MOUNT_PATH, exist_ok=True)
        
        # Check if directory was created successfully
        if os.path.exists(MOUNT_PATH):
            # Ensure proper permissions
            debug_log("Setting permissions on mount directory")
            os.chmod(MOUNT_PATH, 0o755)  # rwxr-xr-x
            success = True
        else:
            # Try with command line
            debug_log("Directory not created, trying with mkdir command")
            subprocess.run(["mkdir", "-p", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            success = os.path.exists(MOUNT_PATH)
    except Exception as e:
        debug_log(f"Failed to create mount point directory: {e}")
        success = False
        
    debug_log(f"Reset mount point {'successful' if success else 'failed'}")
    return success

def mount_iphone(documents_mode=False):
    """Mount iPhone filesystem
    
    Args:
        documents_mode: If True, mount a specific app's Documents folder
    """
    global CURRENT_MOUNT_TYPE, CURRENT_APP_ID
    debug_log(f"mount_iphone called with documents_mode={documents_mode}")
    
    # First ensure the mount point is clean
    if os.path.exists(MOUNT_PATH):
        if check_mount():
            debug_log("iPhone already mounted")
            messagebox.showinfo("Already Mounted", "iPhone is already mounted.")
            list_files()
            return
        # Directory exists but not mounted - we can proceed
        debug_log(f"Mount path exists but not mounted: {MOUNT_PATH}")
    else:
        try:
            debug_log(f"Creating mount path: {MOUNT_PATH}")
            os.makedirs(MOUNT_PATH, exist_ok=True)
        except Exception as e:
            debug_log(f"Failed to create mount directory: {str(e)}")
            # Try to reset the mount point
            if not reset_mount_point():
                messagebox.showerror("Error", f"Failed to create mount directory: {str(e)}\n\nTry manually running: mkdir -p ~/iPhoneMount")
                return

    try:
        # First unmount if any stale mount exists
        debug_log("Attempting to unmount any stale mount")
        subprocess.run(["fusermount", "-u", MOUNT_PATH], stderr=subprocess.PIPE)
        
        # Reset mount type tracking
        CURRENT_MOUNT_TYPE = None
        CURRENT_APP_ID = None
        
        # Try to clean up non-empty mount point by removing any files
        try:
            debug_log("Cleaning mount point directory")
            for item in os.listdir(MOUNT_PATH):
                item_path = os.path.join(MOUNT_PATH, item)
                if os.path.isfile(item_path):
                    debug_log(f"Removing file: {item_path}")
                    os.remove(item_path)
        except Exception as e:
            # Just log, don't stop the process
            debug_log(f"Warning: Could not clean mount directory: {e}")
            
        # Get the device UDID for more reliable mounting
        debug_log("Getting device UDID")
        udid = get_device_udid()
        if not udid:
            debug_log("No iPhone device found")
            messagebox.showerror("Error", "No iPhone device found. Please make sure it's connected and unlocked.")
            return
            
        debug_log(f"Found device with UDID: {udid}")
        
        # Use the UDID for more reliable mounting
        command = ["ifuse", "--udid", udid]
        
        # If documents mode is requested, prompt for app selection
        if documents_mode:
            debug_log("Documents mode requested, showing app selection dialog")
            
            app_id = select_app_dialog()
            debug_log(f"App selected: {app_id}")
            
            if not app_id:
                debug_log("App selection canceled or no app selected")
                update_status("Status: App selection canceled")
                return  # User canceled
                
            # Store the app ID globally
            CURRENT_APP_ID = app_id
            
            debug_log(f"Adding --documents flag with app: {app_id}")
            command.extend(["--documents", app_id])
            update_status(f"Status: Mounting documents for app {app_id}...")
        else:
            debug_log("Using standard media mount mode")
            update_status(f"Status: Mounting media (mostly read-only)...")
            
        # Add nonempty option to handle non-empty mount point
        debug_log("Adding nonempty option")
        command.extend(["-o", "nonempty"])
            
        # Add mount point
        command.append(MOUNT_PATH)
        
        debug_log(f"Running mount command: {' '.join(command)}")
        # Update UI before running the mount command
        root.update_idletasks()
        
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        debug_log(f"Mount command exit code: {result.returncode}")
        debug_log(f"Mount command stdout: {result.stdout}")
        debug_log(f"Mount command stderr: {result.stderr}")
        
        if check_mount():
            debug_log("Mount successful, updating UI")
            if documents_mode:
                # Set the mount type
                CURRENT_MOUNT_TYPE = "documents"
                messagebox.showinfo("Mounted", f"App documents folder mounted successfully.\n\nYou can now upload files to this app.")
                update_status(f"Status: App '{app_id}' documents mounted (read-write)")
            else:
                # Set the mount type
                CURRENT_MOUNT_TYPE = "media"
                messagebox.showinfo("Mounted", "iPhone media mounted successfully (mostly read-only).")
                update_status("Status: iPhone media mounted (read-only)")
            list_files()
        else:
            debug_log("Mount failed, checking error messages")
            error = result.stderr.decode('utf-8') if result.stderr else "Unknown error"
            if "No device found" in error:
                debug_log("No device found error")
                messagebox.showerror("Error", "No iPhone device found. Please make sure it's connected and unlocked.")
                update_status("Status: No device found")
            elif "Permission denied" in error:
                debug_log("Permission denied error")
                messagebox.showerror("Error", "Permission denied when mounting iPhone.\n\nTry running the app with sudo or as root.")
                update_status("Status: Permission denied mounting iPhone")
            else:
                debug_log(f"Other mount error: {error}")
                messagebox.showerror("Error", f"Failed to mount iPhone: {error}")
                update_status(f"Status: Mount error - {error[:30]}...")
    except Exception as e:
        debug_log(f"Exception during mount: {str(e)}")
        debug_log(traceback.format_exc())
        messagebox.showerror("Error", f"Mount error: {str(e)}")
        update_status(f"Status: Error - {str(e)[:30]}...")

def mount_iphone_documents():
    """Mount documents folder of a selected app (allows file transfers)"""
    mount_iphone(documents_mode=True)

def unmount_iphone():
    global CURRENT_MOUNT_TYPE, CURRENT_APP_ID
    if not check_mount():
        messagebox.showinfo("Not Mounted", "iPhone is not currently mounted.")
        return
        
    try:
        update_status("Status: Unmounting...")
        result = subprocess.run(["fusermount", "-u", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        debug_log(f"Unmount exit code: {result.returncode}")
        
        if result.returncode != 0:
            debug_log(f"Standard unmount failed, trying force unmount")
            # Try more aggressive unmounting
            subprocess.run(["fusermount", "-uz", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        if not check_mount():
            messagebox.showinfo("Unmounted", "iPhone unmounted successfully.")
            update_status("Status: iPhone unmounted successfully")
            # Clear the file list
            file_list.delete(0, END)
            # Reset mount type tracking
            CURRENT_MOUNT_TYPE = None
            CURRENT_APP_ID = None
        else:
            # If still mounted, provide more detailed error
            error_output = result.stderr.decode('utf-8') if result.stderr else "Unknown error"
            debug_log(f"Failed to unmount. Error: {error_output}")
            messagebox.showerror("Error", f"Failed to unmount iPhone: {error_output}\n\nTry the 'Deep Clean Mount' option.")
            update_status("Status: Unmount failed")
    except Exception as e:
        debug_log(f"Unmount error: {str(e)}")
        messagebox.showerror("Error", f"Unmount error: {str(e)}")
        update_status(f"Status: Error - {str(e)[:30]}...")

def is_system_file(filename):
    """Check if a file is a system file that should be hidden from users

    Args:
        filename: The name of the file to check

    Returns:
        bool: True if the file should be hidden, False otherwise
    """
    # System files and metadata files to ignore
    system_patterns = [
        # File extensions
        '.lock',        # Lock files
        '.DS_Store',    # macOS metadata
        '.ithmb',       # iOS thumbnail images
        '.plist',       # Property list files
        '.albummetadata', # Album metadata
        '.memorymetadata', # Memory metadata
        '.facemetadata',  # Face recognition metadata
        '.log',         # Log files
        '.sqlite',      # SQLite database files
        '.sqlitedb',    # SQLite database files
        '.sqlite-shm',  # SQLite shared memory files
        '.sqlite-wal',  # SQLite write-ahead log
        '.db',          # Database files
        '.dat',         # Data files
        '.tmp',         # Temporary files
        '.pb',          # iOS property list backups
        '.cache',       # Cache files
        '.ptl',         # iOS portal files
        '.crashreport', # Crash reports
        '.btree',       # B-tree index files
        '.strings',     # String resource files
        '.itc',         # iTunes cache files
        '.itdb',        # iTunes database files
        '.itl',         # iTunes library files
        '.bak',         # Backup files
        '.mdbackup',    # Mobile device backup files
        '.mddata',      # Mobile device data files
        '.thumb',       # Thumbnail files
        '.journal',     # Journal files
        '.synctoken',   # Sync token files
        '.artwork',     # Artwork cache files
        '.bat',         # Batch files
        
        # File name patterns
        'Thumbs.db',    # Windows thumbnail cache
        'thumbs',       # Generic thumbnail files
        'iTunesMetadata', # iTunes metadata
        'iTunesArtwork', # iTunes artwork
        'iTunesPrefs',  # iTunes preferences
        'iTunesTouch',  # iTunes touch data
        'iTunesSync',   # iTunes sync data
        'CoverFlow',    # Cover flow cache
        'Manifest.',    # Manifest files
        'SyncData',     # Sync data
        'Recordings',   # Voice recordings metadata
        'PhotoData',    # Photo data
        '.config',      # Configuration files
        
        # Apple system files
        '.Trashes',     # iOS trash
        '__MACOSX',     # macOS resource fork
        '.fseventsd',   # iOS filesystem events
        '.metadata_',   # Generic metadata
        '.com.apple',   # Apple system files
        '._',           # macOS resource forks
        '.DocumentRevisions-',  # Document revisions
        'DCIM/.MISC',   # Camera misc data
    ]
    
    # Directories to completely ignore
    system_directories = [
        # Photo and media related directories
        'PhotoData/Catches',
        'PhotoData/AlbumsMetadata',
        'PhotoData/Mutations',
        'PhotoData/Sync',
        'PhotoData/Thumbnails',
        'PhotoData/Videos',
        'PhotoData/CPLAssets',
        'PhotoData/Metadata',
        'MediaAnalysis',
        'MotionAssets'
        
        # System directories
        'iTunes_Control/',
        'iTunes-control',
        'iTunesControl',
        'Books/',
        'Podcasts/',
        'Recordings/',
        'Purchases/',
        
        # Cache and metadata directories
        '.Spotlight-V100',
        '.DocumentRevisions-V100',
        '.TemporaryItems',
        '.Trashes',
        '.fseventsd',
        '.Trash',
        '.com.apple',
        
        # System folders
        'DCIM/.MISC',
        'DCIM/.thumbnails',
        'DCIM/.TRACES',
        'DCIM/.MISC',
        'System/',
        'private/var/mobile/Library/Caches',
        'private/var/mobile/Library/Logs',
        'private/var/mobile/Library/Preferences',
        'private/var/root',
        'private/var/Keychains',
        'private/var/stash',
        'private/etc',
        'private/tmp',
        
        # Device firmware and backup
        'System/Library',
        'System/Library/Lockdown',
        'System/Library/Caches',
        'System/Library/LaunchDaemons',
        'private/var/MobileDevice',
        'private/var/MobileDevice/ProvisioningProfiles',
        'private/var/containers',
        'private/var/db',
        'private/var/keybags'
    ]
    
    # Check if the filename is in or starts with any system directory
    for directory in system_directories:
        normalized_dir = directory.rstrip('/')  # Handle trailing slash variations
        if filename.startswith(normalized_dir + '/') or filename == normalized_dir:
            return True
    
    # Check if the filename matches any of the system patterns
    for pattern in system_patterns:
        if pattern in filename:
            return True
    
    # Check if the filename starts with a dot (hidden files)
    if os.path.basename(filename).startswith('.'):
        return True
        
    return False

def list_files():
    try:
        file_list.delete(0, END)
        if check_mount():
            try:
                update_status("Status: Listing files...")
                
                file_count = 0
                skipped_count = 0
                batch_size = 100  # Process files in batches for better UI responsiveness
                current_batch = []
                max_files = 5000  # Limit max files to show for performance
                reached_limit = False
                
                # Add a header if we're in documents mode
                current_mount_type = get_mount_type()
                if current_mount_type and "documents" in current_mount_type:
                    # Add a special informational header
                    file_list.insert(END, "--- App Documents Folder ---")
                    file_list.insert(END, "Files saved here will be available in the app on your iPhone")
                    file_list.insert(END, "")
                
                # Define system directories to skip directly in this function
                system_dirs_to_skip = [
                    # Photo and media related directories
                    'PhotoData/Catches',
                    'PhotoData/AlbumsMetadata',
                    'PhotoData/Mutations',
                    'PhotoData/Sync',
                    'PhotoData/Thumbnails',
                    'PhotoData/Videos',
                    'PhotoData/CPLAssets',
                    'PhotoData/Metadata',
                    'MediaAnalysis',
                    'MotionAssets',
                    
                    # System directories
                    'iTunes_Control/',
                    'iTunes-control',
                    'iTunesControl',
                    'Books/',
                    'Podcasts/',
                    'Recordings/',
                    'Purchases/',
                    
                    # Cache and metadata directories
                    '.Spotlight-V100',
                    '.DocumentRevisions-V100',
                    '.TemporaryItems',
                    '.Trashes',
                    '.fseventsd',
                    '.Trash',
                    '.com.apple',
                    
                    # System folders
                    'DCIM/.MISC',
                    'DCIM/.thumbnails',
                    'DCIM/.TRACES',
                    'DCIM/.MISC',
                    'System/',
                    'private/var/mobile/Library/Caches',
                    'private/var/mobile/Library/Logs',
                    'private/var/mobile/Library/Preferences',
                    'private/var/root',
                    'private/var/Keychains',
                    'private/var/stash',
                    'private/etc',
                    'private/tmp'
                ]
                
                # Normalize the directory paths
                normalized_dirs = []
                for directory in system_dirs_to_skip:
                    normalized_dirs.append(directory.rstrip('/'))
                
                # More efficient walking with early directory skipping
                remaining_files = []
                
                for root_dir, dirs, files in os.walk(MOUNT_PATH):
                    try:
                        # Skip unwanted directories early
                        rel_root = os.path.relpath(root_dir, MOUNT_PATH)
                        if rel_root != '.' and any(rel_root == skip_dir or rel_root.startswith(skip_dir + '/') for skip_dir in normalized_dirs):
                            # Remove all subdirs to prevent further walking into this branch
                            dirs.clear()
                            continue
                        
                        # Filter directories list in-place to skip system folders
                        i = 0
                        while i < len(dirs):
                            dir_path = os.path.join(rel_root, dirs[i]) if rel_root != '.' else dirs[i]
                            # Skip system directories
                            if CURRENT_MOUNT_TYPE == "media" and any(dir_path == skip_dir or dir_path.startswith(skip_dir + '/') for skip_dir in normalized_dirs):
                                dirs.pop(i)  # Remove this directory from walk
                            else:
                                i += 1
                                
                        for f in files:
                            if not file_list.winfo_exists():
                                return  # Widget destroyed
                            
                            full_path = os.path.join(root_dir, f)
                            relative_path = os.path.relpath(full_path, MOUNT_PATH)
                            
                            # Skip system files in media mode (faster check with less string operations)
                            if CURRENT_MOUNT_TYPE == "media":
                                # Fast check for common file extensions and patterns first
                                basename = os.path.basename(relative_path)
                                if basename.startswith('.') or '.cache' in relative_path or '.plist' in relative_path:
                                    skipped_count += 1
                                    continue
                                
                                # Then do full check only if needed
                                if is_system_file(relative_path):
                                    skipped_count += 1
                                    continue
                            
                            # Add to current batch
                            current_batch.append(relative_path)
                            file_count += 1
                            
                            # Process batch
                            if len(current_batch) >= batch_size:
                                # Check if we've hit the file limit
                                if file_count > max_files:
                                    reached_limit = True
                                    remaining_files = current_batch
                                    break
                                    
                                # Update UI with this batch
                                for item in current_batch:
                                    file_list.insert(END, item)
                                
                                # Clear batch and update UI
                                current_batch = []
                                update_status(f"Status: Listed {file_count} files...")
                                root.update_idletasks()
                        
                        # If we've hit the limit, stop walking
                        if reached_limit:
                            break
                            
                    except Exception as e:
                        debug_log(f"Error processing directory {root_dir}: {e}")
                        continue  # Continue with next directory
                
                # Add any remaining files in the last batch
                for item in current_batch:
                    if len(remaining_files) < max_files:
                        file_list.insert(END, item)
                
                # Add instructions if empty folder            
                if file_count == 0 and current_mount_type and "documents" in current_mount_type:
                    file_list.insert(END, "This folder is empty.")
                    file_list.insert(END, "Use the 'Upload File to iPhone' button to upload files.")
                
                # Show message if we hit the display limit
                if reached_limit:
                    file_list.insert(END, "")
                    file_list.insert(END, f"--- Only showing {max_files} of {file_count + skipped_count} files ---")
                    file_list.insert(END, "Use the search feature to find specific files")
                
                status_message = f"Status: iPhone mounted - {file_count} files listed"
                if skipped_count > 0:
                    status_message += f" ({skipped_count} system files hidden)"
                if reached_limit:
                    status_message += f" (display limited to {max_files} files)"
                    
                update_status(status_message)
                debug_log(f"Listed {file_count} files, hid {skipped_count} system files")
                
            except tk.TclError:
                # Widget destroyed
                return
            except Exception as e:
                messagebox.showerror("Error", f"Failed to list files: {str(e)}")
                update_status(f"Status: Error listing files - {str(e)[:30]}...")
        else:
            update_status("Status: iPhone not mounted")
            messagebox.showerror("Error", "iPhone not mounted.")
    except tk.TclError:
        # Widget destroyed
        return

def get_mount_type():
    """Check what type of mount we currently have"""
    try:
        debug_log("Checking mount type")
        result = subprocess.run(["mount"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if MOUNT_PATH in line:
                debug_log(f"Mount line: {line}")
                return line
    except Exception as e:
        debug_log(f"Error checking mount type: {e}")
    return None

def is_documents_mount():
    """Check if the current mount is a documents mount"""
    global CURRENT_MOUNT_TYPE
    debug_log(f"Checking if documents mount. Current mount type: {CURRENT_MOUNT_TYPE}")
    
    # First check our internal tracking
    if CURRENT_MOUNT_TYPE == "documents":
        return True
        
    # Fallback to checking mount info
    mount_info = get_mount_type()
    debug_log(f"Mount info from system: {mount_info}")
    
    if not mount_info:
        return False
        
    # Look for documents in the mount info
    is_docs = "documents" in mount_info.lower() or "--documents" in mount_info.lower()
    
    # Update our internal tracking if we found something
    if is_docs:
        CURRENT_MOUNT_TYPE = "documents"
    elif check_mount():
        CURRENT_MOUNT_TYPE = "media"
    else:
        CURRENT_MOUNT_TYPE = None
        
    return is_docs

def download_file():
    try:
        selected = file_list.curselection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select one or more files to download first.")
            return
            
        # Handle multiple selections
        if len(selected) == 1:
            # Single file download - ask for destination
            selected_file = file_list.get(selected[0])
            if selected_file.startswith("---") or not selected_file.strip():
                messagebox.showinfo("Invalid Selection", "Please select a valid file to download.")
                return
                
            source_path = os.path.join(MOUNT_PATH, selected_file)
            
            if not os.path.exists(source_path):
                messagebox.showerror("Error", f"Source file not found: {source_path}")
                return
                
            save_path = filedialog.asksaveasfilename(initialfile=os.path.basename(selected_file))
            if save_path:
                update_status(f"Status: Downloading {os.path.basename(selected_file)}...")
                
                shutil.copy2(source_path, save_path)
                messagebox.showinfo("Saved", f"File saved to {save_path}")
                update_status(f"Status: Downloaded to {os.path.basename(save_path)}")
        else:
            # Multiple files download - ask for destination directory
            dir_path = filedialog.askdirectory(title="Select Download Destination Folder")
            if not dir_path:
                return  # User canceled
                
            # Count valid selections (skip header/info lines)
            valid_files = []
            for idx in selected:
                selected_file = file_list.get(idx)
                if not selected_file.startswith("---") and selected_file.strip():
                    source_path = os.path.join(MOUNT_PATH, selected_file)
                    if os.path.exists(source_path) and os.path.isfile(source_path):
                        valid_files.append((source_path, selected_file))
            
            if not valid_files:
                messagebox.showinfo("Invalid Selection", "No valid files selected for download.")
                return
            
            # Confirm the operation
            count = len(valid_files)
            if not messagebox.askyesno("Confirm Download", f"Download {count} files to {dir_path}?"):
                return
                
            # Download all selected files
            success_count = 0
            fail_count = 0
            
            for i, (source_path, file_path) in enumerate(valid_files):
                try:
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(dir_path, filename)
                    
                    # Update status every file
                    update_status(f"Status: Downloading file {i+1} of {count}: {filename}...")
                    root.update_idletasks()
                    
                    # Copy the file
                    shutil.copy2(source_path, dest_path)
                    success_count += 1
                    
                    # Update UI every 5 files
                    if i % 5 == 0:
                        root.update_idletasks()
                except Exception as e:
                    debug_log(f"Error downloading {file_path}: {e}")
                    fail_count += 1
            
            # Show summary
            if fail_count > 0:
                messagebox.showinfo("Download Summary", 
                                   f"Downloaded {success_count} files successfully.\n"
                                   f"Failed to download {fail_count} files.")
                update_status(f"Status: Downloaded {success_count} files, {fail_count} failed")
            else:
                messagebox.showinfo("Download Complete", f"Successfully downloaded {success_count} files to {dir_path}")
                update_status(f"Status: Downloaded {success_count} files")
    except tk.TclError:
        # Widget destroyed
        return
    except Exception as e:
        messagebox.showerror("Error", f"Download error: {str(e)}")
        update_status(f"Status: Download error - {str(e)[:30]}...")

def upload_file():
    if not check_mount():
        messagebox.showerror("Error", "iPhone not mounted.")
        return
        
    # Check if we're in documents mode which allows uploads
    debug_log("Checking mount type for upload")
    is_docs_mode = is_documents_mount()
    debug_log(f"Documents mode: {is_docs_mode}")
    
    if not is_docs_mode:
        messagebox.showinfo("Documents Mode Required", 
                          "To upload files, you need to mount in Documents mode.\n\n"
                          "Please unmount first, then use 'Mount Documents' instead.")
        return
        
    file_path = filedialog.askopenfilename()
    if not file_path:
        return  # User canceled
        
    try:
        # Get basename for destination
        filename = os.path.basename(file_path)
        dest = os.path.join(MOUNT_PATH, filename)
        
        update_status(f"Status: Uploading {filename}...")
        
        try:
            # Use a chunk-by-chunk copy method which is more reliable on iOS
            debug_log(f"Attempting chunk-by-chunk copy from {file_path} to {dest}")
            
            # Get file size for progress updates
            file_size = os.path.getsize(file_path)
            
            # Use binary mode for consistent behavior
            with open(file_path, 'rb') as src_file:
                try:
                    with open(dest, 'wb') as dest_file:
                        copied = 0
                        chunk_size = 1024 * 64  # 64KB chunks
                        
                        while True:
                            chunk = src_file.read(chunk_size)
                            if not chunk:
                                break
                                
                            dest_file.write(chunk)
                            copied += len(chunk)
                            
                            # Update progress every 10 chunks
                            if copied % (chunk_size * 10) < chunk_size:
                                percent = int((copied / file_size) * 100)
                                update_status(f"Status: Uploading {filename} ({percent}%)...")
                                root.update_idletasks()
                    
                    debug_log(f"File copy successful: {filename}")
                    messagebox.showinfo("Uploaded", f"File {filename} uploaded to iPhone.\n\n" +
                                      "You can access this file in the app on your iPhone.")
                    update_status(f"Status: Uploaded {filename}")
                    
                    # Refresh the file list
                    list_files()
                    
                except PermissionError as e:
                    debug_log(f"Permission error during file writing: {e}")
                    raise
                except OSError as e:
                    debug_log(f"OS error during file writing: {e}")
                    
                    # If dest file exists but is incomplete, try to remove it
                    if os.path.exists(dest):
                        try:
                            os.remove(dest)
                            debug_log(f"Removed incomplete file: {dest}")
                        except:
                            pass
                    
                    if "Function not implemented" in str(e):
                        # This is a common error with ifuse/iOS
                        messagebox.showerror("iOS Limitation", 
                                          "This iOS app's Documents folder doesn't support file uploads.\n\n" +
                                          "Try these solutions:\n" +
                                          "1. Try a different app (Firefox, Chrome often work)\n" +
                                          "2. Use iTunes file sharing instead\n" +
                                          "3. Use native iOS file sharing features")
                        update_status("Status: This app doesn't support file uploads")
                    else:
                        raise
                    
        except PermissionError as e:
            debug_log(f"Permission error: {e}")
            messagebox.showerror("Permission Error", 
                               "Cannot write to iPhone filesystem. This may be due to iOS restrictions.\n\n"
                               "Try these solutions:\n"
                               "1. Make sure you're in Documents mount mode\n"
                               "2. Try a different app's Documents folder\n"
                               "3. Check if your iPhone is locked")
            update_status("Status: Upload failed - Permission error")
        except OSError as e:
            debug_log(f"OS error: {e}")
            if "Function not implemented" in str(e):
                messagebox.showerror("iOS Limitation", 
                                   "This iOS app's Documents folder doesn't support file uploads.\n\n" +
                                   "Try these solutions:\n" +
                                   "1. Try a different app (Firefox, Chrome often work)\n" +
                                   "2. Use iTunes file sharing instead\n" +
                                   "3. Use native iOS file sharing features")
                update_status("Status: This app doesn't support file uploads")
            else:
                raise
                
    except tk.TclError:
        # Widget destroyed
        return
    except Exception as e:
        debug_log(f"Upload error: {e}")
        messagebox.showerror("Error", f"Upload error: {str(e)}\n\nThis might be due to iOS restrictions on file writing.")
        update_status(f"Status: Upload error - {str(e)[:30]}...")

def show_help():
    """Display help information about iPhone file transfers"""
    help_text = """
iPhone File Transfer Help:

Different Mounting Modes:
------------------------
1. Media Mode (Read-Only):
   - Allows access to photos, videos, and music
   - Generally doesn't allow writing files to the iPhone
   - Good for downloading media from your iPhone

2. Documents Mode (Read-Write):
   - Accesses a specific app's Documents folder
   - Allows both reading and writing files
   - Each app has its own isolated folder
   - Allows you to upload files to your iPhone

Common Issues:
------------
- "Failed to mount directory: File exists" error:
   This happens when the mount point directory has issues.
   Click the "Reset Mount Point" button to fix it.
   If that doesn't work, try the "Deep Clean Mount" button.
   
- "Function not implemented" error:
   This is due to iOS restrictions on writing to certain locations.
   Try using Documents mode with a different app.
   Not all iOS apps support file uploads - try Firefox or Chrome.

- Permission errors:
   iOS strictly controls what files can be modified.
   Try a different app like Firefox, Chrome, or Acrobat.

- Mounting doesn't work at all:
   1. Make sure your iPhone is unlocked
   2. Try the "Reset Mount Point" button
   3. If that fails, try "Deep Clean Mount" (requires sudo)
   4. Restart the app or your computer
   5. Check if ifuse is installed correctly

Special Utility Buttons:
---------------------
- Reset Mount Point: Cleans and recreates the mount directory
- Deep Clean Mount: Uses sudo to forcibly fix mount issues
- Toggle Debug: Enables detailed logging for troubleshooting

Tips:
----
- Always make sure your iPhone is unlocked
- You may need to trust your computer on iPhone
- Some folders will remain read-only due to iOS security
- For file uploads, use file based apps like Xender or Documents by Readle or Chrome or any other file based app
"""
    # Create a scrollable help window
    help_window = tk.Toplevel(root)
    help_window.title("iPhone File Transfer Help")
    help_window.geometry("600x500")
    help_window.transient(root)  # Set as transient to root
    help_window.grab_set()  # Make help window modal
    
    # Create frame for the text and scrollbar
    text_frame = Frame(help_window)
    text_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Add scrollbar
    scrollbar = Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    # Create text widget with scrollbar
    text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_widget.yview)
    
    # Insert the help text
    text_widget.insert("1.0", help_text)
    text_widget.config(state="disabled")  # Make text read-only
    
    # Button at bottom to close
    Button(help_window, text="Close", command=help_window.destroy, width=10).pack(pady=10)
    
    # Center the window
    help_window.update_idletasks()
    width = help_window.winfo_width()
    height = help_window.winfo_height()
    x = (help_window.winfo_screenwidth() // 2) - (width // 2)
    y = (help_window.winfo_screenheight() // 2) - (height // 2)
    help_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Force focus on help window
    help_window.focus_force()

def on_closing():
    """Handle window closing event"""
    try:
        if check_mount():
            debug_log("Closing window while iPhone mounted, asking user to unmount")
            if messagebox.askyesno("Unmount iPhone", "iPhone is still mounted. Unmount before exiting?"):
                try:
                    debug_log("User chose to unmount before exit")
                    # Try standard unmount first
                    result = subprocess.run(["fusermount", "-u", MOUNT_PATH], 
                                         stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                         check=False)
                    if result.returncode != 0:
                        # If that fails, try force unmount
                        subprocess.run(["fusermount", "-uz", MOUNT_PATH], 
                                     stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                     check=False)
                    debug_log("Unmount attempt completed")
                except Exception as e:
                    debug_log(f"Unmount error: {str(e)}")
                    print(f"Unmount error: {str(e)}")
        debug_log("Cleaning up and exiting")
        
        # Try to release the lock
        try:
            if 'lock_socket' in globals():
                lock_socket.close()
        except:
            pass
            
        root.destroy()
    except Exception as e:
        debug_log(f"Error closing application: {str(e)}")
        debug_log(traceback.format_exc())
        print(f"Error closing application: {str(e)}")
        try:
            root.destroy()
        except:
            pass
    # Force exit to avoid hanging threads
    os._exit(0)

def deep_clean_mount_point():
    """Perform a deep clean of the mount point using sudo if available"""
    try:
        debug_log("Performing deep clean of mount point")
        
        # First try basic unmount
        subprocess.run(["fusermount", "-u", MOUNT_PATH], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        # Try to use sudo to fix permissions and clean up
        commands = [
            ["sudo", "umount", "-f", MOUNT_PATH],
            ["sudo", "rm", "-rf", MOUNT_PATH],
            ["sudo", "mkdir", "-p", MOUNT_PATH],
            ["sudo", "chown", f"{os.getuid()}:{os.getgid()}", MOUNT_PATH],
            ["sudo", "chmod", "755", MOUNT_PATH]
        ]
        
        for cmd in commands:
            debug_log(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            debug_log(f"Result: {result.returncode}")
        
        if os.path.exists(MOUNT_PATH) and os.access(MOUNT_PATH, os.W_OK):
            debug_log("Deep clean successful")
            messagebox.showinfo("Deep Clean", "Successfully performed deep clean of mount point.")
            update_status("Status: Mount point deep cleaned")
            return True
        else:
            debug_log("Deep clean failed to create writable directory")
            messagebox.showerror("Deep Clean Failed", 
                               "Could not create a writable mount point.\n\n"
                               "Try running the following commands in terminal:\n"
                               "sudo fusermount -u ~/iPhoneMount\n"
                               "sudo rm -rf ~/iPhoneMount\n"
                               "mkdir -p ~/iPhoneMount")
            update_status("Status: Deep clean failed")
            return False
    except Exception as e:
        debug_log(f"Deep clean error: {e}")
        messagebox.showerror("Deep Clean Error", f"Error during deep clean: {str(e)}")
        update_status("Status: Deep clean error")
        return False

def reset_mount_point_ui():
    """Reset the mount point directory with UI feedback"""
    if check_mount():
        if not messagebox.askyesno("Confirmation", "iPhone is currently mounted. Unmount and reset mount point?"):
            return
    
    update_status("Status: Resetting mount point...")
    if reset_mount_point():
        messagebox.showinfo("Success", "Mount point has been reset successfully.\n\nTry mounting your iPhone again.")
        update_status("Status: Mount point reset complete")
    else:
        if messagebox.askyesno("Reset Failed", 
                             "Standard reset failed. Would you like to attempt a deep clean?\n\n"
                             "This will use sudo and require your password in the terminal."):
            deep_clean_mount_point()
        else:
            messagebox.showerror("Error", "Failed to reset mount point. Try manually fixing in terminal.")
            update_status("Status: Failed to reset mount point")

def toggle_debug_mode():
    """Toggle debug mode on/off"""
    global DEBUG
    DEBUG = not DEBUG
    debug_status = "enabled" if DEBUG else "disabled"
    update_status(f"Status: Debug mode {debug_status}")
    
    if DEBUG:
        # Show immediate feedback
        debug_log("Debug mode enabled")
        debug_log(f"Current mount type: {CURRENT_MOUNT_TYPE}")
        debug_log(f"Current app ID: {CURRENT_APP_ID}")
        debug_log(f"Is mounted: {check_mount()}")
        debug_log(f"Mount info: {get_mount_type()}")
        messagebox.showinfo("Debug Mode", f"Debug mode enabled. Check console for detailed logs.")

def check_instance_running():
    """Check if another instance of the app is already running using a lock file"""
    try:
        # Try to create a lock socket
        global lock_socket
        lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        lock_socket.bind('\0' + 'iphone_file_transfer_lock')
        debug_log("No other instance detected, proceeding")
        return False
    except:
        debug_log("Another instance is already running")
        return True

def search_files():
    """Search for files in the current list view"""
    if not check_mount():
        messagebox.showerror("Error", "iPhone not mounted.")
        return
        
    # Create a search dialog
    search_window = tk.Toplevel(root)
    search_window.title("Search Files")
    search_window.geometry("400x100")
    search_window.transient(root)
    search_window.grab_set()
    
    # Search frame
    search_frame = Frame(search_window)
    search_frame.pack(fill="x", padx=10, pady=10)
    
    Label(search_frame, text="Search:").pack(side="left", padx=5)
    search_var = StringVar()
    search_entry = Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=5, expand=True, fill="x")
    search_entry.focus_set()
    
    result_label = Label(search_window, text="")
    result_label.pack(pady=5)
    
    def do_search():
        search_term = search_var.get().strip().lower()
        if not search_term:
            return
            
        # Clear current selection
        file_list.selection_clear(0, END)
        
        # Find matches
        matches = 0
        for i in range(file_list.size()):
            item = file_list.get(i)
            if search_term in item.lower():
                file_list.selection_set(i)
                if matches == 0:  # Ensure first match is visible
                    file_list.see(i)
                matches += 1
                
        if matches > 0:
            result_label.config(text=f"Found {matches} matching files")
            search_window.focus_set()  # Return focus to search dialog
        else:
            result_label.config(text="No matches found")
    
    # Buttons
    button_frame = Frame(search_window)
    button_frame.pack(fill="x", padx=10, pady=5)
    
    Button(button_frame, text="Search", command=do_search, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Close", command=search_window.destroy, width=10).pack(side="right", padx=5)
    
    # Bind Enter key to search
    search_entry.bind("<Return>", lambda event: do_search())

def show_about():
    """Display information about the application"""
    about_text = f"""
{APP_NAME} v{APP_VERSION}

{APP_DESCRIPTION}

A simple utility to transfer files between 
Linux and iOS devices (iPhone, iPad).

System Information:
- OS: {platform.system()} {platform.release()}
- Python: {platform.python_version()}
- Tkinter: {tk.TkVersion}

Requirements:
- ifuse (for mounting iOS devices)
- libimobiledevice (for device communication)
- usbmuxd (for USB connection)

Copyright © 2025 - present
Licensed under MIT License
"""
    # Create about window
    about_window = tk.Toplevel(root)
    about_window.title(f"About {APP_NAME}")
    about_window.geometry("400x350")
    about_window.transient(root)
    about_window.grab_set()
    
    # Icon/logo placeholder
    logo_frame = Frame(about_window, height=60)
    logo_frame.pack(fill="x", pady=10)
    
    Label(logo_frame, text="📱", font=("Helvetica", 24)).pack()
    Label(about_window, text=APP_NAME, font=("Helvetica", 16, "bold")).pack()
    Label(about_window, text=f"Version {APP_VERSION}", font=("Helvetica", 10)).pack()
    
    # About text
    text_frame = Frame(about_window)
    text_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    text_widget = tk.Text(text_frame, wrap="word", height=12, width=40)
    text_widget.pack(fill="both", expand=True)
    text_widget.insert("1.0", about_text)
    text_widget.config(state="disabled")
    
    # Close button
    Button(about_window, text="Close", command=about_window.destroy, width=10).pack(pady=10)
    
    # Center window
    about_window.update_idletasks()
    width = about_window.winfo_width()
    height = about_window.winfo_height()
    x = (about_window.winfo_screenwidth() // 2) - (width // 2)
    y = (about_window.winfo_screenheight() // 2) - (height // 2)
    about_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def main():
    """Entry point for command line usage"""
    # Check for command line options
    if len(sys.argv) > 1:
        if sys.argv[1] == "--version" or sys.argv[1] == "-v":
            print(f"{APP_NAME} v{APP_VERSION}")
            print(APP_DESCRIPTION)
            print(f"Copyright © 2025")
            sys.exit(0)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print(f"{APP_NAME} v{APP_VERSION} - {APP_DESCRIPTION}")
            print("\nUsage:")
            print("  plugnpass [OPTION]")
            print("\nOptions:")
            print("  -h, --help     Show this help message and exit")
            print("  -v, --version  Show version information and exit")
            print("  -d, --debug    Enable debug mode")
            print("\nFor more information, visit:")
            print("  https://github.com/adermgram/plugnpass")
            sys.exit(0)
        elif sys.argv[1] == "--debug" or sys.argv[1] == "-d":
            global DEBUG
            DEBUG = True
            print("Debug mode enabled")
    
    # Check if another instance is already running
    if check_instance_running():
        print(f"Another instance of {APP_NAME} is already running.")
        messagebox.showerror("Already Running", 
                           f"Another instance of {APP_NAME} is already running.\n\n"
                           "Please use the existing window.")
        sys.exit(1)
    
    # Check for requirements before starting
    missing_requirements = check_requirements()
    if missing_requirements:
        error_msg = "The following requirements are missing:\n\n"
        error_msg += "\n".join(missing_requirements)
        error_msg += "\n\nPlease install the required packages and try again."
        messagebox.showerror("Missing Requirements", error_msg)
        sys.exit(1)
        
    try:
        global root
        root = tk.Tk()
        root.title(f"{APP_NAME} v{APP_VERSION} - {APP_DESCRIPTION}")
        root.geometry("750x550")
        root.protocol("WM_DELETE_WINDOW", on_closing)  # Handle window close event
        
        # Set up UI and other components
        setup_ui(root)
        
        # Check if the mount point is already mounted
        if check_mount():
            debug_log("iPhone already mounted at startup")
            update_status("Status: iPhone already mounted")
            root.after(500, list_files)  # Schedule listing files after UI is shown
        
        log_message(f"{APP_NAME} v{APP_VERSION} started successfully")
        root.mainloop()
    except Exception as e:
        error_msg = f"Main loop error: {str(e)}"
        log_message(error_msg, "ERROR")
        log_message(traceback.format_exc(), "ERROR")
        print(error_msg)
        sys.exit(1)

def setup_ui(root):
    """Set up the UI components"""
    global top_frame, status_label, button_frame, extra_frame, list_frame, file_list, scrollbar, bottom_frame
    
    # Top frame for title and status
    top_frame = Frame(root)
    top_frame.pack(fill="x", pady=5)
    
    Label(top_frame, text=f"📱 {APP_NAME}", font=("Helvetica", 14)).pack(side="left", padx=10)
    status_label = Label(top_frame, text="Status: Not connected", fg="gray")
    status_label.pack(side="right", padx=10)
    
    # Button frame
    button_frame = Frame(root)
    button_frame.pack(pady=5)
    
    Button(button_frame, text="Mount Media", command=mount_iphone, width=15).pack(side="left", padx=5)
    Button(button_frame, text="Mount Documents", command=mount_iphone_documents, width=15).pack(side="left", padx=5)
    Button(button_frame, text="Unmount", command=unmount_iphone, width=10).pack(side="left", padx=5)
    Button(button_frame, text="Refresh Files", command=list_files, width=10).pack(side="left", padx=5)
    
    # Extra button frame for utilities
    extra_frame = Frame(root)
    extra_frame.pack(pady=2)
    
    Button(extra_frame, text="Reset Mount Point", command=reset_mount_point_ui, width=15).pack(side="left", padx=5)
    Button(extra_frame, text="Deep Clean Mount", command=deep_clean_mount_point, width=15).pack(side="left", padx=5)
    Button(extra_frame, text="Search Files", command=search_files, width=10).pack(side="left", padx=5)
    Button(extra_frame, text="Help", command=show_help, width=10).pack(side="left", padx=5)
    
    # File list with scrollbar
    list_frame = Frame(root)
    list_frame.pack(fill="both", expand=True, pady=5, padx=10)
    
    scrollbar = Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")
    
    # Use extended selection mode to allow multiple file selection
    file_list = Listbox(list_frame, yscrollcommand=scrollbar.set, width=80, font=("Monospace", 10), selectmode="extended")
    file_list.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=file_list.yview)
    
    # Bottom button frame
    bottom_frame = Frame(root)
    bottom_frame.pack(pady=10)
    
    Button(bottom_frame, text="Upload File to iPhone", command=upload_file, width=20).pack(side="left", padx=5)
    Button(bottom_frame, text="Download Selected Files", command=download_file, width=20).pack(side="left", padx=5)
    Button(bottom_frame, text="About", command=show_about, width=10).pack(side="right", padx=5)

# If script is run directly, call the main function
if __name__ == "__main__":
    main()

