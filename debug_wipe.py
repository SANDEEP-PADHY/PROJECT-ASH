"""
Debug version of secure wipe with extensive logging
"""
import os
import sys
import subprocess
import time

def test_diskpart_on_device(device_letter):
    """Test diskpart operations on a specific device"""
    print(f"Testing diskpart operations on {device_letter}")
    
    # Check admin privileges
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Running as admin: {is_admin}")
        if not is_admin:
            print("ERROR: Not running as administrator!")
            return False
    except Exception as e:
        print(f"Could not check admin status: {e}")
        return False
    
    # Get disk index for the drive
    try:
        result = subprocess.run(
            ['wmic', 'logicaldisk', 'where', f'DeviceID="{device_letter}"', 'get', 'DeviceID,Size,FreeSpace,VolumeName'],
            capture_output=True, text=True, shell=True
        )
        print(f"Drive info output:\n{result.stdout}")
        
        # Get physical disk info
        result2 = subprocess.run(['diskpart'], input='list disk\nexit\n', capture_output=True, text=True, shell=True)
        print(f"Diskpart list disk output:\n{result2.stdout}")
        
    except Exception as e:
        print(f"Error getting drive info: {e}")
        return False
    
    # Ask user for disk number (since auto-detection might be failing)
    try:
        disk_num = input(f"What disk number corresponds to {device_letter}? (Check diskpart output above): ")
        disk_num = int(disk_num.strip())
    except ValueError:
        print("Invalid disk number")
        return False
    
    print(f"Using disk number: {disk_num}")
    
    # Create and run diskpart script
    script_content = f"""select disk {disk_num}
clean
create partition primary
active
format fs=ntfs quick label="DEBUG_WIPED"
assign
exit
"""
    
    script_path = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'debug_diskpart.txt')
    print(f"Writing diskpart script to: {script_path}")
    print("Script content:")
    print(script_content)
    
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        print("\nRunning diskpart...")
        result = subprocess.run(
            ["diskpart", "/s", script_path],
            capture_output=True,
            text=True
        )
        
        print(f"Diskpart return code: {result.returncode}")
        print(f"Diskpart stdout:\n{result.stdout}")
        print(f"Diskpart stderr:\n{result.stderr}")
        
        # Clean up
        try:
            os.remove(script_path)
        except:
            pass
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running diskpart: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_wipe.py E:")
        print("Where E: is the drive letter to test")
        sys.exit(1)
    
    device = sys.argv[1].upper()
    if not device.endswith(':'):
        device += ':'
    
    print(f"Debug wiping test on {device}")
    print("WARNING: This will DESTROY ALL DATA on the specified drive!")
    
    confirm = input(f"Are you sure you want to test format {device}? Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("Cancelled")
        sys.exit(0)
    
    success = test_diskpart_on_device(device)
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
