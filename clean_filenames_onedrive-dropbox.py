import os
import re
import logging
from datetime import datetime

INVALID_NAMES = [".lock", "CON", "PRN", "AUX", "NUL", "_vti_", "desktop.ini"] + [f"COM{i}" for i in range(10)] + [f"LPT{i}" for i in range(10)]
INVALID_START = ["~$"]
INVALID_ROOT_FOLDERS = ["forms"]

def setup_logging():
    log_dir = os.path.expanduser('~/logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'clean-filenames_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(filename=log_file, 
                        level=logging.INFO, 
                        format='[%(asctime)s] %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')
    return log_file

def clean_name(name):
    valid_name = name
    # Filter for invalid characters
    valid_name = re.sub(r'[\\/*?:"<>|]', '', valid_name)
    valid_name = re.sub(r'^\.', '', valid_name)
    valid_name = ''.join(c for c in valid_name if c.isascii())
    valid_name = "" if valid_name in INVALID_NAMES or any(valid_name.startswith(prefix) for prefix in INVALID_START) else valid_name
    
    # Remove trailing whitespaces before the extension
    if valid_name:
        name_part, ext_part = os.path.splitext(valid_name)
        valid_name = f"{name_part.rstrip()}{ext_part}"
    
    return valid_name

def clean_files(root_dir):
    for filename in os.listdir(root_dir):
        full_path = os.path.join(root_dir, filename)
        if os.path.isfile(full_path):
            valid_filename = clean_name(filename)

            if filename != valid_filename:
                original = full_path
                new = os.path.join(root_dir, valid_filename)
                
                i = 1
                while os.path.exists(new) and valid_filename != "":
                    base, ext = os.path.splitext(valid_filename)
                    new = os.path.join(root_dir, f'{base}_{i}{ext}')
                    i += 1
                
                if valid_filename != "":
                    os.rename(original, new)
                    logging.info(f'Renamed file {original} to {new}')

        elif os.path.isdir(full_path):
            clean_files(full_path) # Recurse into subdirectories

def clean_folders(root_dir):
    for foldername in os.listdir(root_dir):
        full_path = os.path.join(root_dir, foldername)
        if os.path.isdir(full_path):
            valid_foldername = clean_name(foldername)

            if foldername != valid_foldername:
                original = full_path
                new = os.path.join(root_dir, valid_foldername)
                
                i = 1
                while os.path.exists(new) and valid_foldername != "":
                    new = os.path.join(root_dir, f'{valid_foldername}_{i}')
                    i += 1
                
                if valid_foldername != "":
                    os.rename(original, new)
                    logging.info(f'Renamed folder {original} to {new}')
                    clean_folders(new) # Recurse into subdirectories
                else:
                    clean_folders(original) # Recurse into original
            else:
                clean_folders(full_path) # Recurse into original


log_file = setup_logging()

try:
    # Call the function with the path of your Dropbox/OneDrive folder
    clean_files('F:\\tmp\\')
    clean_folders('F:\\tmp\\')
    print("Successfully cleaned files and folders. For more information, check the log file at: ", log_file)
except Exception as e:
    print("An error occurred while cleaning files and folders. Please check the log file at: ", log_file)
    logging.exception("Exception occurred")


# Windows path example:
# clean_files('C:\\Dropbox\\')

# macOS Path example:
# clean_files('~/Library/CloudStorage/OneDrive/')
