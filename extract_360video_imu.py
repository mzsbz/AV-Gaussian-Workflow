#!/usr/bin/env python3
"""
Enhanced 360 Video Frame Extraction with IMU Data Analysis

This script extends the original extract_360video.py to support IMU data extraction
for analysis while using time-based frame extraction.
"""

import argparse
import json
import subprocess
import sys
import shutil
import re
from pathlib import Path
from tqdm import tqdm
import math
from typing import List, Optional

from config import DATASET_PATH
from imu_extractor import IMUExtractor

def _resolve_default_input() -> Path:
    VIDEO_DIR = DATASET_PATH / "_source" / "original"
    # Pick the first .mp4 file in the directory as the default input
    # Prefer .mp4 files for frame extraction, .insv files for IMU data
    mp4_files = sorted(VIDEO_DIR.glob("*.mp4"))
    if mp4_files:
        return mp4_files[0]
    
    # Fallback to .insv files if no .mp4 files found
    insv_files = sorted(VIDEO_DIR.glob("*.insv")) + sorted(VIDEO_DIR.glob("*.INSV"))
    if insv_files:
        return insv_files[0]
    
    print(f"Error: video not found. No .mp4 or .insv file in: {VIDEO_DIR}", file=sys.stderr)
    sys.exit(1)

VIDEO_DIR: Path = DATASET_PATH / "_source" / "original"
EXTRACTED_DIR: Path = DATASET_PATH / "_source" / "extracted_imu"
SYMLINK_DIR: Path = DATASET_PATH / "_source" / "colmap_images_imu"

DEFAULT_INPUT = _resolve_default_input()

def label_for_track(track_index: int) -> str:
    if track_index == 0:
        return "front"
    if track_index == 1:
        return "back"
    return f"track{track_index}"

def run_command(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def ensure_tools_exist() -> None:
    for tool in ("ffprobe", "ffmpeg", "exiftool"):
        if not shutil.which(tool):
            print(f"Error: {tool} not found. Please install required tools.", file=sys.stderr)
            sys.exit(1)

def create_or_update_symlink(link_path: Path, target_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        current_target = link_path.readlink()
        if current_target != target_path:
            link_path.unlink()
            link_path.symlink_to(target_path)
        return
    if link_path.exists():
        print(f"Warning: {link_path} exists and is not a symlink; skipping symlink creation", file=sys.stderr)
        return
    link_path.symlink_to(target_path)

def probe_video_stream_indices(input_path: Path) -> list[int]:
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v",
        "-show_entries", "stream=index",
        "-of", "json",
        str(input_path),
    ]
    result = run_command(cmd)
    data = json.loads(result.stdout or "{}")
    streams = data.get("streams", [])
    return [int(s["index"]) for s in streams]

def probe_duration_seconds(input_path: Path) -> float:
    # Use container duration; for separate tracks in the same file this is fine
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(input_path),
    ]
    result = run_command(cmd)
    try:
        return float((result.stdout or "0").strip())
    except ValueError:
        return 0.0

def create_both_folder_with_symlinks(extracted_dir: Path) -> None:
    """Create a 'both' folder containing symlinks to all images from 'front' and 'back' folders."""
    both_dir = extracted_dir / "both"
    both_dir.mkdir(exist_ok=True)
    
    # Create symlinks from front and back folders
    for track in ["front", "back"]:
        track_dir = extracted_dir / track
        if track_dir.exists():
            for image_file in track_dir.glob("*.jpg"):
                symlink_name = both_dir / image_file.name
                if not symlink_name.exists():
                    symlink_name.symlink_to(image_file)

def extract_frames_for_track_time_based(input_path: Path, track_index: int, output_dir: Path, every_seconds: float) -> None:
    """Time-based frame extraction."""
    output_dir.mkdir(parents=True, exist_ok=True)
    label = label_for_track(track_index)
    output_pattern = str(output_dir / f"frame_%06d_{label}.jpg")
    cmd = [
        "ffmpeg", "-hide_banner", "-y", "-stats", "-loglevel", "info",
        "-i", str(input_path),
        "-map", f"0:v:{track_index}",
        "-vf", f"fps=1/{every_seconds}",
        "-q:v", "2",
        output_pattern,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Estimate total frames given 1 frame every `every_seconds`
    duration_s = probe_duration_seconds(input_path)
    total_frames = int(math.ceil(duration_s / every_seconds)) if duration_s > 0 else None
    progress_bar = tqdm(total=total_frames, unit="frame", desc=label_for_track(track_index), dynamic_ncols=True)
    frame_regex = re.compile(r"frame=\s*(\d+)")
    last_count = 0
    try:
        assert process.stderr is not None
        for line in process.stderr:
            match = frame_regex.search(line)
            if match:
                current = int(match.group(1))
                delta = max(0, current - last_count)
                if delta:
                    progress_bar.update(delta)
                    last_count = current
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
    finally:
        progress_bar.close()

def find_insv_file_for_mp4(mp4_path: Path) -> Optional[Path]:
    """Find the corresponding .insv file for a given .mp4 file."""
    if mp4_path.suffix.lower() == '.mp4':
        insv_path = mp4_path.with_suffix('.insv')
        if insv_path.exists():
            return insv_path
        # Also check for .INSV (uppercase)
        insv_path_upper = mp4_path.with_suffix('.INSV')
        if insv_path_upper.exists():
            return insv_path_upper
    return None

def extract_imu_data_for_analysis(input_path: Path) -> bool:
    """Extract IMU data for analysis purposes (not for frame extraction)."""
    # Try to find corresponding .insv file for IMU data
    insv_path = find_insv_file_for_mp4(input_path)
    
    if insv_path:
        print(f"Found corresponding .insv file: {insv_path}")
        print(f"Extracting IMU data from {insv_path} for analysis...")
        extractor = IMUExtractor(insv_path)
    else:
        print(f"Extracting IMU data from {input_path} for analysis...")
        extractor = IMUExtractor(input_path)
    
    if not extractor.extract_imu_metadata():
        print("Warning: Could not extract IMU data from video. IMU analysis not available.")
        return False
    
    print(f"Found {len(extractor.imu_data)} IMU readings")
    
    # Save IMU data for analysis
    imu_dir = DATASET_PATH / "_source" / "imu_data"
    imu_dir.mkdir(parents=True, exist_ok=True)
    
    extractor.save_imu_data_csv(imu_dir / "imu_readings.csv")
    
    # Save heading data for direction analysis
    extractor.save_heading_data_csv(imu_dir / "heading_data.csv")
    
    # Get and display direction summary
    direction_summary = extractor.get_direction_summary()
    if direction_summary:
        print("\n=== IMU Direction Analysis ===")
        print(f"Total rotation: {direction_summary['total_rotation_degrees']:.1f}°")
        print(f"Direction changes: {direction_summary['direction_changes_count']}")
        print(f"Average rotation rate: {direction_summary['average_rotation_rate_deg_per_sec']:.2f}°/s")
        print(f"Initial heading: {direction_summary['initial_heading_degrees']:.1f}°")
        print(f"Final heading: {direction_summary['final_heading_degrees']:.1f}°")
    
    print(f"IMU analysis data saved to {imu_dir}")
    return True

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract frames for each video track using time-based sampling with optional IMU data analysis"
    )
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT, help="Path to input video")
    
    # Extraction parameters
    parser.add_argument("--every-seconds", dest="every_seconds", type=float, default=5.0,
                       help="Extract one frame every N seconds (default: 5.0)")
    parser.add_argument("--extract-imu", action="store_true", default=True,
                       help="Extract IMU data for analysis (default: True)")
    
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    ensure_tools_exist()

    # Extract IMU data for analysis if requested
    if args.extract_imu:
        print("Extracting IMU data for analysis...")
        extract_imu_data_for_analysis(input_path)
    else:
        print("Skipping IMU data extraction")

    # Ensure output DIR exists and symlink is set to it
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    create_or_update_symlink(SYMLINK_DIR, EXTRACTED_DIR)

    track_indices = probe_video_stream_indices(input_path)
    if not track_indices:
        print(f"No video streams found in: {input_path}", file=sys.stderr)
        return 1

    print(f"Found {len(track_indices)} video stream(s).")
    print(f"Using time-based extraction: 1 frame every {args.every_seconds}s")
    
    # Extract frames for each track
    for idx in track_indices:
        label = label_for_track(idx)
        frames_dir = EXTRACTED_DIR / label
        print(f"  -> Extracting 1 frame every {args.every_seconds}s to {frames_dir}")
        extract_frames_for_track_time_based(input_path, idx, frames_dir, args.every_seconds)

    # Create the 'both' folder with symlinks
    create_both_folder_with_symlinks(EXTRACTED_DIR)
    
    # Create symlink from SYMLINK_DIR to the 'both' folder
    both_symlink_path = SYMLINK_DIR / "both"
    create_or_update_symlink(both_symlink_path, EXTRACTED_DIR / "both")

    print(f"Done. Output files are in: {EXTRACTED_DIR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
