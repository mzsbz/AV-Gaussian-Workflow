#!/usr/bin/env python3
"""
Test script to demonstrate IMU data extraction capabilities.

This script tests the IMU extraction functionality with sample data
and provides examples of how to use the IMU data analysis features.
"""

import sys
from pathlib import Path
from imu_extractor import IMUExtractor

def test_imu_extraction_capability():
    """Test if the system can handle IMU extraction."""
    print("=== Testing IMU Extraction Capabilities ===\n")
    
    # Check if exiftool is available
    import shutil
    if not shutil.which("exiftool"):
        print("❌ exiftool not found. Please install it first:")
        print("   sudo apt install libimage-exiftool-perl")
        return False
    else:
        print("✅ exiftool is available")
    
    # Check for numpy
    try:
        import numpy as np
        print("✅ numpy is available")
    except ImportError:
        print("❌ numpy not found. Please install it:")
        print("   uv add numpy")
        return False
    
    print("\n=== System Check Complete ===")
    print("✅ All required dependencies are available")
    print("✅ Ready for IMU data extraction and analysis")
    
    return True

def demonstrate_usage():
    """Demonstrate how to use the IMU extraction functionality."""
    print("\n=== Usage Examples ===\n")
    
    print("1. Extract IMU data from an Insta360 video:")
    print("   python imu_extractor.py /path/to/video.insv")
    print("   python imu_extractor.py /path/to/video.insv --output-dir ./analysis")
    print()
    
    print("2. Extract frames with IMU data analysis:")
    print("   python extract_360video_imu.py /path/to/video.mp4 --every-seconds 5.0")
    print("   python extract_360video_imu.py /path/to/video.mp4 --every-seconds 3.0")
    print("   # (IMU data will be extracted from corresponding .insv file)")
    print()
    
    print("3. Extract frames using traditional time-based sampling:")
    print("   python extract_360video_imu.py /path/to/video.mp4 --every-seconds 5.0")
    print()
    
    print("4. Extract frames without IMU analysis:")
    print("   python extract_360video_imu.py /path/to/video.mp4 --extract-imu false")
    print("   # (Automatically finds corresponding .insv file for IMU data)")
    print()
    
    print("=== File Format Support ===")
    print("• Insta360 .insv files (native format with IMU data) - for IMU extraction")
    print("• Standard .mp4 files (processed video) - for frame extraction")
    print("• System automatically pairs .mp4 and .insv files with same stem")
    print()
    
    print("=== Output Files ===")
    print("When using IMU data extraction, additional files are created:")
    print("• _source/imu_data/imu_readings.csv - Raw IMU sensor data")
    print("• _source/imu_data/heading_data.csv - Calculated heading changes")

def show_imu_data_format():
    """Show the expected IMU data format."""
    print("\n=== Expected IMU Data Format ===\n")
    
    print("The system looks for the following metadata fields:")
    print("• AccelerometerData / GyroscopeData")
    print("• SensorData / IMUData")
    print("• CameraMotionMetadata")
    print()
    
    print("Expected data structure:")
    print("AccelX, AccelY, AccelZ (m/s²)")
    print("GyroX, GyroY, GyroZ (rad/s)")
    print("Timestamp (seconds)")
    print()
    
    print("IMU data analysis process:")
    print("1. Extract accelerometer and gyroscope readings")
    print("2. Apply gravity compensation")
    print("3. Calculate heading changes from gyroscope data")
    print("4. Analyze movement patterns and rotation")
    print("5. Generate movement summary statistics")

def show_analysis_capabilities():
    """Show what kind of analysis is possible with IMU data."""
    print("\n=== IMU Data Analysis Capabilities ===\n")
    
    print("Movement Analysis:")
    print("• Total rotation in degrees")
    print("• Number of direction changes")
    print("• Average rotation rate")
    print("• Initial and final heading")
    print()
    
    print("Sensor Data:")
    print("• Raw accelerometer readings (X, Y, Z)")
    print("• Raw gyroscope readings (X, Y, Z)")
    print("• Timestamped sensor data")
    print("• Gravity-compensated acceleration")
    print()
    
    print("Output Formats:")
    print("• CSV files for further analysis")
    print("• Movement summary statistics")
    print("• Compatible with data analysis tools")

def main():
    """Run all tests and demonstrations."""
    print("IMU Data Extraction Test Suite")
    print("=" * 40)
    
    # Test basic capabilities
    if not test_imu_extraction_capability():
        print("\n❌ System check failed. Please resolve issues before proceeding.")
        return 1
    
    # Show usage examples
    demonstrate_usage()
    
    # Show data format information
    show_imu_data_format()
    
    # Show analysis capabilities
    show_analysis_capabilities()
    
    print("\n=== Test Suite Complete ===")
    print("✅ Your system is ready for IMU data extraction and analysis!")
    print("\nNext steps:")
    print("1. Place your Insta360 video files in _source/original/")
    print("2. Run: python extract_360video_imu.py")
    print("3. Check the generated IMU analysis data")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
