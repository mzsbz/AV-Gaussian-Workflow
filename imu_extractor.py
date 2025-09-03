#!/usr/bin/env python3
"""
IMU Data Extractor for Insta360 Videos

This module extracts IMU (accelerometer/gyroscope) data from Insta360 video files
for analysis and research purposes.
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import numpy as np
from datetime import datetime, timedelta
import csv

@dataclass
class IMUReading:
    """Represents a single IMU reading with timestamp."""
    timestamp: float  # seconds
    accel_x: float   # m/s²
    accel_y: float   # m/s²
    accel_z: float   # m/s²
    gyro_x: float    # rad/s
    gyro_y: float    # rad/s
    gyro_z: float    # rad/s

class IMUExtractor:
    """Extracts and processes IMU data from Insta360 videos."""
    
    def __init__(self, video_path: Path):
        self.video_path = video_path
        self.imu_data: List[IMUReading] = []
        
    def extract_imu_metadata(self) -> bool:
        """
        Extract IMU metadata from video file using exiftool.
        Returns True if successful, False otherwise.
        """
        try:
            # For .insv files, try multiple extraction methods to get complete data
            if self.video_path.suffix.lower() in ['.insv']:
                print("Detected .insv file - attempting comprehensive IMU extraction...")
                return self._extract_insta360_comprehensive()
            
            # Standard extraction for other formats
            return self._extract_standard_metadata()
            
        except subprocess.CalledProcessError as e:
            print(f"Error running exiftool: {e}")
            print(f"stderr: {e.stderr}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing exiftool JSON output: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error extracting IMU data: {e}")
            return False
    
    def _extract_standard_metadata(self) -> bool:
        """Extract metadata using standard exiftool approach."""
        cmd = [
            "exiftool",
            "-ee3",  # Extract embedded data up to 3 levels deep
            "-api", "largefilesupport=1",
            "-api", "RequestAll=3",
            "-api", "MaxDataLen=0",  # Remove data length limit
            "-a",    # Allow duplicate tags
            "-u",    # Extract unknown tags
            "-g3",   # Group output by tag group
            "-j",    # JSON output
            str(self.video_path)
        ]
        
        print(f"Running exiftool on {self.video_path}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        if not metadata:
            print(f"Warning: No metadata found in {self.video_path}")
            return False
        
        # Parse IMU data from metadata
        self._parse_imu_from_metadata(metadata[0] if isinstance(metadata, list) else metadata)
        return len(self.imu_data) > 0
    
    def _extract_insta360_comprehensive(self) -> bool:
        """Extract IMU data comprehensively from Insta360 .insv files."""
        print("Using comprehensive Insta360 extraction method...")
        
        # Method 1: Try with non-JSON output to get raw accelerometer data
        cmd = [
            "exiftool",
            "-ee",
            "-api", "largefilesupport=1",
            "-api", "RequestAll=3",
            "-a",
            "-u",
            "-g1",
            str(self.video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the raw output for IMU data
        if self._parse_raw_insta360_output(result.stdout):
            print(f"Successfully extracted {len(self.imu_data)} IMU readings from raw output")
            self._check_imu_data_completeness()
            return True
        
        # Fallback to standard method if raw parsing fails
        print("Raw parsing failed, falling back to standard JSON extraction...")
        return self._extract_standard_metadata()
    
    def _parse_raw_insta360_output(self, raw_output: str) -> bool:
        """Parse IMU data from raw exiftool output for Insta360 files."""
        try:
            lines = raw_output.split('\n')
            current_timecode = None
            current_accel = None
            current_gyro = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for Time Code lines
                if line.startswith('Time Code'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        try:
                            current_timecode = float(parts[1].strip()) / 1000.0  # Convert to seconds
                        except ValueError:
                            continue
                
                # Look for Accelerometer lines
                elif line.startswith('Accelerometer'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        accel_str = parts[1].strip()
                        accel_parts = accel_str.split()
                        if len(accel_parts) == 3:
                            try:
                                # Store raw g-force values (we'll convert to m/s² after gravity compensation)
                                current_accel = [float(x) for x in accel_parts]
                            except ValueError:
                                continue
                
                # Look for Angular Velocity lines
                elif line.startswith('Angular Velocity'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        gyro_str = parts[1].strip()
                        gyro_parts = gyro_str.split()
                        if len(gyro_parts) == 3:
                            try:
                                current_gyro = [float(x) for x in gyro_parts]
                            except ValueError:
                                continue
                
                # If we have all three components, create an IMU reading
                if current_timecode is not None and current_accel and current_gyro:
                    reading = IMUReading(
                        timestamp=current_timecode,
                        accel_x=current_accel[0],
                        accel_y=current_accel[1],
                        accel_z=current_accel[2],
                        gyro_x=current_gyro[0],
                        gyro_y=current_gyro[1],
                        gyro_z=current_gyro[2]
                    )
                    self.imu_data.append(reading)
                    
                    # Reset for next reading
                    current_timecode = None
                    current_accel = None
                    current_gyro = None
            
            return len(self.imu_data) > 0
            
        except Exception as e:
            print(f"Error parsing raw Insta360 output: {e}")
            return False
            
    def _check_imu_data_completeness(self) -> None:
        """Check if IMU data covers the full video duration and warn if incomplete."""
        if not self.imu_data:
            return
        
        # Get video duration
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                   "-of", "default=noprint_wrappers=1:nokey=1", str(self.video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_duration = float(result.stdout.strip())
        except:
            print("Warning: Could not determine video duration for completeness check")
            return
        
        # Check IMU data coverage
        imu_start = min(reading.timestamp for reading in self.imu_data)
        imu_end = max(reading.timestamp for reading in self.imu_data)
        imu_duration = imu_end - imu_start
        
        print(f"IMU data coverage: {imu_start:.1f}s to {imu_end:.1f}s ({imu_duration:.1f}s)")
        print(f"Video duration: {video_duration:.1f}s")
        
        coverage_percentage = (imu_duration / video_duration) * 100
        
        if coverage_percentage < 90:  # Less than 90% coverage
            print(f"⚠️  WARNING: IMU data only covers {coverage_percentage:.1f}% of the video!")
            print("   This is likely due to ExifTool's 20,000 record limit for Insta360 files.")
            print("   Consider using specialized Insta360 tools for complete IMU extraction.")
        else:
            print(f"✅ IMU data covers {coverage_percentage:.1f}% of the video")
    
    def _try_enhanced_insv_extraction(self) -> None:
        """Try additional extraction methods specific to .insv files."""
        try:
            # Try extracting embedded data with different exiftool options
            enhanced_cmd = [
                "exiftool",
                "-ee",   # Extract embedded data
                "-api", "largefilesupport=1",
                "-api", "RequestAll=3",
                "-api", "MaxDataLen=0",  # Remove data length limit
                "-a",    # Allow duplicate tags
                "-u",    # Extract unknown tags
                "-j",    # JSON output
                str(self.video_path)
            ]
            
            result = subprocess.run(enhanced_cmd, capture_output=True, text=True, check=True)
            enhanced_metadata = json.loads(result.stdout)
            
            if enhanced_metadata:
                print("Enhanced extraction found additional data")
                # Parse any additional IMU data found
                for item in enhanced_metadata:
                    if isinstance(item, dict):
                        self._parse_imu_from_metadata(item)
                        
        except Exception as e:
            print(f"Enhanced extraction failed: {e}")
            # Continue with normal extraction
    
    def _parse_imu_from_metadata(self, metadata: dict) -> None:
        """Parse IMU readings from exiftool metadata."""
        # Look for various possible IMU data fields
        imu_fields = [
            'AccelerometerData', 'GyroscopeData', 'SensorData',
            'CameraMotionMetadata', 'MotionData', 'IMUData'
        ]
        
        for field in imu_fields:
            if field in metadata:
                self._extract_imu_readings(metadata[field], field)
                break
        
        # Check for Insta360 specific format (Doc* entries with Accelerometer/AngularVelocity)
        for key, value in metadata.items():
            if key.startswith('Doc') and isinstance(value, dict):
                if 'Accelerometer' in value and 'AngularVelocity' in value:
                    self._extract_insta360_imu_reading(value, key)
        
        # Also check embedded data sections
        for key, value in metadata.items():
            if 'accel' in key.lower() or 'gyro' in key.lower() or 'imu' in key.lower():
                if isinstance(value, (list, dict)):
                    self._extract_imu_readings(value, key)
    
    def _extract_insta360_imu_reading(self, data: dict, doc_key: str) -> None:
        """Extract IMU reading from Insta360's Doc* format."""
        try:
            # Parse timestamp (TimeCode is in milliseconds, convert to seconds)
            timecode = data.get('TimeCode', 0)
            timestamp = float(timecode) / 1000.0  # Convert to seconds
            
            # Parse accelerometer data (format: "x y z")
            accel_str = data.get('Accelerometer', '')
            accel_parts = accel_str.split()
            if len(accel_parts) == 3:
                accel_x = float(accel_parts[0])
                accel_y = float(accel_parts[1])
                accel_z = float(accel_parts[2])
            else:
                return
            
            # Parse gyroscope data (format: "x y z")
            gyro_str = data.get('AngularVelocity', '')
            gyro_parts = gyro_str.split()
            if len(gyro_parts) == 3:
                gyro_x = float(gyro_parts[0])
                gyro_y = float(gyro_parts[1])
                gyro_z = float(gyro_parts[2])
            else:
                return
            
            # Create IMU reading
            reading = IMUReading(
                timestamp=timestamp,
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                gyro_x=gyro_x,
                gyro_y=gyro_y,
                gyro_z=gyro_z
            )
            
            self.imu_data.append(reading)
            
        except (ValueError, TypeError) as e:
            print(f"Error parsing Insta360 IMU data from {doc_key}: {e}")
            return
    
    def _extract_imu_readings(self, data, field_name: str) -> None:
        """Extract individual IMU readings from data structure."""
        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    reading = self._parse_single_imu_reading(item, i * 0.01)  # Assume 100Hz
                    if reading:
                        self.imu_data.append(reading)
        elif isinstance(data, dict):
            # Single reading or nested structure
            reading = self._parse_single_imu_reading(data, 0.0)
            if reading:
                self.imu_data.append(reading)
    
    def _parse_single_imu_reading(self, data: dict, timestamp: float) -> Optional[IMUReading]:
        """Parse a single IMU reading from a data dictionary."""
        try:
            # Look for accelerometer data
            accel_x = self._find_value(data, ['AccelX', 'accel_x', 'ax', 'AccelerationX'])
            accel_y = self._find_value(data, ['AccelY', 'accel_y', 'ay', 'AccelerationY'])
            accel_z = self._find_value(data, ['AccelZ', 'accel_z', 'az', 'AccelerationZ'])
            
            # Look for gyroscope data
            gyro_x = self._find_value(data, ['GyroX', 'gyro_x', 'gx', 'AngularVelocityX'])
            gyro_y = self._find_value(data, ['GyroY', 'gyro_y', 'gy', 'AngularVelocityY'])
            gyro_z = self._find_value(data, ['GyroZ', 'gyro_z', 'gz', 'AngularVelocityZ'])
            
            # Look for timestamp
            ts = self._find_value(data, ['timestamp', 'time', 'Timestamp', 'Time'])
            if ts is not None:
                timestamp = float(ts)
            
            # Only create reading if we have at least some accelerometer data
            if accel_x is not None and accel_y is not None and accel_z is not None:
                return IMUReading(
                    timestamp=timestamp,
                    accel_x=float(accel_x),
                    accel_y=float(accel_y),
                    accel_z=float(accel_z),
                    gyro_x=float(gyro_x) if gyro_x is not None else 0.0,
                    gyro_y=float(gyro_y) if gyro_y is not None else 0.0,
                    gyro_z=float(gyro_z) if gyro_z is not None else 0.0
                )
        except (ValueError, TypeError):
            pass
        return None
    
    def _find_value(self, data: dict, keys: List[str]):
        """Find a value in dictionary using multiple possible key names."""
        for key in keys:
            if key in data:
                return data[key]
        return None
    
    def _apply_gravity_compensation(self) -> None:
        """Apply basic gravity compensation to accelerometer data and convert to m/s²."""
        if len(self.imu_data) < 10:
            return
            
        # Estimate gravity vector from first few readings (assuming initial stillness)
        gravity_samples = self.imu_data[:10]
        avg_accel_x = sum(r.accel_x for r in gravity_samples) / len(gravity_samples)
        avg_accel_y = sum(r.accel_y for r in gravity_samples) / len(gravity_samples)
        avg_accel_z = sum(r.accel_z for r in gravity_samples) / len(gravity_samples)
        
        print(f"Applying gravity compensation: estimated gravity vector = [{avg_accel_x:.3f}, {avg_accel_y:.3f}, {avg_accel_z:.3f}] g")
        
        # Apply gravity compensation and convert to m/s²
        for reading in self.imu_data:
            # Subtract gravity (in g-force units)
            reading.accel_x -= avg_accel_x
            reading.accel_y -= avg_accel_y
            reading.accel_z -= avg_accel_z
            
            # Convert from g-force to m/s²
            reading.accel_x *= 9.8
            reading.accel_y *= 9.8
            reading.accel_z *= 9.8
    
    def save_imu_data_csv(self, output_path: Path) -> None:
        """Save extracted IMU data to CSV file."""
        if not self.imu_data:
            print("No IMU data to save")
            return
            
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'accel_x', 'accel_y', 'accel_z', 
                           'gyro_x', 'gyro_y', 'gyro_z'])
            
            for reading in self.imu_data:
                writer.writerow([
                    reading.timestamp, reading.accel_x, reading.accel_y, reading.accel_z,
                    reading.gyro_x, reading.gyro_y, reading.gyro_z
                ])

    def save_heading_data_csv(self, output_path: Path) -> None:
        """Save calculated heading data to CSV file."""
        headings = self.calculate_heading_changes()
        if not headings:
            print("No heading data to save")
            return
            
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['timestamp', 'heading_degrees'])
            
            for timestamp, heading in headings:
                writer.writerow([timestamp, heading])

    def calculate_heading_changes(self) -> List[Tuple[float, float]]:
        """
        Calculate heading changes from gyroscope data.
        
        Returns:
            List of (timestamp, heading_degrees) tuples
        """
        if not self.imu_data:
            return []
        
        headings = []
        current_heading = 0.0  # Start at 0 degrees
        
        for i, reading in enumerate(self.imu_data):
            if i == 0:
                # First reading, assume initial heading
                headings.append((reading.timestamp, current_heading))
                continue
            
            # Calculate time delta
            dt = reading.timestamp - self.imu_data[i-1].timestamp
            if dt <= 0:
                dt = 1.0 / 1000.0  # Fallback to 1ms if invalid
            
            # Integrate gyroscope Z-axis (yaw rate) to get heading change
            # Gyro Z is rotation around the vertical axis (yaw)
            heading_change = reading.gyro_z * dt  # radians
            
            # Convert to degrees
            heading_change_degrees = math.degrees(heading_change)
            current_heading += heading_change_degrees
            
            # Normalize heading to 0-360 degrees
            current_heading = current_heading % 360.0
            if current_heading < 0:
                current_heading += 360.0
            
            headings.append((reading.timestamp, current_heading))
        
        return headings
    
    def get_direction_summary(self) -> dict:
        """
        Get a summary of direction changes and movement patterns.
        
        Returns:
            Dictionary with direction analysis
        """
        if not self.imu_data:
            return {}
        
        headings = self.calculate_heading_changes()
        if not headings:
            return {}
        
        # Calculate total rotation
        total_rotation = 0.0
        direction_changes = 0
        prev_heading = headings[0][1]
        
        for timestamp, heading in headings[1:]:
            # Calculate shortest angular distance
            diff = heading - prev_heading
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            
            total_rotation += abs(diff)
            
            # Count significant direction changes (> 10 degrees)
            if abs(diff) > 10:
                direction_changes += 1
            
            prev_heading = heading
        
        # Calculate average heading change rate
        if len(headings) > 1:
            duration = headings[-1][0] - headings[0][0]
            avg_rotation_rate = total_rotation / duration if duration > 0 else 0
        else:
            avg_rotation_rate = 0
        
        return {
            'total_rotation_degrees': total_rotation,
            'direction_changes_count': direction_changes,
            'average_rotation_rate_deg_per_sec': avg_rotation_rate,
            'initial_heading_degrees': headings[0][1],
            'final_heading_degrees': headings[-1][1],
            'heading_samples': len(headings)
        }

def main():
    """Test the IMU extractor with a sample video file."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract IMU data from Insta360 video")
    parser.add_argument("video", type=Path, help="Path to Insta360 video file")
    parser.add_argument("--output-dir", type=Path, default=Path("."), 
                       help="Output directory for CSV files")
    
    args = parser.parse_args()
    
    if not args.video.exists():
        print(f"Error: Video file not found: {args.video}")
        return 1
    
    # Extract IMU data
    extractor = IMUExtractor(args.video)
    print(f"Extracting IMU data from {args.video}...")
    
    if not extractor.extract_imu_metadata():
        print("Failed to extract IMU data")
        return 1
    
    print(f"Extracted {len(extractor.imu_data)} IMU readings")
    
    # Save data
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    imu_csv = args.output_dir / "imu_data.csv"
    extractor.save_imu_data_csv(imu_csv)
    print(f"IMU data saved to {imu_csv}")
    
    # Save heading data
    heading_csv = args.output_dir / "heading_data.csv"
    extractor.save_heading_data_csv(heading_csv)
    print(f"Heading data saved to {heading_csv}")
    
    # Get and display direction summary
    direction_summary = extractor.get_direction_summary()
    if direction_summary:
        print("\n=== Direction Analysis ===")
        print(f"Total rotation: {direction_summary['total_rotation_degrees']:.1f}°")
        print(f"Direction changes: {direction_summary['direction_changes_count']}")
        print(f"Average rotation rate: {direction_summary['average_rotation_rate_deg_per_sec']:.2f}°/s")
        print(f"Initial heading: {direction_summary['initial_heading_degrees']:.1f}°")
        print(f"Final heading: {direction_summary['final_heading_degrees']:.1f}°")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
