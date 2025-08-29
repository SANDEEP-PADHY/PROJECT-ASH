"""
test_drive_detection.py
Simple test to verify drive detection and certificate placement functionality
"""
from secure_wipe import find_drive_letter_by_label, refresh_explorer
from certificate import generate_certificate
import time

def test_drive_detection():
    print("Testing drive detection...")
    
    # Test finding a drive with common labels
    test_labels = ["WIPED_DRIVE", "New Volume", ""]
    
    for label in test_labels:
        print(f"Looking for drives with label: '{label}'")
        drive = find_drive_letter_by_label(label)
        if drive:
            print(f"  Found drive: {drive}")
        else:
            print(f"  No drive found with label: '{label}'")
    
    print("\nTesting Windows Explorer refresh...")
    refresh_explorer()
    print("Explorer refresh attempted")
    
    print("\nTesting certificate generation...")
    test_entry = {
        "display": "Test Drive",
        "device": "C:\\",
        "kind": "logical"
    }
    
    # Test saving to current directory
    cert1 = generate_certificate(test_entry)
    print(f"Certificate 1: {cert1}")
    
    # Test saving to a specific drive (if available)
    cert2 = generate_certificate(test_entry, "C:\\")
    print(f"Certificate 2: {cert2}")

if __name__ == "__main__":
    test_drive_detection()
