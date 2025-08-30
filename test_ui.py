"""
test_ui.py
Simple test script to verify UI functionality
"""
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    # Test basic imports
    try:
        import platform
        print(f"✅ Platform: {platform.system()} {platform.release()}")
    except ImportError as e:
        print(f"❌ Platform import failed: {e}")
        return False
    
    # Test GUI frameworks
    gui_available = []
    
    try:
        import PyQt5.QtWidgets
        gui_available.append("PyQt5")
        print("✅ PyQt5 available")
    except ImportError:
        print("⚠️ PyQt5 not available")
    
    try:
        import PyQt6.QtWidgets
        gui_available.append("PyQt6")
        print("✅ PyQt6 available")
    except ImportError:
        print("⚠️ PyQt6 not available")
    
    try:
        import tkinter
        gui_available.append("tkinter")
        print("✅ tkinter available")
    except ImportError:
        print("❌ tkinter not available")
    
    if not gui_available:
        print("❌ No GUI frameworks available")
        return False
    
    # Test project modules
    try:
        from linux_compat import is_admin, detect_drives
        print("✅ linux_compat module available")
    except ImportError as e:
        print(f"❌ linux_compat import failed: {e}")
        return False
    
    try:
        from main_crossplatform import SecureWipeWorker
        print("✅ main_crossplatform module available")
    except ImportError as e:
        print(f"❌ main_crossplatform import failed: {e}")
        return False
    
    return True

def test_drive_detection():
    """Test drive detection functionality with detailed debugging"""
    print("\nTesting drive detection...")
    try:
        from linux_compat import detect_drives, is_admin
        import platform
        
        print(f"Platform: {platform.system()}")
        print(f"Admin privileges: {'Yes' if is_admin() else 'No'}")
        print("-" * 50)
        
        drives = detect_drives()
        
        if not drives:
            print("❌ No drives detected!")
            print("This could indicate:")
            print("  • Missing system utilities (lsblk on Linux)")
            print("  • Permission issues")
            print("  • PowerShell execution policy on Windows")
            return False
        
        print(f"✅ Detected {len(drives)} drives:")
        
        # Group drives by type
        physical_drives = [d for d in drives if d.get('kind') == 'physical']
        logical_drives = [d for d in drives if d.get('kind') == 'logical']
        
        if physical_drives:
            print(f"\n  Physical Drives ({len(physical_drives)}):")
            for i, drive in enumerate(physical_drives, 1):
                display = drive.get('display', drive.get('device', 'Unknown'))
                size = drive.get('size_gb', 0)
                model = drive.get('model', 'Unknown')
                print(f"    {i}. {display}")
                print(f"       Device: {drive.get('device')}")
                print(f"       Model: {model}")
                print(f"       Size: {size} GB")
        
        if logical_drives:
            print(f"\n  Logical Drives ({len(logical_drives)}):")
            for i, drive in enumerate(logical_drives, 1):
                display = drive.get('display', drive.get('device', 'Unknown'))
                mountpoint = drive.get('mountpoint', 'N/A')
                print(f"    {i}. {display}")
                print(f"       Device: {drive.get('device')}")
                if mountpoint != 'N/A':
                    print(f"       Mount: {mountpoint}")
        
        # Validate drive data structure
        for i, drive in enumerate(drives):
            required_fields = ['kind', 'device', 'display']
            missing_fields = [field for field in required_fields if field not in drive]
            if missing_fields:
                print(f"⚠️  Drive {i+1} missing fields: {missing_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Drive detection failed: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("PROJECT ASH - UI COMPATIBILITY TEST")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test drive detection
    if not test_drive_detection():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED - UI should work correctly")
        print("\nRecommended launch command:")
        print("python ui_launcher.py")
    else:
        print("❌ SOME TESTS FAILED - Check installation")
        print("\nTry installing missing dependencies:")
        print("pip install -r requirements.txt")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
