#!/usr/bin/env python3
"""
Script to downsample images by a factor of 2.
"""

import cv2
import numpy as np
from pathlib import Path
import os

# Define paths
#/home/pc-04/Research/_datasets/YJP_Lvl04_250828_DSLR/_source/editedFull
DATASET_NAME = "YJP_Lvl04_250828_DSLR"
INPUT_DIRECTORY = f"/home/pc-04/Research/_datasets/{DATASET_NAME}/_source/editedFull"
OUTPUT_DIRECTORY = f"/home/pc-04/Research/_datasets/{DATASET_NAME}/_source/3dgrut_images"
    

def downsample_images(input_dir, output_dir, scale_factor=2):
    """
    Downsample all images in input_dir by scale_factor and save to output_dir.
    
    Args:
        input_dir (str): Path to input images directory
        output_dir (str): Path to output images directory
        scale_factor (int): Factor to downsample by (default: 2)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
        image_files.extend(input_path.glob(f'*{ext.upper()}'))
    
    print(f"Found {len(image_files)} image files to process")
    
    processed_count = 0
    for img_file in image_files:
        try:
            # Read image
            img = cv2.imread(str(img_file))
            if img is None:
                print(f"Warning: Could not read {img_file}")
                continue
            
            # Get original dimensions
            height, width = img.shape[:2]
            new_height = height // scale_factor
            new_width = width // scale_factor
            
            # Downsample using INTER_AREA (best for downsampling)
            downsampled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Create output filename
            output_file = output_path / img_file.name
            
            # Save downsampled image
            cv2.imwrite(str(output_file), downsampled)
            
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"Processed {processed_count}/{len(image_files)} images")
                
        except Exception as e:
            print(f"Error processing {img_file}: {e}")
    
    print(f"Successfully processed {processed_count} images")
    print(f"Downsampled images saved to: {output_path}")

if __name__ == "__main__":
    
    print(f"Input directory: {INPUT_DIRECTORY}")
    print(f"Output directory: {OUTPUT_DIRECTORY}")
    
    # Check if input directory exists
    if not Path(INPUT_DIRECTORY).exists():
        print(f"Error: Input directory {INPUT_DIRECTORY} does not exist")
        exit(1)
    
    # Process images
    downsample_images(INPUT_DIRECTORY, OUTPUT_DIRECTORY, scale_factor=2)
