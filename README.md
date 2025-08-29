## AV-Gaussian-Workflow Utilities

### split_video_tracks.sh
Extract frames at 1 fps for each video stream (track) in a container. No split video files are produced.

#### Requirements
- ffmpeg (includes `ffmpeg` and `ffprobe`)

#### Script
- Location: `split_video_tracks.sh`
- Default input: `/home/pc-04/Research/_datasets/YJP-Lvl04_250826/_source/VID_20250826_162604_00_014.mp4`

#### Usage
Run with default input:
```bash
/home/pc-04/Research/gaussian-splats/AV-Gaussian-Workflow/split_video_tracks.sh
```

Run with a custom input file:
```bash
/home/pc-04/Research/gaussian-splats/AV-Gaussian-Workflow/split_video_tracks.sh /path/to/input.mp4
```

#### Behavior
- Detects all video streams using `ffprobe`
- For each video stream index `N`:
  - Extracts 1 fps JPEG frames to: `.../trackN_frames/frame_%06d_trackN.jpg`
    - Example: `track0_frames/frame_000001_track0.jpg`

#### Examples of outputs
- Frames: `track0_frames/frame_000001_track0.jpg`, `track1_frames/frame_000001_track1.jpg`

#### Notes
- If the container has no video streams, the script exits with an error.
- Overwrites existing outputs of the same name.

### extract_frames.py
Python version that mirrors the shell script behavior using `ffprobe`/`ffmpeg`.

#### Requirements
- Python 3.8+
- ffmpeg (includes `ffmpeg` and `ffprobe`)

#### Usage
Run with default input:
```bash
python3 /home/pc-04/Research/gaussian-splats/AV-Gaussian-Workflow/extract_frames.py
```

Run with a custom input file:
```bash
python3 /home/pc-04/Research/gaussian-splats/AV-Gaussian-Workflow/extract_frames.py /path/to/input.mp4
```

#### Behavior
- Same outputs as the shell script: `trackN_frames/frame_%06d_trackN.jpg`

