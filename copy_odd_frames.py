#!/usr/bin/env python3
"""
Script to copy every odd frame from source directory to destination directory.
Creates destination directory if it doesn't exist.
"""

import shutil
from pathlib import Path
import argparse


def copy_odd_frames(source_dir: Path, dest_dir: Path):
    """
    Copy every odd frame from source directory to destination directory.
    
    Args:
        source_dir: Source directory containing the frames
        dest_dir: Destination directory where odd frames will be copied
    """
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all image files from source directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = [f for f in source_dir.iterdir() 
                   if f.is_file() and f.suffix.lower() in image_extensions]
    
    # Sort files to ensure consistent ordering
    image_files.sort()
    
    print(f"Found {len(image_files)} image files in source directory")
    
    # Copy every odd frame (1st, 3rd, 5th, etc.)
    copied_count = 0
    for i, image_file in enumerate(image_files):
        if i % 2 == 0:  # Even index means odd frame (0-indexed)
            dest_file = dest_dir / image_file.name
            shutil.copy2(image_file, dest_file)
            copied_count += 1
            if copied_count % 100 == 0:  # Progress indicator
                print(f"Copied {copied_count} files...")
    
    print(f"Successfully copied {copied_count} odd frames to {dest_dir}")


def main():
    parser = argparse.ArgumentParser(description="Copy every odd frame from source to destination")
    parser.add_argument("source_dir", help="Source directory containing frames")
    parser.add_argument("dest_dir", help="Destination directory for odd frames")
    
    args = parser.parse_args()
    
    source_path = Path(args.source_dir)
    dest_path = Path(args.dest_dir)
    
    # Validate source directory exists
    if not source_path.exists():
        print(f"Error: Source directory '{source_path}' does not exist")
        return 1
    
    if not source_path.is_dir():
        print(f"Error: '{source_path}' is not a directory")
        return 1
    
    try:
        copy_odd_frames(source_path, dest_path)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
