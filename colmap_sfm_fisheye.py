#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys


# ===== User-configurable parameters =====
# Defaults are derived from config.py; override via env vars if needed.
from config import DATASET_NAME, DATASET_PATH  # noqa: E402

# Source images directory for this dataset
IMAGE_DIR_DEFAULT: Path = (DATASET_PATH / "_source" / "colmap_images" / "front")

# Output run directory for COLMAP artifacts
RUN_DIR_DEFAULT: Path = (DATASET_PATH / "colmap_runs" / "front")
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
    ], check=True)

    # Export model to text and PLY
    print("[INFO] Exporting model to text and PLY...")
    model_dir = sparse_dir / "0"
    if model_dir.is_dir():
        (sparse_dir / "text").mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "colmap", "model_converter",
            "--input_path", str(model_dir),
            "--output_path", str(sparse_dir / "text"),
            "--output_type", "TXT",
        ], check=True)

        subprocess.run([
            "colmap", "model_converter",
            "--input_path", str(model_dir),
            "--output_path", str(sparse_dir / "points3D.ply"),
            "--output_type", "PLY",
        ], check=True)
    else:
        print(f"[WARN] No model directory at {model_dir}. Mapper may have failed or produced a different index.")

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


