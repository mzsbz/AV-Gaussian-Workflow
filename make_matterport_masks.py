import config
import shutil
from pathlib import Path

# ===== User-configurable parameters =====
MASK_DIR: Path = Path(__file__).parent / "masks" / "matterport"
OUT_DIR: Path = config.DATASET_PATH / "colmap_runs" / config.DATA_VARIANT / "images"

def create_matterport_masks():
    """Create mask files for skybox images based on skybox number."""
    
    # Ensure MASK_DIR exists
    if not MASK_DIR.exists():
        print(f"Error: MASK_DIR does not exist: {MASK_DIR}")
        return
    
    # Ensure OUT_DIR exists
    if not OUT_DIR.exists():
        print(f"Error: OUT_DIR does not exist: {OUT_DIR}")
        return
    
    # Get all skybox images
    skybox_images = list(OUT_DIR.glob("*_skybox*.jpg"))
    
    if not skybox_images:
        print(f"No skybox images found in {OUT_DIR}")
        return
    
    print(f"Found {len(skybox_images)} skybox images")
    
    # Process each skybox image
    for image_path in skybox_images:
        image_name = image_path.stem  # Get filename without extension
        
        # Determine which mask to use based on skybox number
        if image_name.endswith("_skybox5"):
            # Use bottom_mask.png for skybox5
            source_mask = MASK_DIR / "bottom_mask.png"
            mask_name = f"{image_name}_mask.png"
        elif image_name.endswith("_skybox0"):
            # Use top_mask.png for skybox0
            source_mask = MASK_DIR / "top_mask.png"
            mask_name = f"{image_name}_mask.png"
        else:
            # Use other_mask.png for other skybox numbers
            source_mask = MASK_DIR / "other_mask.png"
            mask_name = f"{image_name}_mask.png"
            
        
        # Check if source mask exists
        if not source_mask.exists():
            print(f"Warning: Source mask not found: {source_mask}")
            continue
        
        # Create destination path
        dest_mask = OUT_DIR / mask_name
        
        # Copy the mask file
        try:
            shutil.copy2(source_mask, dest_mask)
            print(f"Created: {mask_name}")
        except Exception as e:
            print(f"Error copying {source_mask} to {dest_mask}: {e}")

if __name__ == "__main__":
    create_matterport_masks()

