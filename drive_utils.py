"""
drive_utils.py
Drive detection and merging logic for Code Monk — Secure Formatter
"""
import os
import string
import ctypes
import wmi

def detect_logical_drives():
    drives = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drive = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive))
            drives.append({
                "kind": "logical",
                "device": drive,
                "drive_type": drive_type,
                "label": drive
            })
    return drives

def detect_wmi_drives():
    drives = []
    try:
        c = wmi.WMI()
        for disk in c.Win32_DiskDrive():
            size_gb = int(disk.Size) // (1024**3) if disk.Size else None
            model = disk.Caption or disk.Model or "Physical Disk"
            dev = disk.DeviceID
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
    found = []
    for i in range(max_drives):
        path = f"\\\\.\\PhysicalDrive{i}"
        try:
            handle = os.open(path, os.O_RDONLY | os.O_BINARY)
            os.close(handle)
            found.append({"kind":"raw", "device": path, "index": i})
        except Exception:
            pass
    return found

def merge_drive_list():
    logical = detect_logical_drives()
    wmi_list = detect_wmi_drives()
    raw = detect_raw_physical()
    merged = []
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
    try:
        c = wmi.WMI()
        for ld in logical:
            drive = ld["device"]
            display = f"{drive} - Logical Drive"
            mapped = False
            try:
                for disk in c.Win32_DiskDrive():
                    for part in disk.associators("Win32_DiskDriveToDiskPartition"):
                        for logical_disk in part.associators("Win32_LogicalDiskToPartition"):
                            if getattr(logical_disk, "DeviceID", "").upper() == drive.strip("\\").upper():
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
                merged.append({
                    "id": f"logical-{drive}",
                    "display": display,
                    "device": drive,
                    "kind": "logical",
                    "model": None,
                    "size_gb": None
                })
    except Exception:
        for ld in logical:
            merged.append({
                "id": f"logical-{ld['device']}",
                "display": f"{ld['device']} - Logical Drive",
                "device": ld['device'],
                "kind": "logical"
            })
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
    return merged
