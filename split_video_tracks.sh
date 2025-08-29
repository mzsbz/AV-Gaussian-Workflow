#!/usr/bin/env bash

set -euo pipefail

# Split each video stream (track) from a container into separate files without re-encoding.
# Usage:
#   ./split_video_tracks.sh [input_video]
# If no argument is provided, defaults to the provided path.

DEFAULT_INPUT="/home/pc-04/Research/_datasets/YJP-Lvl04_250826/_source/VID_20250826_162604_00_014.mp4"
INPUT_PATH="${1:-$DEFAULT_INPUT}"

if [[ ! -f "$INPUT_PATH" ]]; then
  echo "Error: input file not found: $INPUT_PATH" >&2
  exit 1
fi

# Check for ffprobe/ffmpeg
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "Error: ffprobe not found. Please install ffmpeg suite." >&2
  exit 1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg not found. Please install ffmpeg suite." >&2
  exit 1
fi

# Derive paths and names
INPUT_DIR="$(dirname -- "$INPUT_PATH")"
INPUT_FILE="$(basename -- "$INPUT_PATH")"
BASE_NAME="${INPUT_FILE%.*}"
EXT="${INPUT_FILE##*.}"
[[ "$EXT" == "$INPUT_FILE" ]] && EXT="mp4"  # fallback if no extension

# Gather video stream indices
mapfile -t VIDEO_INDICES < <(ffprobe -v error -select_streams v -show_entries stream=index -of csv=p=0 "$INPUT_PATH")

NUM_VID_STREAMS="${#VIDEO_INDICES[@]}"
if [[ "$NUM_VID_STREAMS" -eq 0 ]]; then
  echo "No video streams found in: $INPUT_PATH" >&2
  exit 1
fi

echo "Found $NUM_VID_STREAMS video stream(s). Extracting frames..."

for IDX in "${VIDEO_INDICES[@]}"; do
  # Extract frames at 1 fps for this track
  FRAMES_DIR="$INPUT_DIR/track${IDX}_frames"
  mkdir -p "$FRAMES_DIR"
  echo "  -> Extracting 1 fps frames to $FRAMES_DIR"
  ffmpeg -hide_banner -loglevel error -y -i "$INPUT_PATH" -map 0:v:"$IDX" -vf fps=1 -q:v 2 "$FRAMES_DIR/frame_%06d_track${IDX}.jpg"
done

echo "Done. Output files are alongside the input in: $INPUT_DIR"


