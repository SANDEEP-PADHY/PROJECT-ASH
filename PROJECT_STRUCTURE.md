# Project Structure

The Code Monk — Secure Formatter has been successfully modularized into the following files:

## Main Files

- **`main.py`** - Entry point for the application
- **`gui.py`** - Main GUI window and user interface logic
- **`secure_wipe.py`** - WipeWorker class containing secure wipe operations
- **`certificate.py`** - Certificate generation functionality
- **`drive_utils.py`** - Drive detection and enumeration utilities
- **`utils.py`** - Shared utilities, constants, and helper functions

## Legacy Files

- **`project_ash.py`** - Original monolithic file (now deprecated, kept for reference)

## Assets

- **`CODE MONK LOGO.png`** - Logo file for branding
- **`app.ico`** - Application icon

## Usage

To run the application:
```bash
python main.py
```

## Module Dependencies

- `main.py` → `gui.py`
- `gui.py` → `drive_utils.py`, `secure_wipe.py`, `utils.py`
- `secure_wipe.py` → `certificate.py`
- `certificate.py` → `utils.py`
- `drive_utils.py` → (standalone)
- `utils.py` → (standalone)

## Benefits of Modularization

1. **Separation of Concerns** - Each module has a single responsibility
2. **Maintainability** - Easier to modify specific functionality
3. **Testability** - Individual modules can be tested independently
4. **Reusability** - Components can be imported and used elsewhere
5. **Readability** - Code is organized and easier to understand

## Fixed Security Issues

1. **Enhanced File Overwriting** - Files are now completely overwritten with random data (not just first 4KB)
2. **Error Logging** - All errors are logged to UI instead of being silently ignored
3. **Certificate Generation** - Only generated if wipe completes without errors
4. **Admin Privileges** - Clear warnings when not running as administrator
