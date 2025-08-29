"""
utils.py
Shared utilities for Code Monk — Secure Formatter
"""
import os
import sys
import ctypes

# Configuration / Branding
APP_TITLE = "Code Monk — Secure Formatter"
COMPANY_NAME = "Code Monk"
LOGO_FILE = "CODE MONK LOGO.png"
CERT_DIR = "."

def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def resource_path(rel):
    """Relative path that works both as script or PyInstaller bundle"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(".")
    return os.path.join(base, rel)
