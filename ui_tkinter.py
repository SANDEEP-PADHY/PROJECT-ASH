"""
ui_tkinter.py
Tkinter-based GUI for Project ASH Secure Formatter
Cross-platform fallback interface using tkinter
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import datetime
import platform
from pathlib import Path

# Import compatibility layer
from linux_compat import is_admin, detect_drives, get_wipe_commands, execute_secure_command
from main_crossplatform import SecureWipeWorker

class TkinterMainWindow:
    """Tkinter-based main window for cross-platform compatibility"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_ui()
        self.worker_thread = None
        self.worker = None
        self.populate_drives()
        
    def setup_window(self):
        """Configure main window"""
        self.root.title("Code Monk — Cross-Platform Secure Formatter")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme configuration
        style.configure('Dark.TFrame', background='#2b2b2b')
        style.configure('Dark.TLabel', background='#2b2b2b', foreground='white')
        style.configure('Dark.TButton', background='#404040', foreground='white')
        style.configure('Dark.TCombobox', fieldbackground='#404040', foreground='white')
        style.configure('Dark.TCheckbutton', background='#2b2b2b', foreground='#ffaaaa')
        style.configure('Dark.TEntry', fieldbackground='#404040', foreground='white')
        
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, 
                               text="Code Monk — Cross-Platform Secure Formatter",
                               font=('Arial', 16, 'bold'),
                               style='Dark.TLabel')
        title_label.pack()
        
        platform_label = ttk.Label(header_frame,
                                  text=f"Platform: {platform.system()} {platform.release()}",
                                  font=('Arial', 10),
                                  style='Dark.TLabel')
        platform_label.pack()
        
        # Drive selection
        drive_frame = ttk.LabelFrame(main_frame, text="Drive Selection", style='Dark.TFrame')
        drive_frame.pack(fill=tk.X, pady=(0, 10))
        
        drive_row = ttk.Frame(drive_frame, style='Dark.TFrame')
        drive_row.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(drive_row, text="Target Drive:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(drive_row, textvariable=self.drive_var, 
                                       state="readonly", width=50, style='Dark.TCombobox')
        self.drive_combo.pack(side=tk.LEFT, padx=(10, 5))
        
        self.refresh_btn = ttk.Button(drive_row, text="Refresh", 
                                     command=self.populate_drives, style='Dark.TButton')
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # Wipe settings
        settings_frame = ttk.LabelFrame(main_frame, text="Wipe Settings", style='Dark.TFrame')
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        settings_row = ttk.Frame(settings_frame, style='Dark.TFrame')
        settings_row.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(settings_row, text="Security Level:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.level_var = tk.StringVar(value="Secure (3 passes)")
        self.level_combo = ttk.Combobox(settings_row, textvariable=self.level_var,
                                       values=["Quick (1 pass)", "Secure (3 passes)", "Ultra (7 passes)"],
                                       state="readonly", style='Dark.TCombobox')
        self.level_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Safety confirmations
        safety_frame = ttk.LabelFrame(main_frame, text="Safety Confirmations", style='Dark.TFrame')
        safety_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.ack_var = tk.BooleanVar()
        self.ack_checkbox = ttk.Checkbutton(safety_frame, 
                                           text="I understand this will PERMANENTLY DESTROY ALL DATA",
                                           variable=self.ack_var, style='Dark.TCheckbutton')
        self.ack_checkbox.pack(anchor=tk.W, padx=10, pady=5)
        
        confirm_row = ttk.Frame(safety_frame, style='Dark.TFrame')
        confirm_row.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(confirm_row, text="Type 'ERASE' to confirm:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.confirm_var = tk.StringVar()
        self.confirm_entry = ttk.Entry(confirm_row, textvariable=self.confirm_var, 
                                      width=15, style='Dark.TEntry')
        self.confirm_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress
        progress_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log", style='Dark.TFrame')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                 bg='#1e1e1e', fg='white',
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="START SECURE WIPE",
                                   command=self.start_wipe, style='Dark.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel",
                                    command=self.cancel_operation, style='Dark.TButton')
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Admin check
        if is_admin():
            self.log("✅ Running with administrator/root privileges")
        else:
            self.log("⚠️ Not running as admin/root - some operations may fail")
    
    def populate_drives(self):
        """Populate the drive combo box"""
        try:
            drives = detect_drives()
            self.drives_data = {}
            drive_options = []
            
            for drive in drives:
                display = drive.get('display', drive.get('device'))
                drive_options.append(display)
                self.drives_data[display] = drive
            
            self.drive_combo['values'] = drive_options
            if drive_options:
                self.drive_combo.current(0)
            
            self.log(f"Detected {len(drives)} drives")
        except Exception as e:
            self.log(f"Error detecting drives: {e}")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_wipe(self):
        """Start the secure wipe process"""
        # Validation
        if not self.ack_var.get():
            messagebox.showwarning("Confirmation Required", 
                                 "You must acknowledge the data destruction warning.")
            return
        
        if self.confirm_var.get().upper() != "ERASE":
            messagebox.showwarning("Confirmation Required",
                                 "Type 'ERASE' in the confirmation field.")
            return
        
        selected_drive = self.drive_var.get()
        if not selected_drive or selected_drive not in self.drives_data:
            messagebox.showwarning("No Drive Selected",
                                 "Please select a drive to wipe.")
            return
        
        drive_data = self.drives_data[selected_drive]
        
        # Final confirmation
        result = messagebox.askyesno("FINAL WARNING",
                                   f"This will PERMANENTLY DESTROY all data on:\n\n{selected_drive}\n\n"
                                   f"This action CANNOT be undone!\n\nProceed?")
        
        if not result:
            return
        
        # Start worker thread
        level_text = self.level_var.get()
        if "1 pass" in level_text:
            passes = 1
        elif "7 passes" in level_text:
            passes = 7
        else:
            passes = 3
        
        self.worker = SecureWipeWorker(
            drive_data, passes,
            progress_callback=self.update_progress,
            status_callback=self.log
        )
        
        self.worker_thread = threading.Thread(target=self.run_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        self.start_btn.configure(state='disabled')
        self.log("Secure wipe operation started...")
    
    def run_worker(self):
        """Run worker in thread"""
        result = self.worker.run()
        
        # Update UI in main thread
        self.root.after(0, lambda: self.wipe_finished(result))
    
    def update_progress(self, percent):
        """Update progress bar"""
        self.progress_var.set(percent)
        self.root.update_idletasks()
    
    def wipe_finished(self, result):
        """Handle wipe completion"""
        self.start_btn.configure(state='normal')
        
        if result.startswith("ERROR"):
            messagebox.showerror("Operation Failed", result)
            self.log(f"Operation failed: {result}")
        else:
            messagebox.showinfo("Operation Complete", 
                              f"Secure wipe completed successfully!\n\nCertificate saved: {result}")
            self.log(f"Operation completed. Certificate: {result}")
        
        self.progress_var.set(0)
    
    def cancel_operation(self):
        """Cancel the current operation"""
        if self.worker:
            self.worker.stop()
            self.log("Cancellation requested...")
        else:
            self.root.quit()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
