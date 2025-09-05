#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys

import config

# ===== User-configurable parameters =====
# Change these to adjust the SfM run without editing the commands below.
IMAGE_DIR_DEFAULT: Path = config.DATASET_PATH / "_source" / "colmap_images" / config.DATA_VARIANT
RUN_DIR_DEFAULT: Path = config.DATASET_PATH / "colmap_runs" / config.DATA_VARIANT
# =======================================


def ensure_colmap_available() -> None:
    if shutil.which("colmap") is None:
        print("[ERROR] COLMAP not found in PATH. Please install or load it first.", file=sys.stderr)
        sys.exit(1)


def detect_gpu() -> tuple[int, str]:
    gpu_index: str = os.environ.get("GPU_INDEX", "0")
    try:
        result = subprocess.run(["nvidia-smi", "-L"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        use_gpu: int = 1 if result.returncode == 0 else 0
        if use_gpu == 0:
            print("[WARN] nvidia-smi not available or no GPU detected; falling back to CPU")
    except FileNotFoundError:
        print("[WARN] nvidia-smi not available or no GPU detected; falling back to CPU")
        use_gpu = 0
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    print(f"[INFO] USE_GPU={use_gpu} GPU_INDEX={gpu_index} CUDA_VISIBLE_DEVICES={visible}")
    return use_gpu, gpu_index


def rsync_copy(src_dir: Path, dst_dir: Path) -> None:
    print("[INFO] Syncing images to run directory...")
    if shutil.which("rsync") is not None:
        subprocess.run(["rsync", "-a", f"{src_dir}/", f"{dst_dir}/"], check=True)
    else:
        # Fallback: shutil.copytree(copy) with dirs_exist_ok
        for item in src_dir.rglob("*"):
            rel = item.relative_to(src_dir)
            target = dst_dir / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)


def create_or_update_symlink(src_dir: Path, dst_link: Path) -> None:
    """Create a symlink at dst_link pointing to src_dir, replacing any existing path.

    Ensures parent directories exist. If dst_link exists as a directory or file,
    it will be removed before creating the symlink.
    """
    print(f"[INFO] Linking images: {dst_link} -> {src_dir}")
    dst_link.parent.mkdir(parents=True, exist_ok=True)

    if dst_link.exists() or dst_link.is_symlink():
        if dst_link.is_symlink() or dst_link.is_file():
            dst_link.unlink()
        else:
            shutil.rmtree(dst_link)

    dst_link.symlink_to(src_dir, target_is_directory=True)


def find_largest_model(sparse_dir: Path) -> Path | None:
    """Find the model with the largest folder size by comparing directory sizes.
    
    Returns the path to the largest model directory, or None if no models found.
    """
    if not sparse_dir.exists():
        return None
    
    model_dirs = [d for d in sparse_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    if not model_dirs:
        return None
    
    if len(model_dirs) == 1:
        return model_dirs[0]
    
    print(f"[INFO] Found {len(model_dirs)} models, comparing folder sizes...")
    
    largest_model = None
    max_size = 0
    
    for model_dir in model_dirs:
        try:
            # Calculate total size of directory
            total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            print(f"[INFO] Model {model_dir.name}: {size_mb:.1f} MB")
            
            if total_size > max_size:
                max_size = total_size
                largest_model = model_dir
        except OSError as e:
            print(f"[WARN] Failed to analyze model {model_dir.name}: {e}")
            continue
    
    if largest_model:
        size_mb = max_size / (1024 * 1024)
        print(f"[INFO] Selected largest model: {largest_model.name} ({size_mb:.1f} MB)")
    else:
        print("[WARN] Could not determine largest model")
    
    return largest_model


def main() -> None:
    # Resolve parameters from env or defaults
    image_dir = Path(os.environ.get("IMAGE_DIR", str(IMAGE_DIR_DEFAULT))).expanduser()
    run_dir = Path(os.environ.get("RUN_DIR", str(RUN_DIR_DEFAULT))).expanduser()

    print(f"[INFO] IMAGE_DIR: {image_dir}")
    print(f"[INFO] RUN_DIR:   {run_dir}")

    ensure_colmap_available()
    use_gpu, gpu_index = detect_gpu()

    # Prepare workspace
    (run_dir / "database").mkdir(parents=True, exist_ok=True)
    (run_dir / "sparse").mkdir(parents=True, exist_ok=True)
    (run_dir / "dense").mkdir(parents=True, exist_ok=True)

    # Link images directory instead of copying
    create_or_update_symlink(image_dir, run_dir / "images")

    db_path = run_dir / "database" / "database.db"
    img_path = run_dir / "images"
    sparse_dir = run_dir / "sparse"

    # Feature extraction (OPENCV_FISHEYE)
    print("[INFO] Running feature extraction (OPENCV_FISHEYE)...")
    subprocess.run([
        "colmap", "feature_extractor",
        "--database_path", str(db_path),
        "--image_path", str(img_path),
        "--ImageReader.camera_model", "OPENCV_FISHEYE",
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.use_gpu", str(use_gpu),
        "--SiftExtraction.gpu_index", str(gpu_index),
        "--SiftExtraction.estimate_affine_shape", "1",
        "--SiftExtraction.domain_size_pooling", "1",
    ], check=True)

    # Exhaustive matching
    print("[INFO] Running exhaustive matching...")
    subprocess.run([
        "colmap", "exhaustive_matcher",
        "--database_path", str(db_path),
        "--SiftMatching.use_gpu", str(use_gpu),
        "--SiftMatching.gpu_index", str(gpu_index),
    ], check=True)

    # Mapper (sparse reconstruction)
    print("[INFO] Running mapper (sparse reconstruction)...")
    (sparse_dir / "0").mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "colmap", "mapper",
        "--database_path", str(db_path),
        "--image_path", str(img_path),
        "--output_path", str(sparse_dir),
        "--Mapper.min_model_size", "10",  # Minimum 10 registered images
    ], check=True)

    # Find the largest model and clean up others
    print("[INFO] Analyzing models to find largest...")
    largest_model = find_largest_model(sparse_dir)
    
    if largest_model:
        # If the largest model is not in sparse/0, move it there
        if largest_model.name != "0":
            print(f"[INFO] Moving largest model from {largest_model.name} to 0...")
            target_dir = sparse_dir / "0"
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(largest_model), str(target_dir))
        
        # Remove all other model directories
        for model_dir in sparse_dir.iterdir():
            if model_dir.is_dir() and model_dir.name.isdigit() and model_dir.name != "0":
                print(f"[INFO] Removing smaller model {model_dir.name}...")
                shutil.rmtree(model_dir)
        
        print("[INFO] Kept only the largest model in sparse/0")
    else:
        print("[WARN] No valid model found")

    print(f"[INFO] Done. Run directory: {run_dir}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Subprocess failed with return code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user", file=sys.stderr)
        sys.exit(130)


