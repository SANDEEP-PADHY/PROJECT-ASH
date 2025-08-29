# Project ASH - Cross-Platform Secure Formatter

A professional-grade secure drive formatting tool that works on both Windows and Linux systems.

## Features

- **Cross-platform compatibility**: Works on Windows and Linux
- **Multiple drive detection methods**: Logical drives, physical drives, and raw devices
- **Secure wiping**: Multi-pass overwriting (1, 3, or 7 passes)
- **Professional GUI**: Dark-themed interface with progress tracking
- **Certificate generation**: PDF certificates for compliance and audit trails
- **Safety mechanisms**: Multiple confirmation steps to prevent accidental data loss
- **Administrator detection**: Checks for proper privileges

## Installation

### Prerequisites

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip parted util-linux coreutils

# RHEL/CentOS/Fedora
sudo yum install python3-pip parted util-linux coreutils

# Arch Linux
sudo pacman -S python-pip parted util-linux coreutils
```

#### Windows
- Python 3.7 or higher
- Administrator privileges for disk operations

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode (Recommended)
```bash
python main_crossplatform.py
```

### Original Windows Version
```bash
python main.py
```

## Platform-Specific Features

### Linux
- Uses `lsblk` for drive detection
- Employs `parted`, `wipefs`, and `dd` for secure operations
- Supports ext4, NTFS, and other filesystems
- Requires root privileges for disk operations

### Windows
- Uses WMI and Windows API for drive detection
- Employs `diskpart` for low-level operations
- Supports NTFS formatting
- Requires Administrator privileges

## Security Process

1. **File Scrambling**: XOR encryption of existing files
2. **File Deletion**: Complete removal of file system entries
3. **Multi-pass Overwriting**: Random data written multiple times
4. **Partition Cleanup**: Removal of partition tables
5. **Fresh Formatting**: Creation of new file system
6. **Certificate Generation**: Proof of completion

## Safety Features

- Multiple confirmation dialogs
- Typed confirmation requirement ("ERASE")
- Final warning with drive details
- Progress tracking with cancellation support
- Comprehensive logging

## File Structure

```
project-ash/
├── main.py                 # Original Windows version
├── main_crossplatform.py   # Cross-platform version
├── linux_compat.py        # Linux compatibility layer
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Development

### Adding New Platforms
1. Extend `linux_compat.py` with platform-specific functions
2. Add drive detection methods for the new platform
3. Implement secure wipe commands
4. Update the GUI framework detection

### Testing
⚠️ **WARNING**: This tool performs irreversible data destruction. Always test on disposable media or virtual machines first.

## Legal Notice

This software is designed for legitimate data destruction purposes. Users are responsible for:
- Ensuring they have proper authorization to wipe drives
- Complying with local data protection regulations
- Following organizational security policies
- Maintaining audit trails through generated certificates

## License

This project is part of Project ASH by Code Monk. Use responsibly and at your own risk.
