# IMU Data Extraction for Insta360 Videos

This guide explains how to use the IMU (Inertial Measurement Unit) data extraction functionality to analyze camera movement patterns from Insta360 video files.

## Overview

Insta360 cameras embed IMU data (accelerometer and gyroscope readings) into their video files. This data can be extracted and analyzed to understand camera movement patterns, rotation, and orientation changes over time.

## Benefits of IMU Data Analysis

- **Movement analysis**: Understand camera motion patterns and rotation
- **Research purposes**: Analyze camera behavior for academic or development work
- **Quality assessment**: Identify periods of stability vs. movement
- **Metadata preservation**: Keep sensor data for future analysis

## Quick Start

### 1. Basic IMU Data Extraction
```bash
# Extract IMU data and analyze movement patterns
uv run python extract_360video_imu.py /path/to/video.mp4

# Extract IMU data with custom time interval for frames
uv run python extract_360video_imu.py /path/to/video.mp4 --every-seconds 3.0
```

### 2. IMU Data Only (No Frame Extraction)
```bash
# Extract only IMU data for analysis
uv run python imu_extractor.py /path/to/video.mp4 --output-dir ./imu_analysis
```

### 3. Traditional Time-Based Frame Extraction
```bash
# Extract 1 frame every 5 seconds (traditional method)
uv run python extract_360video_imu.py /path/to/video.mp4 --every-seconds 5.0
```

## Installation Requirements

The system requires the following dependencies:

```bash
# Install exiftool for metadata extraction
sudo apt install libimage-exiftool-perl

# Install Python dependencies
uv add numpy
```

## File Format Support

- **Insta360 .insv files**: Native format with embedded IMU data (used for IMU extraction)
- **Standard .mp4 files**: Processed video files (used for frame extraction)
- **Automatic pairing**: System automatically finds corresponding .insv files for .mp4 files with the same stem
- **Fallback support**: Can extract IMU data from .mp4 files if no .insv file is found

## How It Works

### 1. IMU Data Extraction
The system uses `exiftool` to extract embedded sensor data from video files:

```bash
exiftool -ee3 -api largefilesupport=1 -j video.mp4
```

### 2. Data Processing
1. **Parse IMU readings**: Extract accelerometer (m/s²) and gyroscope (rad/s) data
2. **Gravity compensation**: Remove estimated gravity vector from accelerometer readings
3. **Heading calculation**: Integrate gyroscope data to track camera rotation
4. **Movement analysis**: Analyze acceleration patterns and direction changes

### 3. Frame Extraction
Extract frames at regular time intervals using ffmpeg:

```bash
ffmpeg -i video.mp4 -vf "fps=1/5" -q:v 2 frame_%06d.jpg
```

## Output Files

When using IMU data extraction, analysis files are created:

```
_source/
├── imu_data/
│   ├── imu_readings.csv           # Raw IMU sensor data
│   └── heading_data.csv           # Calculated heading changes
├── extracted/
│   ├── front/                     # Front camera frames
│   ├── back/                      # Back camera frames
│   └── both/                      # Symlinks to all frames
└── colmap_images -> extracted/    # Symlink for COLMAP
```

## Analysis Files

### imu_readings.csv
Raw IMU sensor data extracted from the video:
```csv
timestamp,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z
0.000,-0.123,0.456,9.789,0.001,-0.002,0.003
0.010,-0.125,0.454,9.791,0.002,-0.001,0.004
...
```

### heading_data.csv
Calculated heading changes over time:
```csv
timestamp,heading_degrees
0.000,0.0
0.010,0.5
1.000,15.2
...
```

## Configuration Options

### Time Intervals for Frame Extraction
- **5.0 seconds**: Good for general analysis
- **3.0 seconds**: Higher density sampling
- **10.0 seconds**: Lower density for long videos
- **1.0 seconds**: Very high density for detailed analysis

### IMU Analysis Parameters
You can modify the IMU processing parameters in `imu_extractor.py`:

```python
# Enable/disable gravity compensation
gravity_filter = True

# Sampling rate detection
auto_detect_sampling_rate = True
```

## Troubleshooting

### Limited IMU Data Coverage (Most Common Issue)
**Symptom**: Warning message "IMU data only covers X% of the video!"

**Cause**: ExifTool has a hardcoded 20,000 record limit for Insta360 files to prevent memory issues.

**Solutions**:
1. **Accept partial coverage**: For videos with consistent movement, the extracted portion may be representative
2. **Use specialized tools**: Consider Insta360's official SDK or tools like `insta360-auto-converter`
3. **Segment extraction**: Split long videos into shorter segments for processing
4. **Focus on analysis**: Use available IMU data for movement pattern analysis

### No IMU Data Found
If the system reports "Could not extract IMU data":

1. **Check file format**: Ensure you're using native Insta360 files (.insv)
2. **Camera settings**: Some export settings may strip IMU data
3. **Manual inspection**: Use `exiftool -ee3 -j video.mp4` to check for embedded data
4. **Continue with frames**: System will still extract frames using time-based sampling

### Performance Considerations
- IMU processing adds ~10-30 seconds to extraction time
- Large video files may require more memory for metadata processing
- IMU analysis is CPU-intensive for long videos

## Integration with Existing Workflow

The IMU-enhanced extraction is designed to be a drop-in replacement:

```bash
# Old workflow
python extract_360video.py --every-seconds 5.0

# New workflow - same output structure with IMU analysis
python extract_360video_imu.py --every-seconds 5.0
```

All existing scripts (`colmap_sfm_fisheye.py`, etc.) work unchanged with the new frame extraction method.

## Testing Your Setup

Run the test script to verify everything is working:

```bash
uv run python test_imu_extraction.py
```

This will check all dependencies and show usage examples.

## Example Workflow

Complete workflow for IMU-enhanced frame extraction:

```bash
# 1. Place both .insv and .mp4 files in source directory
cp my_video.insv _source/original/
cp my_video.mp4 _source/original/

# 2. Extract frames using time-based sampling with IMU analysis
uv run python extract_360video_imu.py my_video.mp4 --every-seconds 5.0
# (IMU data will be automatically extracted from my_video.insv)

# 3. Run COLMAP SfM as usual
uv run python colmap_sfm_fisheye.py

# 4. Analyze IMU data (optional)
ls _source/imu_data/
```

**Note**: The system automatically pairs .mp4 and .insv files with the same stem. If you only have .insv files, the system will use them for both IMU extraction and frame extraction.

## Technical Details

### IMU Data Structure
The system looks for these metadata fields:
- `AccelerometerData` / `GyroscopeData`
- `SensorData` / `IMUData` 
- `CameraMotionMetadata`
- Any field containing 'accel', 'gyro', or 'imu'

### Movement Analysis Algorithm
1. **Preprocessing**: Remove gravity bias using initial readings
2. **Heading integration**: Integrate gyroscope Z-axis for yaw changes
3. **Pattern analysis**: Analyze acceleration and rotation patterns
4. **Direction summary**: Calculate total rotation and direction changes

### Limitations
- **Data coverage**: May be limited by ExifTool record limits
- **Accuracy**: Sensor data quality depends on camera model and settings
- **Calibration**: May need adjustment for different camera models

## Future Improvements

Potential enhancements:
- GPS integration for absolute positioning
- Machine learning-based movement classification
- Orientation-aware analysis
- Multi-sensor fusion (IMU + optical flow)
- Real-time processing capabilities
