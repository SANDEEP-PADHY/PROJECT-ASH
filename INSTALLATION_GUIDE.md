# Project ASH - Cross-Platform Installation Guide

## Overview
Project ASH Secure Formatter provides multiple UI options that work across Windows and Linux platforms:

1. **PyQt5/PyQt6 GUI** (Recommended) - Modern, feature-rich interface
2. **Tkinter GUI** (Fallback) - Basic but functional interface
3. **Console Interface** (Ultimate fallback) - Text-based interface

The `ui_launcher.py` automatically detects and launches the best available interface.

## Quick Start

### Windows
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Launch the application
python ui_launcher.py
```

### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip parted util-linux coreutils

# Install Python dependencies
pip3 install -r requirements.txt

# Launch the application
python3 ui_launcher.py
```

### Linux (RHEL/CentOS/Fedora)
```bash
# Install system dependencies
sudo yum install python3-pip parted util-linux coreutils
# or for newer versions:
sudo dnf install python3-pip parted util-linux coreutils

# Install Python dependencies
pip3 install -r requirements.txt

# Launch the application
python3 ui_launcher.py
```

### Linux (Arch)
```bash
# Install system dependencies
sudo pacman -S python-pip parted util-linux coreutils

# Install Python dependencies
pip install -r requirements.txt

# Launch the application
python ui_launcher.py
```

## Detailed Installation

### Prerequisites
- Python 3.7 or higher
- Administrator/root privileges (recommended)

### GUI Framework Options

#### Option 1: PyQt5 (Recommended)
```bash
pip install PyQt5>=5.15.0
```

#### Option 2: PyQt6 (Alternative)
```bash
pip install PyQt6>=6.0.0
```

#### Option 3: Tkinter (Usually pre-installed)
Tkinter comes with most Python installations. If missing:

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**RHEL/CentOS:**
```bash
sudo yum install tkinter
```

### Platform-Specific Dependencies

#### Windows
```powershell
pip install pywin32>=300 wmi>=1.5.1
```

#### Linux
System utilities (required for secure operations):
```bash
# Ubuntu/Debian
sudo apt install parted util-linux coreutils

# RHEL/CentOS
sudo yum install parted util-linux coreutils

# Arch
sudo pacman -S parted util-linux coreutils
```

## Usage

### Launching the Application

#### Automatic Detection (Recommended)
```bash
python ui_launcher.py
```
This will automatically detect and launch the best available interface.

#### Manual Interface Selection

**PyQt Interface:**
```bash
python main_crossplatform.py
```

**Tkinter Interface:**
```bash
python -c "from ui_tkinter import TkinterMainWindow; TkinterMainWindow().run()"
```

**Console Interface:**
```bash
python console_interface.py
```

### Running with Elevated Privileges

#### Windows
Run Command Prompt or PowerShell as Administrator:
```powershell
# Right-click Command Prompt -> "Run as administrator"
python ui_launcher.py
```

#### Linux
```bash
sudo python3 ui_launcher.py
```

## Troubleshooting

### Common Issues

#### "No GUI frameworks detected"
**Solution:** Install PyQt5 or ensure tkinter is available:
```bash
pip install PyQt5
```

#### "Not running as admin/root"
**Solution:** Run with elevated privileges (see above)

#### Linux: "Command not found: parted"
**Solution:** Install system utilities:
```bash
sudo apt install parted util-linux coreutils
```

#### Import errors on Linux
**Solution:** Use python3 explicitly:
```bash
python3 ui_launcher.py
```

### Minimal Installation (Console Only)
If you only need the console interface:
```bash
pip install reportlab>=3.6.0 Pillow>=8.0.0 psutil>=5.8.0
python console_interface.py
```

## Features by Interface

| Feature | PyQt GUI | Tkinter GUI | Console |
|---------|----------|-------------|---------|
| Drive Detection | ✅ | ✅ | ✅ |
| Progress Bar | ✅ | ✅ | ✅ |
| Real-time Logs | ✅ | ✅ | ✅ |
| Dark Theme | ✅ | ✅ | N/A |
| Certificate Generation | ✅ | ✅ | ✅ |
| Cross-platform | ✅ | ✅ | ✅ |
| No Dependencies | ❌ | ⚠️ | ✅ |

## Security Notes

⚠️ **WARNING:** This software performs destructive operations on storage devices.

- Always run with appropriate privileges
- Test on disposable media first
- Verify target drive selection carefully
- Operations cannot be undone

## Support

For issues or questions:
1. Check this installation guide
2. Verify all dependencies are installed
3. Try different interface options
4. Run with elevated privileges

The application will automatically fall back to simpler interfaces if advanced ones are unavailable.
