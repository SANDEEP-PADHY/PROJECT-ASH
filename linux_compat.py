"""
linux_compat.py
Linux compatibility layer for Project ASH Secure Formatter
Cross-platform drive detection and disk operations
"""
import os
import sys
import subprocess
import json
import re
from pathlib import Path
import platform

def is_admin():
    """Check if running with administrator/root privileges"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def detect_linux_drives():
    """Detect drives on Linux using multiple methods with robust error handling"""
    drives = []
    
    # Method 1: Use lsblk command (most reliable)
    print("[DEBUG] Attempting lsblk drive detection...")
    try:
        # Check if lsblk exists
        check_result = subprocess.run(['which', 'lsblk'], capture_output=True, text=True)
        if check_result.returncode != 0:
            print("[DEBUG] lsblk command not found, trying alternative methods")
            raise FileNotFoundError("lsblk not available")
        
        result = subprocess.run(['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,MODEL'], 
                              capture_output=True, text=True, timeout=10)
        
        print(f"[DEBUG] lsblk exit code: {result.returncode}")
        print(f"[DEBUG] lsblk stdout length: {len(result.stdout)}")
        
        if result.returncode != 0:
            print(f"[DEBUG] lsblk stderr: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, 'lsblk')
        
        if not result.stdout.strip():
            print("[DEBUG] lsblk returned empty output")
            raise ValueError("Empty lsblk output")
        
        # Debug: print raw output
        print(f"[DEBUG] Raw lsblk output: {result.stdout[:200]}...")
        
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON parse error: {e}")
            print(f"[DEBUG] Raw output: {result.stdout}")
            raise
        
        blockdevices = data.get('blockdevices', [])
        print(f"[DEBUG] Found {len(blockdevices)} block devices")
        
        for device in blockdevices:
            device_type = device.get('type', 'unknown')
            device_name = device.get('name', 'unknown')
            print(f"[DEBUG] Processing device: {device_name} (type: {device_type})")
            
            if device_type == 'disk':
                size_bytes = parse_size(device.get('size', '0'))
                size_gb = size_bytes // (1024**3) if size_bytes else 0
                model = device.get('model') or 'Unknown Device'
                
                drives.append({
                    "kind": "physical",
                    "device": f"/dev/{device_name}",
                    "model": model,
                    "size_gb": size_gb,
                    "display": f"/dev/{device_name} - {model} ({size_gb} GB)"
                })
                
                # Add partitions as logical drives
                children = device.get('children', [])
                print(f"[DEBUG] Device {device_name} has {len(children)} partitions")
                
                for child in children:
                    if child.get('type') == 'part':
                        part_name = child.get('name', 'unknown')
                        part_size = parse_size(child.get('size', '0'))
                        part_gb = part_size // (1024**3) if part_size else 0
                        mountpoint = child.get('mountpoint') or 'Not mounted'
                        
                        drives.append({
                            "kind": "logical",
                            "device": f"/dev/{part_name}",
                            "parent_physical": f"/dev/{device_name}",
                            "size_gb": part_gb,
                            "mountpoint": mountpoint,
                            "display": f"/dev/{part_name} - Partition ({part_gb} GB) - {mountpoint}"
                        })
        
        print(f"[DEBUG] lsblk method found {len(drives)} drives")
        
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, 
            json.JSONDecodeError, ValueError) as e:
        print(f"[DEBUG] lsblk detection failed: {e}")
        drives = []
    
    # Method 2: Parse /proc/partitions as fallback
    if not drives:
        try:
            with open('/proc/partitions', 'r') as f:
                lines = f.readlines()[2:]  # Skip header
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        major, minor, blocks, name = parts
                        if not re.match(r'.*\d+$', name):  # Whole disk, not partition
                            size_gb = int(blocks) * 1024 // (1024**3)
                            drives.append({
                                "kind": "physical",
                                "device": f"/dev/{name}",
                                "model": "Unknown",
                                "size_gb": size_gb,
                                "display": f"/dev/{name} - Physical Drive ({size_gb} GB)"
                            })
        except Exception as e:
            print(f"proc/partitions detection failed: {e}")
    
    return drives

def detect_windows_drives():
    """Enhanced Windows drive detection with multiple methods"""
    import ctypes
    import string
    drives = []
    
    print("[DEBUG] Starting Windows drive detection...")
    
    # Method 1: PowerShell Get-PhysicalDisk (modern approach)
    try:
        print("[DEBUG] Trying PowerShell Get-PhysicalDisk...")
        ps_cmd = [
            'powershell', '-Command',
            'Get-PhysicalDisk | ConvertTo-Json -Depth 2'
        ]
        result = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"[DEBUG] PowerShell output length: {len(result.stdout)}")
            try:
                ps_data = json.loads(result.stdout)
                if not isinstance(ps_data, list):
                    ps_data = [ps_data]  # Single disk case
                
                for disk in ps_data:
                    size_bytes = disk.get('Size', 0)
                    size_gb = int(size_bytes) // (1024**3) if size_bytes else 0
                    model = disk.get('FriendlyName', 'Unknown Drive')
                    device_id = disk.get('DeviceId', 0)
                    
                    drives.append({
                        "kind": "physical",
                        "device": f"\\.\PhysicalDrive{device_id}",
                        "model": model,
                        "size_gb": size_gb,
                        "display": f"PhysicalDrive{device_id} - {model} ({size_gb} GB)",
                        "index": device_id
                    })
                
                print(f"[DEBUG] PowerShell method found {len(drives)} drives")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] PowerShell JSON parse error: {e}")
        else:
            print(f"[DEBUG] PowerShell failed: {result.stderr}")
    
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[DEBUG] PowerShell method failed: {e}")
    
    # Method 2: WMI fallback (if available)
    if not drives:
        try:
            print("[DEBUG] Trying WMI method...")
            import wmi
            c = wmi.WMI()
            
            for disk in c.Win32_DiskDrive():
                size_bytes = int(disk.Size) if disk.Size else 0
                size_gb = size_bytes // (1024**3) if size_bytes else 0
                model = disk.Caption or disk.Model or "Physical Disk"
                device_id = disk.DeviceID  # like '\\.\PHYSICALDRIVE0'
                index = int(disk.Index) if disk.Index is not None else 0
                
                drives.append({
                    "kind": "physical",
                    "device": device_id,
                    "model": model,
                    "size_gb": size_gb,
                    "display": f"PhysicalDrive{index} - {model} ({size_gb} GB)",
                    "index": index
                })
            
            print(f"[DEBUG] WMI method found {len(drives)} drives")
            
        except ImportError:
            print("[DEBUG] WMI not available")
        except Exception as e:
            print(f"[DEBUG] WMI method failed: {e}")
    
    # Method 3: Direct ctypes probing for PhysicalDrive devices
    if not drives:
        print("[DEBUG] Trying direct PhysicalDrive probing...")
        for i in range(32):  # Check first 32 physical drives
            device_path = f"\\.\PhysicalDrive{i}"
            try:
                # Try to open the device handle
                handle = ctypes.windll.kernel32.CreateFileW(
                    device_path,
                    0,  # No access needed, just check existence
                    3,  # FILE_SHARE_READ | FILE_SHARE_WRITE
                    None,
                    3,  # OPEN_EXISTING
                    0,
                    None
                )
                
                if handle != -1:  # INVALID_HANDLE_VALUE
                    ctypes.windll.kernel32.CloseHandle(handle)
                    drives.append({
                        "kind": "physical",
                        "device": device_path,
                        "model": f"Physical Drive {i}",
                        "size_gb": 0,  # Size unknown with this method
                        "display": f"PhysicalDrive{i} - Physical Drive ({i})",
                        "index": i
                    })
            except Exception:
                continue  # Drive doesn't exist or no access
        
        print(f"[DEBUG] Direct probing found {len(drives)} drives")
    
    # Method 4: Add logical drives
    print("[DEBUG] Adding logical drives...")
    logical_count = 0
    try:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive_path))
                
                # Only include fixed drives (type 3) and removable (type 2)
                if drive_type in [2, 3]:
                    type_name = "Fixed" if drive_type == 3 else "Removable"
                    drives.append({
                        "kind": "logical",
                        "device": drive_path,
                        "model": f"{type_name} Drive",
                        "size_gb": 0,
                        "display": f"{letter}: - {type_name} Drive",
                        "drive_type": drive_type
                    })
                    logical_count += 1
    except Exception as e:
        print(f"[DEBUG] Logical drive detection failed: {e}")
    
    print(f"[DEBUG] Added {logical_count} logical drives")
    print(f"[DEBUG] Total Windows drives found: {len(drives)}")
    
    return drives

def detect_drives():
    """Cross-platform drive detection"""
    if platform.system() == "Windows":
        return detect_windows_drives()
    else:
        return detect_linux_drives()

def parse_size(size_str):
    """Parse size strings like '500G', '1.5T' to bytes"""
    if not size_str or size_str == '0':
        return 0
    
    size_str = size_str.upper().strip()
    multipliers = {
        'B': 1,
        'K': 1024,
        'M': 1024**2,
        'G': 1024**3,
        'T': 1024**4
    }
    
    # Extract number and unit
    match = re.match(r'([0-9.]+)([BKMGT]?)', size_str)
    if match:
        number, unit = match.groups()
        return int(float(number) * multipliers.get(unit, 1))
    return 0

def secure_wipe_linux(device_path, passes=3):
    """Linux-specific secure wipe operations"""
    commands = []
    
    # 1. Unmount if mounted
    commands.append(['umount', device_path])
    
    # 2. Wipe filesystem signatures
    commands.append(['wipefs', '-a', device_path])
    
    # 3. Multiple pass overwrite with dd
    for i in range(passes):
        # Random data pass
        commands.append(['dd', f'if=/dev/urandom', f'of={device_path}', 'bs=1M', 'status=progress'])
        # Zero pass
        commands.append(['dd', f'if=/dev/zero', f'of={device_path}', 'bs=1M', 'status=progress'])
    
    # 4. Create new partition table
    commands.append(['parted', device_path, '--script', 'mklabel', 'gpt'])
    
    # 5. Create primary partition
    commands.append(['parted', device_path, '--script', 'mkpart', 'primary', 'ext4', '0%', '100%'])
    
    # 6. Format as ext4
    partition = f"{device_path}1" if not device_path.endswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')) else device_path
    commands.append(['mkfs.ext4', '-F', partition])
    
    return commands

def secure_wipe_windows(device_path, passes=3):
    """Windows-specific secure wipe operations"""
    # Keep original Windows diskpart logic
    commands = []
    # ... (original Windows implementation)
    return commands

def get_wipe_commands(device_path, passes=3):
    """Get platform-specific wipe commands"""
    if platform.system() == "Windows":
        return secure_wipe_windows(device_path, passes)
    else:
        return secure_wipe_linux(device_path, passes)

def execute_secure_command(cmd, timeout=300):
    """Execute a command with proper error handling and timeout"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              timeout=timeout, check=False)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

# GUI Framework compatibility
def get_gui_framework():
    """Determine best GUI framework for the platform"""
    try:
        from PyQt5 import QtWidgets
        return "PyQt5"
    except ImportError:
        try:
            from PyQt6 import QtWidgets
            return "PyQt6"
        except ImportError:
            try:
                import tkinter
                return "tkinter"
            except ImportError:
                return None

def create_cross_platform_app():
    """Create a cross-platform application instance"""
    framework = get_gui_framework()
    
    if framework in ["PyQt5", "PyQt6"]:
        if framework == "PyQt5":
            from PyQt5 import QtWidgets
        else:
            from PyQt6 import QtWidgets
        
        import sys
        app = QtWidgets.QApplication(sys.argv)
        return app, framework
    elif framework == "tkinter":
        import tkinter as tk
        app = tk.Tk()
        return app, framework
    else:
        raise RuntimeError("No supported GUI framework found")
