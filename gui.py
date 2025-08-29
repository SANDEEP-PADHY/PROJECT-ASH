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
        self.resize(900, 620)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin: 8px 0px;
                padding: 15px 5px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #2a2a2a;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #333333;
            }
            QComboBox {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #777777;
                background-color: #3a3a3a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #cccccc;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                selection-background-color: #555555;
                outline: none;
            }
            QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 8px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #777777;
                background-color: #3a3a3a;
            }
            QCheckBox {
                color: #ffaaaa;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #555555;
                background-color: #333333;
            }
            QCheckBox::indicator:checked {
                background-color: #ff6b6b;
                border-color: #ff6b6b;
            }
            QCheckBox::indicator:hover {
                border-color: #777777;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #cccccc;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                line-height: 1.4;
            }
            QProgressBar {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 5px;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(15)

        # Header (logo + title)
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(15)
        
        # Logo container with background
        logo_container = QtWidgets.QFrame()
        logo_container.setFixedSize(90, 90)
        logo_container.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 2px solid #555555;
                border-radius: 45px;
            }
        """)
        logo_layout = QtWidgets.QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(10, 10, 10, 10)
        
        logo_label = QtWidgets.QLabel()
        logo_label.setAlignment(QtCore.Qt.AlignCenter)
        logo_path = resource_path(LOGO_FILE)
        if os.path.exists(logo_path):
            pix = QtGui.QPixmap(logo_path).scaledToHeight(60, QtCore.Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            # Fallback text logo
            logo_label.setText("CM")
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        logo_layout.addWidget(logo_label)
        
        header.addWidget(logo_container)
        
        # Title and subtitle
        title_container = QtWidgets.QVBoxLayout()
        title_lbl = QtWidgets.QLabel(f"<b>{COMPANY_NAME}</b>")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff; margin: 0;")
        subtitle_lbl = QtWidgets.QLabel("Secure Drive Formatter & Certificate Generator")
        subtitle_lbl.setStyleSheet("font-size: 14px; color: #cccccc; margin: 0;")
        title_container.addWidget(title_lbl)
        title_container.addWidget(subtitle_lbl)
        title_container.addStretch()
        
        header.addLayout(title_container)
        header.addStretch()
        
        # Version info
        version_lbl = QtWidgets.QLabel("v2.0")
        version_lbl.setStyleSheet("font-size: 11px; color: #888888; font-weight: bold;")
        version_lbl.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        header.addWidget(version_lbl)
        
        v.addLayout(header)

        # Drive selection area
        drive_group = QtWidgets.QGroupBox("🔧 Target Drive Selection")
        drive_group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        drive_layout = QtWidgets.QVBoxLayout(drive_group)
        drive_layout.setSpacing(12)

        # Drive selection row
        drive_row = QtWidgets.QHBoxLayout()
        drive_row.setSpacing(10)
        
        drive_label = QtWidgets.QLabel("Select Target:")
        drive_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11pt;")
        drive_label.setMinimumWidth(100)
        
        self.drive_combo = QtWidgets.QComboBox()
        self.drive_combo.setMinimumWidth(400)
        self.drive_combo.setMinimumHeight(35)
        
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        self.refresh_btn.setFixedWidth(100)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.refresh_btn.clicked.connect(self.populate_drives)
        
        drive_row.addWidget(drive_label)
        drive_row.addWidget(self.drive_combo)
        drive_row.addWidget(self.refresh_btn)
        drive_layout.addLayout(drive_row)

        # Info text
        self.info_label = QtWidgets.QLabel("💡 Detected drives will show as: Drive Letter or PhysicalDriveN - Model (Size)")
        self.info_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-style: italic;")
        self.info_label.setWordWrap(True)
        drive_layout.addWidget(self.info_label)

        v.addWidget(drive_group)

        # Security & Wipe settings
        security_group = QtWidgets.QGroupBox("⚙️ Security Configuration")
        security_group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        security_layout = QtWidgets.QVBoxLayout(security_group)
        security_layout.setSpacing(15)

        # Wipe level selection
        wipe_row = QtWidgets.QHBoxLayout()
        wipe_row.setSpacing(10)
        
        wipe_label = QtWidgets.QLabel("Wipe Level:")
        wipe_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11pt;")
        wipe_label.setMinimumWidth(100)
        
        self.level_combo = QtWidgets.QComboBox()
        self.level_combo.setMinimumHeight(35)
        self.level_combo.addItems([
            "🚀 Quick (1 pass) - Fast but less secure",
            "🛡️ Secure (3 passes) - Recommended balance",
            "🔒 Ultra (7 passes) - Maximum security, slower"
        ])
        self.level_combo.setCurrentIndex(1)
        
        wipe_row.addWidget(wipe_label)
        wipe_row.addWidget(self.level_combo)
        wipe_row.addStretch()
        security_layout.addLayout(wipe_row)

        # Warning section
        warning_frame = QtWidgets.QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: #3d1a1a;
                border: 2px solid #ff6b6b;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        warning_layout = QtWidgets.QVBoxLayout(warning_frame)
        warning_layout.setSpacing(8)
        
        warning_title = QtWidgets.QLabel("⚠️ CRITICAL WARNING")
        warning_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #ff6b6b;")
        warning_layout.addWidget(warning_title)
        
        self.ack_checkbox = QtWidgets.QCheckBox("I understand this will PERMANENTLY DESTROY ALL DATA on the selected drive")
        self.ack_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ffaaaa;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        warning_layout.addWidget(self.ack_checkbox)

        # Confirmation input
        confirm_row = QtWidgets.QHBoxLayout()
        confirm_row.setSpacing(10)
        
        confirm_label = QtWidgets.QLabel("Type 'ERASE' to enable:")
        confirm_label.setStyleSheet("font-weight: bold; color: #ff6b6b; font-size: 11pt;")
        
        self.erase_edit = QtWidgets.QLineEdit()
        self.erase_edit.setPlaceholderText("Type ERASE here...")
        self.erase_edit.setMaximumWidth(200)
        self.erase_edit.setMinimumHeight(30)
        self.erase_edit.setStyleSheet("""
            QLineEdit {
                font-weight: bold;
                font-size: 11pt;
                background-color: #2a1a1a;
                border: 2px solid #ff6b6b;
                color: #ffffff;
            }
            QLineEdit:focus {
                background-color: #3a2a2a;
            }
        """)
        
        confirm_row.addWidget(confirm_label)
        confirm_row.addWidget(self.erase_edit)
        confirm_row.addStretch()
        warning_layout.addLayout(confirm_row)
        
        security_layout.addWidget(warning_frame)
        v.addWidget(security_group)

        # Progress and log section
        progress_group = QtWidgets.QGroupBox("📊 Operation Progress & Log")
        progress_group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        progress_layout = QtWidgets.QVBoxLayout(progress_group)
        progress_layout.setSpacing(10)

        # Progress bar with label
        progress_container = QtWidgets.QVBoxLayout()
        progress_label = QtWidgets.QLabel("Progress:")
        progress_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 10pt;")
        
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setMinimumHeight(30)
        
        progress_container.addWidget(progress_label)
        progress_container.addWidget(self.progress)
        progress_layout.addLayout(progress_container)

        # Log area
        log_label = QtWidgets.QLabel("Activity Log:")
        log_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 10pt;")
        progress_layout.addWidget(log_label)
        
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setMaximumHeight(180)
        progress_layout.addWidget(self.log)
        
        v.addWidget(progress_group)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_btn = QtWidgets.QPushButton("🚀 START SECURE FORMAT & GENERATE CERTIFICATE")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:1 #cc0000);
                color: white;
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #ff6666;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6666, stop:1 #ff0000);
                border-color: #ff8888;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #cc0000, stop:1 #aa0000);
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
                border-color: #666666;
            }
        """)
        self.start_btn.clicked.connect(self.on_start)
        
        self.cancel_btn = QtWidgets.QPushButton("❌ Cancel / Exit")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setFixedWidth(150)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #888888;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #777777;
                border-color: #aaaaaa;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        v.addLayout(button_layout)

        # Footer with enhanced warning
        footer_frame = QtWidgets.QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        footer_layout = QtWidgets.QVBoxLayout(footer_frame)
        footer_layout.setSpacing(4)
        
        footer_warning = QtWidgets.QLabel("⚠️ WARNING: This tool performs destructive operations that cannot be undone!")
        footer_warning.setStyleSheet("color: #ffaa00; font-size: 10pt; font-weight: bold;")
        footer_warning.setAlignment(QtCore.Qt.AlignCenter)
        
        footer_advice = QtWidgets.QLabel("Always test on disposable media first • Ensure important data is backed up • Run as Administrator")
        footer_advice.setStyleSheet("color: #cccccc; font-size: 9pt;")
        footer_advice.setAlignment(QtCore.Qt.AlignCenter)
        
        footer_layout.addWidget(footer_warning)
        footer_layout.addWidget(footer_advice)
        v.addWidget(footer_frame)

        # internal
        self.worker_thread = None
        self.worker = None

        # populate drives now
        self.populate_drives()

        # admin hint
        if not is_admin():
            self.log.append("⚠️  Not running as Administrator. Some operations may fail without elevation.")
            self.log.append("💡  Right-click the executable and select 'Run as administrator' for full functionality.")
        else:
            self.log.append("✅  Administrator privileges detected - All operations available.")
        
        self.log.append("🔧  Application initialized successfully.")
        self.log.append("📝  Select a target drive and configure security settings to begin.")

    def populate_drives(self):
        self.drive_combo.clear()
        self.log.append("🔍  Scanning for available drives...")
        try:
            merged = merge_drive_list()
            for e in merged:
                disp = e.get("display") or e.get("device")
                self.drive_combo.addItem(disp, e)
            self.log.append(f"✅  Detected {len(merged)} drive entries successfully.")
            if len(merged) == 0:
                self.log.append("⚠️   No drives detected. Try running as Administrator or check connections.")
        except Exception as ex:
            self.log.append(f"❌  Error detecting drives: {ex}")
            self.log.append("💡  Try refreshing or running as Administrator.")

    def append_log(self, txt):
        self.log.append(txt)
        self.log.ensureCursorVisible()

    def on_start(self):
        # validations
        if not self.ack_checkbox.isChecked():
            QtWidgets.QMessageBox.warning(self, "⚠️ Confirmation Required", 
                "You must check the acknowledgment checkbox before continuing.\n\nThis confirms you understand the destructive nature of this operation.")
            return
        if self.erase_edit.text().strip().upper() != "ERASE":
            QtWidgets.QMessageBox.warning(self, "⚠️ Confirmation Required", 
                "Please type 'ERASE' (without quotes) in the confirmation box.\n\nThis is a safety measure to prevent accidental data destruction.")
            return
        data = self.drive_combo.currentData()
        if not data:
            QtWidgets.QMessageBox.warning(self, "❌ No Drive Selected", 
                "Please select a target drive from the dropdown list before proceeding.")
            return

        # Final confirmation with enhanced dialog
        target_info = data.get('display') or data.get('device')
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("🚨 FINAL WARNING - POINT OF NO RETURN")
        msg_box.setText("CRITICAL: This operation will PERMANENTLY DESTROY ALL DATA")
        msg_box.setInformativeText(f"Target Drive: {target_info}\n\nThis action CANNOT be undone!\nAll files, partitions, and data will be irrecoverably erased.\n\nAre you absolutely certain you want to proceed?")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.No)
        
        # Style the message box
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QMessageBox QPushButton:hover {
                background-color: #505050;
            }
        """)
        
        if msg_box.exec_() != QtWidgets.QMessageBox.Yes:
            self.log.append("🛑  Operation cancelled by user.")
            return

        # prepare worker
        passes = 1 if self.level_combo.currentIndex() == 0 else 3 if self.level_combo.currentIndex() == 1 else 7
        do_real = True
        self.start_btn.setEnabled(False)
        self.start_btn.setText("🔄 OPERATION IN PROGRESS...")
        
        self.log.append("🚀  Starting secure wipe operation...")
        self.log.append(f"📋  Target: {target_info}")
        self.log.append(f"🔒  Security Level: {passes} passes")
        
        self.worker = WipeWorker(data, level_passes=passes, do_real=do_real)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(lambda s: self.append_log(f"⚙️  {s}"))
        self.worker.finished.connect(self.on_finished)

        self.worker_thread = QtCore.QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def on_cancel(self):
        if self.worker:
            self.worker.stop()
            self.log.append("🛑  Cancellation requested - stopping operation...")
        else:
            self.close()

    def on_finished(self, result):
        # result is cert path or error prefix
        self.log.append(f"🏁  Operation completed: {result}")
        
        # Reset button
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 START SECURE FORMAT & GENERATE CERTIFICATE")
        
        if result and not str(result).startswith("ERROR"):
            # Success
            success_msg = QtWidgets.QMessageBox()
            success_msg.setIcon(QtWidgets.QMessageBox.Information)
            success_msg.setWindowTitle("✅ Operation Successful")
            success_msg.setText("Secure Format Complete!")
            success_msg.setInformativeText(f"The drive has been securely wiped and formatted.\n\nCertificate generated:\n{result}")
            success_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2a2a2a;
                    color: white;
                }
                QMessageBox QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #45a049;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 60px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            success_msg.exec_()
            self.log.append("✅  Certificate generated successfully.")
        else:
            # Error
            error_msg = QtWidgets.QMessageBox()
            error_msg.setIcon(QtWidgets.QMessageBox.Critical)
            error_msg.setWindowTitle("❌ Operation Failed")
            error_msg.setText("Secure Format Failed")
            error_msg.setInformativeText(f"The operation encountered errors:\n\n{result}")
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: #2a2a2a;
                    color: white;
                }
                QMessageBox QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: 1px solid #cc0000;
                    border-radius: 4px;
                    padding: 6px 12px;
                    min-width: 60px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #ff6666;
                }
            """)
            error_msg.exec_()
            self.log.append("❌  Operation failed - check log for details.")
            
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
