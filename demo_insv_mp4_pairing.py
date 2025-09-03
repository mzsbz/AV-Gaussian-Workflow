#!/usr/bin/env python3
"""
Demonstration script showing how .insv and .mp4 file pairing works.

This script shows the workflow for using .insv files for IMU data extraction
while using .mp4 files for frame extraction.
"""

import sys
from pathlib import Path
from extract_360video_imu import find_insv_file_for_mp4, _resolve_default_input
from config import DATASET_PATH

def demonstrate_file_pairing():
    """Demonstrate how .insv and .mp4 files are paired."""
    print("=== Insta360 .insv/.mp4 File Pairing Demo ===\n")
    
    # Check what files are available
    video_dir = DATASET_PATH / "_source" / "original"
    print(f"Checking for video files in: {video_dir}")
    
    if not video_dir.exists():
        print(f"Directory {video_dir} does not exist")
        return
    
    # List available files
    mp4_files = sorted(video_dir.glob("*.mp4"))
    insv_files = sorted(video_dir.glob("*.insv")) + sorted(video_dir.glob("*.INSV"))
    
    print(f"Found {len(mp4_files)} .mp4 files:")
    for f in mp4_files:
        print(f"  • {f.name}")
    
    print(f"Found {len(insv_files)} .insv files:")
    for f in insv_files:
        print(f"  • {f.name}")
    
    print()
    
    # Demonstrate pairing
    if mp4_files:
        print("=== File Pairing Examples ===")
        for mp4_file in mp4_files[:3]:  # Show first 3 examples
            insv_file = find_insv_file_for_mp4(mp4_file)
            if insv_file:
                print(f"✅ {mp4_file.name} → {insv_file.name}")
                print(f"   IMU data will be extracted from: {insv_file.name}")
                print(f"   Frames will be extracted from: {mp4_file.name}")
            else:
                print(f"❌ {mp4_file.name} → No corresponding .insv file found")
                print(f"   Will try to extract IMU data from: {mp4_file.name}")
            print()
    
    # Show workflow
    print("=== Workflow Summary ===")
    print("1. Place both .insv and .mp4 files in _source/original/")
    print("2. Run: python extract_360video_imu.py video.mp4 --every-seconds 5.0")
    print("3. System automatically:")
    print("   • Finds video.mp4.insv for IMU data extraction")
    print("   • Uses video.mp4 for frame extraction")
    print("   • Extracts frames at regular time intervals")
    print("   • Analyzes IMU data for movement patterns")
    print()
    
    print("=== Benefits ===")
    print("• .insv files contain raw IMU data (better for movement analysis)")
    print("• .mp4 files are processed/compressed (better for frame extraction)")
    print("• Automatic pairing eliminates manual file management")
    print("• Fallback to .mp4 IMU extraction if no .insv file found")

def main():
    """Main demonstration function."""
    print("Insta360 .insv/.mp4 File Pairing Demonstration")
    print("=" * 60)
    
    demonstrate_file_pairing()
    
    print("\n=== Ready to Use ===")
    print("The system is ready to automatically pair your .insv and .mp4 files!")
    print("Just run: python extract_360video_imu.py --every-seconds 5.0")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
