"""
gui.py
GUI components for Code Monk — Secure Formatter
"""
import os
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from drive_utils import merge_drive_list
from secure_wipe import WipeWorker
from utils import APP_TITLE, COMPANY_NAME, LOGO_FILE, is_admin, resource_path

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
