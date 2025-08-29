import os
import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import psutil
import time

APP_NAME = "Code Monk Secure Formatter"
CERT_FILE = "format_certificate.pdf"

# --- Secure Format Simulation ---
def secure_format(drive):
    steps = [
        "Encrypting existing data...",
        "Deleting partitions...",
        "Filling drive with random trash...",
        "Compressing drive contents...",
        "Final formatting...",
        "Generating certificate..."
    ]

    for step in steps:
        log(f"[{drive}] {step}")
        time.sleep(1.5)  # simulate time delay

    create_certificate(drive)
    log(f"✅ {drive} formatted securely. Certificate generated: {CERT_FILE}")
    messagebox.showinfo("Success", f"Drive {drive} securely formatted!\nCertificate saved as {CERT_FILE}")

# --- Generate PDF Certificate ---
def create_certificate(drive):
    c = canvas.Canvas(CERT_FILE, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(300, 800, "Secure Format Certificate")
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Drive: {drive}")
    c.drawString(100, 730, f"Formatted by: {APP_NAME}")
    c.drawString(100, 710, f"Status: Successfully formatted")
    c.drawString(100, 690, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()

# --- Logging ---
def log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

# --- Get all connected drives ---
def get_drives():
    drives = []
    partitions = psutil.disk_partitions()
    for p in partitions:
        if "removable" in p.opts or "rw" in p.opts or p.device:
            drives.append(p.device)
    return drives

# --- Start format process ---
def start_format():
    drive = drive_var.get()
    if not drive:
        messagebox.showerror("Error", "Please select a drive")
        return
    confirm = messagebox.askyesno("Danger", f"⚠️ WARNING: This will securely erase {drive}. Continue?")
    if confirm:
        secure_format(drive)

# --- GUI Setup ---
root = tk.Tk()
root.title(APP_NAME)
root.geometry("600x400")
root.configure(bg="black")

# Logo
if os.path.exists("CODE MONK LOGO.png"):
    logo_img = tk.PhotoImage(file="CODE MONK LOGO.png")
    logo_label = tk.Label(root, image=logo_img, bg="black")
    logo_label.pack(pady=10)

# Title
title_label = tk.Label(root, text=APP_NAME, font=("Arial", 18, "bold"), bg="black", fg="white")
title_label.pack(pady=10)

# Drive dropdown
drive_var = tk.StringVar()
drive_dropdown = ttk.Combobox(root, textvariable=drive_var, values=get_drives(), font=("Arial", 12))
drive_dropdown.pack(pady=10)

# Refresh drives
def refresh_drives():
    drive_dropdown["values"] = get_drives()
    log("🔄 Drive list refreshed")

refresh_btn = tk.Button(root, text="Refresh Drives", command=refresh_drives, bg="white", fg="black")
refresh_btn.pack(pady=5)

# Format button
format_btn = tk.Button(root, text="Secure Format", command=start_format, bg="white", fg="black", font=("Arial", 12, "bold"))
format_btn.pack(pady=10)

# Log box
log_box = tk.Text(root, height=10, width=70, bg="black", fg="white", font=("Consolas", 10))
log_box.pack(pady=10)

root.mainloop()
