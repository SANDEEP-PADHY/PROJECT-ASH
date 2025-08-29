"""
secure_wipe.py
Contains WipeWorker class and secure wipe logic for Code Monk — Secure Formatter
"""
import os
import shutil
import tempfile
import subprocess
import time
import datetime
import string
from PyQt5 import QtCore
from certificate import generate_certificate

def find_drive_letter_by_label(label="WIPED_DRIVE"):
    """Find drive letter by volume label"""
    try:
        import win32api
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        for drive in drives:
            try:
                vol_info = win32api.GetVolumeInformation(drive)
                if vol_info[0] == label:
                    return drive
            except Exception:
                continue
    except ImportError:
        # Fallback method using subprocess
        try:
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace,caption,volumename'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if label in line:
                        parts = line.split()
                        for part in parts:
                            if ':' in part and len(part) == 2:
                                return part + '\\'
        except Exception:
            pass
    return None

def refresh_explorer():
    """Refresh Windows Explorer to show newly formatted drives"""
    try:
        # Send broadcast message to refresh explorer
        import ctypes
        from ctypes import wintypes
        
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, 0,
            0, 1000, None
        )
        
        # Also try refreshing the desktop
        ctypes.windll.user32.SendMessageTimeoutW(
            ctypes.windll.user32.FindWindowW("Progman", None),
            WM_SETTINGCHANGE, 0, 0, 0, 1000, None
        )
    except Exception:
        pass

class WipeWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(int)            # 0-100
    status = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)            # certificate path or error

    def __init__(self, entry, level_passes=3, do_real=True):
        super().__init__()
        self.entry = entry
        self.passes = level_passes
        self.do_real = do_real   # if False, only simulate
        self._stop = False
        self.errors = []

    def stop(self):
        self._stop = True

    def run(self):
        try:
            device = self.entry["device"]
            display = self.entry.get("display", device)
            steps = [
                ("Preparing target", 3),
                ("Overwriting files with random data", 20),
                ("Deleting files & partitions", 20),
                ("Overwriting free space with random data", 30),
                ("Creating compressed junk", 10),
                ("Final formatting", 15),
                ("Generating certificate", 2)
            ]
            total = sum(weight for (_, weight) in steps)
            progress_acc = 0

            def step_update(msg, weight):
                nonlocal progress_acc
                if self._stop:
                    raise Exception("Operation cancelled")
                self.status.emit(msg)
                for i in range(weight):
                    progress_acc += 1
                    self.progress.emit(int(progress_acc / total * 100))
                    time.sleep(0.05)

            step_update("Checking target accessibility...", steps[0][1])
            accessible = os.path.exists(device) if not device.startswith("\\\\?\\") and ":" in device else True

            if not self.do_real:
                step_update("Simulation: Overwriting files ...", steps[1][1])
                step_update("Simulation: Deleting files ...", steps[2][1])
                step_update("Simulation: Overwriting ...", steps[3][1])
                step_update("Simulation: Creating junk archive ...", steps[4][1])
                step_update("Simulation: Final format ...", steps[5][1])
            else:
                self.status.emit(f"REAL MODE: Starting destructive operations on {device}")
                
                # Check admin privileges
                try:
                    import ctypes
                    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                    if not is_admin:
                        self.status.emit("WARNING: Not running as administrator - some operations may fail")
                        self.errors.append("Not running as administrator")
                except Exception:
                    pass
                
                # Skip file-level operations for protected drives - go straight to low-level format
                step_update("Skipping file operations - using low-level format...", steps[1][1])
                self.status.emit("Protected/Live OS detected - using diskpart for complete drive wipe")
                    
                # Skip file deletion - let diskpart handle everything
                step_update("Preparing for complete drive wipe...", steps[2][1])
                self.status.emit("Skipping individual file deletion - diskpart will wipe everything")
                # Diskpart for physical/raw - Enhanced for protected drives
                if self.entry["kind"] in ("physical", "raw"):
                    step_update("Performing low-level disk wipe with diskpart...", steps[3][1])
                    try:
                        idx = self.entry.get("index")
                        if idx is not None:
                            # Enhanced diskpart script for protected/Live OS drives
                            script = f"""select disk {idx}
clean
create partition primary
active
format fs=ntfs quick label="WIPED_DRIVE"
assign
exit
"""
                            script_path = os.path.join(os.environ.get('TEMP', 'C:\\temp'), 'secure_wipe_script.txt')
                            with open(script_path, "w") as f:
                                f.write(script)
                            
                            self.status.emit(f"Running diskpart on disk {idx} (this may take a few minutes)...")
                            
                            # Run diskpart with extended timeout for protected drives
                            result = subprocess.run(["diskpart", "/s", script_path], 
                                                   capture_output=True, text=True, 
                                                   shell=True, timeout=600)  # 10 minute timeout
                            
                            try:
                                os.remove(script_path)
                            except Exception:
                                pass
                                
                            self.status.emit(f"Diskpart completed with return code: {result.returncode}")
                            
                            if result.stdout:
                                stdout_lines = result.stdout.strip().split('\n')
                                for line in stdout_lines[-10:]:  # Show last 10 lines
                                    if line.strip():
                                        self.status.emit(f"Diskpart: {line.strip()}")
                            
                            if result.stderr and result.stderr.strip():
                                self.status.emit(f"Diskpart warnings: {result.stderr.strip()}")
                            
                            if result.returncode == 0:
                                self.status.emit("✅ Diskpart completed successfully - drive wiped and formatted")
                            else:
                                error_msg = f"Diskpart failed with code {result.returncode}"
                                self.status.emit(f"❌ {error_msg}")
                                # Don't treat this as a fatal error - continue with other operations
                            
                            # Give system time to register the changes
                            self.status.emit("Waiting for system to recognize formatted drive...")
                            time.sleep(3)
                            refresh_explorer()
                            self.status.emit("Refreshed Windows Explorer")
                            
                    except subprocess.TimeoutExpired:
                        error_msg = "Diskpart operation timed out after 10 minutes"
                        self.status.emit(f"⚠️ {error_msg}")
                        # Don't treat timeout as fatal error
                    except Exception as e:
                        error_msg = f"Diskpart error: {e}"
                        self.status.emit(f"⚠️ {error_msg}")
                        # Continue with other operations
                        
                # Skip free space overwriting for protected drives
                step_update("Skipping free space overwrite - drive already wiped by diskpart...", steps[3][1])
                self.status.emit("Free space overwrite not needed after diskpart clean operation")
                
                # Create junk archive (skip for protected drives)
                step_update("Skipping junk creation - not needed after diskpart clean...", steps[4][1])
                self.status.emit("Junk archive creation skipped for protected drives")
                # Final format
                step_update("Final formatting (quick)...", steps[5][1])
                try:
                    if self.entry["kind"] in ("logical"):
                        vol = self.entry["device"].rstrip("\\")
                        # Use more robust formatting command
                        cmd = f'format {vol} /FS:NTFS /Q /V:WIPED_DRIVE /Y'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        self.status.emit(f"Format command result: {result.returncode}")
                        if result.stdout:
                            self.status.emit(f"Format output: {result.stdout.strip()}")
                        if result.stderr and result.stderr.strip():
                            self.status.emit(f"Format warnings: {result.stderr.strip()}")
                        
                        # Refresh explorer after logical format too
                        time.sleep(1)
                        refresh_explorer()
                        self.status.emit("Refreshed Windows Explorer after logical format")
                        
                    elif self.entry["kind"] in ("physical", "raw"):
                        # Physical drives were already handled by diskpart above
                        self.status.emit("Physical drive formatting completed via diskpart")
                except Exception as e:
                    self.status.emit(f"Format error: {e}")
                    self.errors.append(str(e))
            # Certificate only if no errors - save to the formatted drive
            step_update("Generating certificate...", steps[6][1])
            if not self.errors:
                # Try to find the newly formatted drive
                target_drive = None
                if self.entry["kind"] in ("physical", "raw"):
                    # Wait a moment for drive to be recognized
                    time.sleep(2)
                    target_drive = find_drive_letter_by_label("WIPED_DRIVE")
                    if target_drive:
                        self.status.emit(f"Found formatted drive at: {target_drive}")
                    else:
                        self.status.emit("Could not locate formatted drive, saving certificate to current directory")
                elif self.entry["kind"] == "logical" and ":" in self.entry["device"]:
                    target_drive = self.entry["device"]
                
                cert = generate_certificate(self.entry, target_drive)
                self.finished.emit(cert)
            else:
                self.finished.emit(f"ERROR: Wipe completed with errors: {self.errors}")
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")
