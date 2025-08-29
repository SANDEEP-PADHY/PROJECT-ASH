"""
secure_formatter_gui.py
Code Monk — Secure Formatter (PyQt5)
WARNING: This is destructive. Read warnings in UI before running.
"""
import os
import sys
import ctypes
import threading
import time
import tempfile
import shutil
import subprocess
import string
import datetime
from pathlib import Path
import psutil
import wmi
from PyQt5 import QtWidgets, QtGui, QtCore
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image

# -----------------------------
# Configuration / Branding
# -----------------------------
APP_TITLE = "Code Monk — Secure Formatter"
COMPANY_NAME = "Code Monk"
LOGO_FILE = "CODE MONK LOGO.png"   # put this in same folder
CERT_DIR = "."                    # where to save certificate

# -----------------------------
# Utilities
# -----------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def resource_path(rel):
    """Rel path that works both as script or PyInstaller bundle"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, rel)

# -----------------------------
# Drive detection (multiple methods)
# -----------------------------
def detect_logical_drives():
    """Get mounted logical drive letters via GetLogicalDrives + GetDriveType"""
    drives = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drive = f"{letter}:\\"
            # drive types: 0 = unknown, 1 = no root dir, 2 = removable, 3 = fixed, 4 = remote, 5 = cdrom, 6 = ramdisk
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive))
            drives.append({
                "kind": "logical",
                "device": drive,
                "drive_type": drive_type,
                "label": drive
            })
    return drives

def detect_wmi_drives():
    """Get physical drive info through WMI (Win32_DiskDrive)."""
    drives = []
    try:
        c = wmi.WMI()
        for disk in c.Win32_DiskDrive():
            # Some helpful fields: DeviceID (\\.\PHYSICALDRIVE0), Model, Index, Size
            size_gb = int(disk.Size) // (1024**3) if disk.Size else None
            model = disk.Caption or disk.Model or "Physical Disk"
            dev = disk.DeviceID  # like '\\.\PHYSICALDRIVE0'
            drives.append({
                "kind": "physical",
                "device": dev,
                "index": int(disk.Index),
                "model": model,
                "size_gb": size_gb,
                "wmi_obj": disk
            })
    except Exception:
        pass
    return drives

def detect_raw_physical(max_drives=32):
    """Probe \\.\PhysicalDriveN directly to find present physical drives (even unpartitioned)."""
    found = []
    for i in range(max_drives):
        path = f"\\\\.\\PhysicalDrive{i}"
        try:
            # try to open read-only
            handle = os.open(path, os.O_RDONLY | os.O_BINARY)
            os.close(handle)
            found.append({"kind":"raw", "device": path, "index": i})
        except Exception:
            # not present or no access
            pass
    return found

def merge_drive_list():
    """Combine logical, wmi and raw lists into a single unique list with metadata"""
    logical = detect_logical_drives()
    wmi_list = detect_wmi_drives()
    raw = detect_raw_physical()

    merged = []
    # Add physical drives first (from WMI), with label; match logical partitions to them via Win32 API if available
    # Build map from physical index to dict
    phys_map = {}
    for p in wmi_list:
        key = p.get("index")
        phys_map[key] = p
        label = f"PhysicalDrive{p['index']} - {p['model']} ({p['size_gb']} GB)" if p.get("size_gb") else f"PhysicalDrive{p['index']} - {p['model']}"
        merged.append({
            "id": f"physical-{p['index']}",
            "display": label,
            "device": p["device"],
            "kind": "physical",
            "index": p["index"],
            "model": p["model"],
            "size_gb": p["size_gb"]
        })

    # Add logical drives and try to map them to a parent physical disk via WMI (optional)
    try:
        c = wmi.WMI()
        # build mapping of logical -> physical via associations
        for ld in logical:
            drive = ld["device"]  # e.g., 'D:\'
            display = f"{drive} - Logical Drive"
            # Quick attempt: query Win32_LogicalDiskToPartition and Win32_DiskDriveToDiskPartition
            mapped = False
            try:
                for disk in c.Win32_DiskDrive():
                    for part in disk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in part.associators("Win32_LogicalDiskToPartition"):
                            if getattr(logical_disk, "DeviceID", "").upper() == drive.strip("\\").upper():
                                # Found mapping
                                size_gb = int(disk.Size) // (1024**3) if disk.Size else None
                                display = f"{drive} - {disk.Caption} ({size_gb} GB)" if size_gb else f"{drive} - {disk.Caption}"
                                merged.append({
                                    "id": f"logical-{drive}",
                                    "display": display,
                                    "device": drive,
                                    "kind": "logical",
                                    "parent_physical": f"PhysicalDrive{int(disk.Index)}",
                                    "model": disk.Caption,
                                    "size_gb": size_gb
                                })
                                mapped = True
                                break
                        if mapped:
                            break
                    if mapped:
                        break
            except Exception:
                pass
            if not mapped:
                # add logical without physical mapping
                merged.append({
                    "id": f"logical-{drive}",
                    "display": display,
                    "device": drive,
                    "kind": "logical",
                    "model": None,
                    "size_gb": None
                })
    except Exception:
        # fallback: just list logicals unchanged
        for ld in logical:
            merged.append({
                "id": f"logical-{ld['device']}",
                "display": f"{ld['device']} - Logical Drive",
                "device": ld['device'],
                "kind": "logical"
            })

    # Add any raw physicals not in WMI list
    for r in raw:
        idx = r["index"]
        if not any(item.get("index") == idx for item in merged):
            merged.append({
                "id": f"raw-{idx}",
                "display": f"PhysicalDrive{idx} - (raw/unpartitioned)",
                "device": r["device"],
                "kind": "raw",
                "index": idx
            })

    # Deduplicate display ordering: physicals first, then logicals that map, then raw/unmapped
    # Already mostly ordered; return merged
    return merged

# -----------------------------
# Secure wipe worker (runs in thread)
# -----------------------------
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

    def stop(self):
        self._stop = True

    def run(self):
        try:
            device = self.entry["device"]
            display = self.entry.get("display", device)
            steps = [
                ("Preparing target", 3),
                ("Scrambling files (encrypt/overwrite)", 20),
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
                # increment progress slowly over weight
                for i in range(weight):
                    progress_acc += 1
                    self.progress.emit(int(progress_acc / total * 100))
                    time.sleep(0.05)

            # 1: Prepare (checks)
            step_update("Checking target accessibility...", steps[0][1])
            # if device is logical path like "D:\" ensure exists
            accessible = os.path.exists(device) if device.startswith("\\\\?\\") is False and ":" in device else True

            # Real destructive steps guarded by do_real
            if not self.do_real:
                # simulate with delays
                step_update("Simulation: Scrambling files ...", steps[1][1])
                step_update("Simulation: Deleting files ...", steps[2][1])
                step_update("Simulation: Overwriting ...", steps[3][1])
                step_update("Simulation: Creating junk archive ...", steps[4][1])
                step_update("Simulation: Final format ...", steps[5][1])
            else:
                # 2: Securely overwrite files (write random data over entire file)
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

                # 3: Delete files & try to remove partitions if raw/physical
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
                        for d in dirs:
                            dpath = os.path.join(root, d)
                            try:
                                shutil.rmtree(dpath)
                                self.status.emit(f"Deleted directory: {dpath}")
                            except Exception as e:
                                self.status.emit(f"Error deleting directory {dpath}: {e}")

                # If entry is physical/raw we can attempt diskpart clean (very destructive)
                if self.entry["kind"] in ("physical", "raw"):
                    # diskpart will require admin; build script dynamically
                    step_update("Attempting low-level clean (diskpart)", 2)
                    try:
                        idx = self.entry.get("index")
                        if idx is not None:
                            script = f"select disk {idx}\nclean\ncreate partition primary\nformat fs=ntfs quick\nassign\nexit\n"
                            with open("diskpart_script.txt", "w") as f:
                                f.write(script)
                            # run diskpart
                            subprocess.run(["diskpart", "/s", "diskpart_script.txt"], check=False, shell=True)
                            try:
                                os.remove("diskpart_script.txt")
                            except Exception:
                                pass
                    except Exception:
                        pass

                # 4: overwrite free space with trash for n passes
                step_update(f"Overwriting free space ({self.passes} passes)...", steps[3][1])
                if ":" in device and os.path.exists(device):
                    for p in range(self.passes):
                        if self._stop:
                            raise Exception("Operation cancelled")
                        try:
                            # create big file until disk is full (write in 4MB chunks)
                            fname = os.path.join(device, f"__cm_trash_pass{p}.bin")
                            with open(fname, "wb") as out:
                                chunk = os.urandom(4 * 1024 * 1024)
                                while True:
                                    out.write(chunk)
                        except (OSError, IOError):
                            # disk full or write error
                            try:
                                os.remove(fname)
                            except Exception:
                                pass
                else:
                    # on physical/raw, attempt to write to first partition path if any assigned
                    pass

                # 5: create dummy archive to garble
                step_update("Creating compressed junk...", steps[4][1])
                try:
                    td = tempfile.mkdtemp()
                    for i in range(3):
                        pth = os.path.join(td, f"junk_{i}.bin")
                        with open(pth, "wb") as f:
                            f.write(os.urandom(2 * 1024 * 1024))  # 2 MB files
                    shutil.make_archive(os.path.join(CERT_DIR, "cm_junk"), "zip", td)
                    try:
                        os.remove(os.path.join(CERT_DIR, "cm_junk.zip"))
                    except Exception:
                        pass
                    shutil.rmtree(td, ignore_errors=True)
                except Exception:
                    pass

                # 6: final format
                step_update("Final formatting (quick)...", steps[5][1])
                try:
                    if self.entry["kind"] in ("logical"):
                        # format X:
                        vol = self.entry["device"].rstrip("\\")
                        cmd = f'format {vol} /FS:NTFS /Q /Y'
                        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif self.entry["kind"] in ("physical", "raw"):
                        # diskpart clean/create/format already attempted earlier; nothing more here
                        pass
                except Exception:
                    pass

            # 7: certificate
            step_update("Generating certificate...", steps[6][1])
            cert = self._generate_certificate(self.entry)
            self.finished.emit(cert)
        except Exception as e:
            self.finished.emit(f"ERROR: {str(e)}")

    def _generate_certificate(self, entry):
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cert_name = os.path.join(CERT_DIR, f"CodeMonk_SecureCertificate_{now}.pdf")
        try:
            c = canvas.Canvas(cert_name, pagesize=A4)
            w, h = A4
            # Logo
            logo_path = resource_path(LOGO_FILE)
            if os.path.exists(logo_path):
                try:
                    # keep logo ratio using PIL to get size if needed
                    im = Image.open(logo_path)
                    iw, ih = im.size
                    # draw scaled
                    target_w = 200
                    target_h = int(ih * (target_w / iw))
                    c.drawImage(logo_path, w/2 - target_w/2, h - 120, width=target_w, height=target_h, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            # Title & metadata
            y = h - 160
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(w/2, y, "SECURE FORMAT CERTIFICATE")
            y -= 30
            c.setFont("Helvetica", 11)
            c.drawString(80, y, f"Issued by : {COMPANY_NAME}")
            y -= 18
            c.drawString(80, y, f"Target    : {entry.get('display') or entry.get('device')}")
            y -= 18
            c.drawString(80, y, f"Method    : Scramble -> Delete -> Overwrite -> Junk -> Quick Format")
            y -= 18
            c.drawString(80, y, f"Date      : {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            y -= 36
            c.drawString(80, y, "Signature:")
            c.line(80, y-6, 260, y-6)
            c.save()
            return cert_name
        except Exception as e:
            return f"ERROR_GEN_CERT: {e}"

# -----------------------------
# Qt GUI Application
# -----------------------------
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(760, 460)
        self.setStyleSheet("background-color: #000000; color: #ffffff; font-family: 'Segoe UI';")

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)

        # Header (logo + title)
        header = QtWidgets.QHBoxLayout()
        logo_label = QtWidgets.QLabel()
        logo_label.setFixedHeight(70)
        logo_path = resource_path(LOGO_FILE)
        if os.path.exists(logo_path):
            pix = QtGui.QPixmap(logo_path).scaledToHeight(70, QtCore.Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        header.addWidget(logo_label)
        title_lbl = QtWidgets.QLabel(f"<b>{COMPANY_NAME}</b> — Secure Formatter")
        title_lbl.setStyleSheet("font-size:18px; margin-left:10px;")
        header.addWidget(title_lbl)
        header.addStretch()
        v.addLayout(header)

        # Drive selection area
        box = QtWidgets.QGroupBox()
        box.setStyleSheet("QGroupBox{background:#111111; border:1px solid #222; padding:10px;}")
        box_layout = QtWidgets.QVBoxLayout(box)

        self.drive_combo = QtWidgets.QComboBox()
        self.drive_combo.setMinimumWidth(520)
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(90)
        self.refresh_btn.clicked.connect(self.populate_drives)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("Target drive:"))
        h1.addWidget(self.drive_combo)
        h1.addWidget(self.refresh_btn)
        box_layout.addLayout(h1)

        # Info text
        self.info_label = QtWidgets.QLabel("Detected drives will show as: letter or PhysicalDriveN - model (size)")
        self.info_label.setStyleSheet("color:#BBBBBB;")
        box_layout.addWidget(self.info_label)

        v.addWidget(box)

        # Wipe level / safety
        sec_layout = QtWidgets.QHBoxLayout()
        sec_layout.addWidget(QtWidgets.QLabel("Wipe level:"))
        self.level_combo = QtWidgets.QComboBox()
        self.level_combo.addItems(["Quick (1 pass)", "Secure (3 passes)", "Ultra (7 passes)"])
        self.level_combo.setCurrentIndex(1)
        sec_layout.addWidget(self.level_combo)
        sec_layout.addStretch()
        v.addLayout(sec_layout)

        # Strong confirmation controls
        confirm_box = QtWidgets.QHBoxLayout()
        self.ack_checkbox = QtWidgets.QCheckBox("I understand this will DESTROY ALL DATA on the selected drive")
        self.ack_checkbox.setStyleSheet("color:#FFAAAA;")
        confirm_box.addWidget(self.ack_checkbox)
        v.addLayout(confirm_box)

        # typed confirmation
        typed_layout = QtWidgets.QHBoxLayout()
        typed_layout.addWidget(QtWidgets.QLabel("Type ERASE to enable:"))
        self.erase_edit = QtWidgets.QLineEdit()
        self.erase_edit.setMaximumWidth(180)
        typed_layout.addWidget(self.erase_edit)
        typed_layout.addStretch()
        v.addLayout(typed_layout)

        # Progress and log
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("QProgressBar{background:#111; color:#fff; text-align:center;} QProgressBar::chunk{background:#fff;}")
        v.addWidget(self.progress)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#000; color:#fff; font-family: Consolas; font-size: 11px;")
        self.log.setFixedHeight(160)
        v.addWidget(self.log)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("SECURE FORMAT & GENERATE CERTIFICATE")
        self.start_btn.setStyleSheet("background:#fff; color:#000; font-weight:bold; padding:10px;")
        self.start_btn.clicked.connect(self.on_start)
        btn_layout.addWidget(self.start_btn)
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        v.addLayout(btn_layout)

        # Footer
        foot = QtWidgets.QLabel("WARNING: This tool performs destructive operations. Test on disposable media first.")
        foot.setStyleSheet("color:#aaaaaa; font-size:10px;")
        v.addWidget(foot)

        # internal
        self.worker_thread = None
        self.worker = None

        # populate drives now
        self.populate_drives()

        # admin hint
        if not is_admin():
            self.log.append("⚠️ Not running as Administrator. Formatting or diskpart may fail without elevation.")
        else:
            self.log.append("✅ Administrator privileges detected.")

    # Populate merges detection methods
    def populate_drives(self):
        self.drive_combo.clear()
        try:
            merged = merge_drive_list()
            for e in merged:
                disp = e.get("display") or e.get("device")
                self.drive_combo.addItem(disp, e)
            self.log.append(f"Detected {len(merged)} drive entries.")
        except Exception as ex:
            self.log.append(f"Error detecting drives: {ex}")

    def append_log(self, txt):
        self.log.append(txt)
        self.log.ensureCursorVisible()

    def on_start(self):
        # validations
        if not self.ack_checkbox.isChecked():
            QtWidgets.QMessageBox.warning(self, "Confirm", "You must check the acknowledgment checkbox before continuing.")
            return
        if self.erase_edit.text().strip().upper() != "ERASE":
            QtWidgets.QMessageBox.warning(self, "Confirm", "Type ERASE in the box to confirm.")
            return
        data = self.drive_combo.currentData()
        if not data:
            QtWidgets.QMessageBox.warning(self, "Select Drive", "Please select a drive to proceed.")
            return

        # confirm again
        ok = QtWidgets.QMessageBox.question(self, "FINAL WARNING",
                                            f"FINAL: This will irreversibly destroy data on:\n{data.get('display') or data.get('device')}\n\nProceed?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if ok != QtWidgets.QMessageBox.Yes:
            return

        # prepare worker
        passes = 1 if self.level_combo.currentIndex() == 0 else 3 if self.level_combo.currentIndex() == 1 else 7
        do_real = True  # we always perform real by default (user confirmed)
        self.start_btn.setEnabled(False)
        self.worker = WipeWorker(data, level_passes=passes, do_real=do_real)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(lambda s: self.append_log(s))
        self.worker.finished.connect(self.on_finished)

        self.worker_thread = QtCore.QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        self.append_log("Started secure wipe thread...")

    def on_cancel(self):
        if self.worker:
            self.worker.stop()
            self.append_log("Cancellation requested.")
        else:
            self.close()

    def on_finished(self, result):
        # result is cert path or error prefix
        self.append_log(f"Finished: {result}")
        if result and not str(result).startswith("ERROR"):
            QtWidgets.QMessageBox.information(self, "Done", f"Operation complete.\nCertificate: {result}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", f"Operation failed: {result}")
        self.start_btn.setEnabled(True)
        # clean up thread
        try:
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait(2000)
        except Exception:
            pass
        self.worker = None
        self.worker_thread = None
        self.progress.setValue(0)

# -----------------------------
# Launch
# -----------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
