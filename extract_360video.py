#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import shutil
import re
from pathlib import Path
from tqdm import tqdm
import math

from config import DATASET_PATH


def _resolve_default_input() -> Path:
    VIDEO_DIR = DATASET_PATH / "_source" / "original"
    # Pick the first .mp4 file in the directory as the default input
    mp4_files = sorted(VIDEO_DIR.glob("*.mp4"))
    if not mp4_files:
        print(f"Error: video not found. No .mp4 file in: {VIDEO_DIR}", file=sys.stderr)
        sys.exit(1)
    return mp4_files[0]


VIDEO_DIR: Path = DATASET_PATH / "_source" / "original"
EXTRACTED_DIR: Path = DATASET_PATH / "_source" / "extracted"
SYMLINK_DIR: Path = DATASET_PATH / "_source" / "colmap_images"

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
    for tool in ("ffprobe", "ffmpeg"):
        if not shutil.which(tool):
            print(f"Error: {tool} not found. Please install ffmpeg suite.", file=sys.stderr)
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
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(input_path),
    ]
    result = run_command(cmd)
    try:
        return float((result.stdout or "0").strip())
    except ValueError:
        return 0.0


def extract_frames_for_track(input_path: Path, track_index: int, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    label = label_for_track(track_index)
    output_pattern = str(output_dir / f"frame_%06d_{label}.jpg")
    cmd = [
        "ffmpeg", "-hide_banner", "-y", "-stats", "-loglevel", "info",
        "-i", str(input_path),
        "-map", f"0:v:{track_index}",
        "-vf", "fps=1",
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

    # Estimate total frames at 1 fps using duration (seconds)
    duration_s = probe_duration_seconds(input_path)
    total_frames = int(math.ceil(duration_s)) if duration_s > 0 else None
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract 1 fps frames for each video track using ffmpeg")
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT, help="Path to input video")
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    ensure_tools_exist()

    # Ensure output DIR exists and symlink is set to it
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    create_or_update_symlink(SYMLINK_DIR, EXTRACTED_DIR)

    track_indices = probe_video_stream_indices(input_path)
    if not track_indices:
        print(f"No video streams found in: {input_path}", file=sys.stderr)
        return 1

    print(f"Found {len(track_indices)} video stream(s). Extracting frames...")
    for idx in track_indices:
        label = label_for_track(idx)
        frames_dir = EXTRACTED_DIR / label
        print(f"  -> Extracting 1 fps frames to {frames_dir}")
        extract_frames_for_track(input_path, idx, frames_dir)

    print(f"Done. Output files are in: {EXTRACTED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


