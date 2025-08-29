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
    """Detect drives on Linux using multiple methods"""
    drives = []
    
    # Method 1: Use lsblk command (most reliable)
    try:
        result = subprocess.run(['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,MODEL'], 
                              capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        for device in data.get('blockdevices', []):
            if device['type'] == 'disk':
                size_bytes = parse_size(device.get('size', '0'))
                size_gb = size_bytes // (1024**3) if size_bytes else 0
                
                drives.append({
                    "kind": "physical",
                    "device": f"/dev/{device['name']}",
                    "model": device.get('model', 'Unknown'),
                    "size_gb": size_gb,
                    "display": f"/dev/{device['name']} - {device.get('model', 'Unknown')} ({size_gb} GB)"
                })
                
                # Add partitions as logical drives
                for child in device.get('children', []):
                    if child['type'] == 'part':
                        part_size = parse_size(child.get('size', '0'))
                        part_gb = part_size // (1024**3) if part_size else 0
                        mountpoint = child.get('mountpoint', 'Not mounted')
                        
                        drives.append({
                            "kind": "logical",
                            "device": f"/dev/{child['name']}",
                            "parent_physical": f"/dev/{device['name']}",
                            "size_gb": part_gb,
                            "mountpoint": mountpoint,
                            "display": f"/dev/{child['name']} - Partition ({part_gb} GB) - {mountpoint}"
                        })
    except Exception as e:
        print(f"lsblk detection failed: {e}")
    
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
    """Original Windows drive detection"""
    import ctypes
    import string
    try:
        import wmi
    except ImportError:
        return []
    
    drives = []
    # ... (keep original Windows code)
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
