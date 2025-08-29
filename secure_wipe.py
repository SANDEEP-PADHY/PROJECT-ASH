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
from PyQt5 import QtCore
from certificate import generate_certificate

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
                # Overwrite files
                step_update("Overwriting files with random data...", steps[1][1])
                if ":" in device and os.path.exists(device):
                    for root, dirs, files in os.walk(device, topdown=False):
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            try:
                                size = os.path.getsize(fpath)
                                with open(fpath, "r+b") as f:
                                    for _ in range(self.passes):
                                        f.seek(0)
                                        f.write(os.urandom(size))
                                        f.flush()
                                self.status.emit(f"Overwritten: {fpath}")
                            except Exception as e:
                                self.status.emit(f"Error overwriting {fpath}: {e}")
                                self.errors.append(str(e))
                # Delete files
                step_update("Deleting files & metadata (best-effort)...", steps[2][1])
                if ":" in device and os.path.exists(device):
                    for root, dirs, files in os.walk(device, topdown=False):
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            try:
                                os.remove(fpath)
                                self.status.emit(f"Deleted: {fpath}")
                            except Exception as e:
                                self.status.emit(f"Error deleting {fpath}: {e}")
                                self.errors.append(str(e))
                        for d in dirs:
                            dpath = os.path.join(root, d)
                            try:
                                shutil.rmtree(dpath)
                                self.status.emit(f"Deleted directory: {dpath}")
                            except Exception as e:
                                self.status.emit(f"Error deleting directory {dpath}: {e}")
                                self.errors.append(str(e))
                # Diskpart for physical/raw
                if self.entry["kind"] in ("physical", "raw"):
                    step_update("Attempting low-level clean (diskpart)", 2)
                    try:
                        idx = self.entry.get("index")
                        if idx is not None:
                            script = f"select disk {idx}\nclean\ncreate partition primary\nformat fs=ntfs quick\nassign\nexit\n"
                            with open("diskpart_script.txt", "w") as f:
                                f.write(script)
                            subprocess.run(["diskpart", "/s", "diskpart_script.txt"], check=False, shell=True)
                            try:
                                os.remove("diskpart_script.txt")
                            except Exception:
                                pass
                    except Exception as e:
                        self.status.emit(f"Diskpart error: {e}")
                        self.errors.append(str(e))
                # Overwrite free space
                step_update(f"Overwriting free space ({self.passes} passes)...", steps[3][1])
                if ":" in device and os.path.exists(device):
                    for p in range(self.passes):
                        if self._stop:
                            raise Exception("Operation cancelled")
                        try:
                            fname = os.path.join(device, f"__cm_trash_pass{p}.bin")
                            with open(fname, "wb") as out:
                                chunk = os.urandom(4 * 1024 * 1024)
                                while True:
                                    out.write(chunk)
                        except (OSError, IOError) as e:
                            try:
                                os.remove(fname)
                            except Exception:
                                pass
                            self.status.emit(f"Free space overwrite error: {e}")
                            self.errors.append(str(e))
                # Create junk archive
                step_update("Creating compressed junk...", steps[4][1])
                try:
                    td = tempfile.mkdtemp()
                    for i in range(3):
                        pth = os.path.join(td, f"junk_{i}.bin")
                        with open(pth, "wb") as f:
                            f.write(os.urandom(2 * 1024 * 1024))
                    shutil.make_archive(os.path.join(".", "cm_junk"), "zip", td)
                    try:
                        os.remove(os.path.join(".", "cm_junk.zip"))
                    except Exception:
                        pass
                    shutil.rmtree(td, ignore_errors=True)
                except Exception as e:
                    self.status.emit(f"Junk archive error: {e}")
                    self.errors.append(str(e))
                # Final format
                step_update("Final formatting (quick)...", steps[5][1])
                try:
                    if self.entry["kind"] in ("logical"):
                        vol = self.entry["device"].rstrip("\\")
                        cmd = f'format {vol} /FS:NTFS /Q /Y'
                        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif self.entry["kind"] in ("physical", "raw"):
                        pass
                except Exception as e:
                    self.status.emit(f"Format error: {e}")
                    self.errors.append(str(e))
            # Certificate only if no errors
            step_update("Generating certificate...", steps[6][1])
            if not self.errors:
                cert = generate_certificate(self.entry)
                self.finished.emit(cert)
            else:
                self.finished.emit(f"ERROR: Wipe completed with errors: {self.errors}")
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")
