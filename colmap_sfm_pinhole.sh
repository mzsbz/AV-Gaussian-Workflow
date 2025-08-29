#!/usr/bin/env bash

set -euo pipefail

# COLMAP SfM pipeline with PINHOLE camera model.
#
# Usage:
#   ./colmap_sfm_fisheye.sh [IMAGE_DIR] [RUN_DIR]
#
# Defaults:
#   IMAGE_DIR: /home/pc-04/Research/_datasets/YJP-Lvl04_250826/_source/track0_frames
#   RUN_DIR:   /home/pc-04/Research/gaussian-splats/AV-Gaussian-Workflow/colmap_runs/track0
#
# The script will:
#   - Create the run workspace (database/, images/, sparse/, dense/)
#   - Copy or sync images into RUN_DIR/images
#   - Extract features with OPENCV_FISHEYE and single shared camera
#   - Perform exhaustive matching
#   - Run the mapper to produce a sparse reconstruction
#   - Export the model to text format under sparse/text
#   - Export sparse point cloud as PLY at sparse/points3D.ply

DATASET_NAME="YJP-Lvl04_250828_DSLR"
DATA_VARIANT="oddset_quarterres"
IMAGE_DIR_DEFAULT="/home/pc-04/Research/_datasets/${DATASET_NAME}/_source/colmap_images/${DATA_VARIANT}"
RUN_DIR_DEFAULT="/home/pc-04/Research/_datasets/${DATASET_NAME}/colmap_runs/${DATA_VARIANT}"

IMAGE_DIR="${1:-$IMAGE_DIR_DEFAULT}"
RUN_DIR="${2:-$RUN_DIR_DEFAULT}"

echo "[INFO] IMAGE_DIR: $IMAGE_DIR"
echo "[INFO] RUN_DIR:   $RUN_DIR"

# GPU configuration
GPU_INDEX="${GPU_INDEX:-0}"
USE_GPU=1
if ! nvidia-smi -L >/dev/null 2>&1; then
  echo "[WARN] nvidia-smi not available or no GPU detected; falling back to CPU"
  USE_GPU=0
fi
echo "[INFO] USE_GPU=$USE_GPU GPU_INDEX=$GPU_INDEX CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-<unset>}"

if ! command -v colmap >/dev/null 2>&1; then
  echo "[ERROR] COLMAP not found in PATH. Please install or load it first." >&2
  exit 1
fi

mkdir -p "$RUN_DIR/database" "$RUN_DIR/images" "$RUN_DIR/sparse" "$RUN_DIR/dense"

echo "[INFO] Syncing images to run directory..."
rsync -a "$IMAGE_DIR"/ "$RUN_DIR/images"/

DB_PATH="$RUN_DIR/database/database.db"
IMG_PATH="$RUN_DIR/images"
SPARSE_DIR="$RUN_DIR/sparse"

echo "[INFO] Running feature extraction (PINHOLE)..."
colmap feature_extractor \
  --database_path "$DB_PATH" \
  --image_path "$IMG_PATH" \
  --ImageReader.camera_model PINHOLE \
  --ImageReader.single_camera 1 \
  --SiftExtraction.use_gpu $USE_GPU \
  --SiftExtraction.gpu_index $GPU_INDEX \
  --SiftExtraction.estimate_affine_shape 1 \
  --SiftExtraction.domain_size_pooling 1 | cat

echo "[INFO] Running exhaustive matching..."
colmap exhaustive_matcher \
  --database_path "$DB_PATH" \
  --SiftMatching.use_gpu $USE_GPU \
  --SiftMatching.gpu_index $GPU_INDEX | cat

echo "[INFO] Running mapper (sparse reconstruction)..."
mkdir -p "$SPARSE_DIR/0"
colmap mapper \
  --database_path "$DB_PATH" \
  --image_path "$IMG_PATH" \
  --output_path "$SPARSE_DIR" | cat

echo "[INFO] Exporting model to text and PLY..."
MODEL_DIR="$SPARSE_DIR/0"
if [ -d "$MODEL_DIR" ]; then
  mkdir -p "$SPARSE_DIR/text"
  colmap model_converter \
    --input_path "$MODEL_DIR" \
    --output_path "$SPARSE_DIR/text" \
    --output_type TXT | cat

  # Export sparse points to PLY
  colmap model_converter \
    --input_path "$MODEL_DIR" \
    --output_path "$SPARSE_DIR/points3D.ply" \
    --output_type PLY | cat
else
  echo "[WARN] No model directory at $MODEL_DIR. Mapper may have failed or produced a different index."
fi

echo "[INFO] Done. Run directory: $RUN_DIR"


