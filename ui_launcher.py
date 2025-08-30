"""
ui_launcher.py
Cross-Platform UI Launcher for Project ASH Secure Formatter
Automatically detects and launches the best available GUI framework
"""
import os
import sys
import platform
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def detect_gui_frameworks():
    """Detect available GUI frameworks in order of preference"""
    frameworks = []
    
    # Test PyQt5
    try:
        import PyQt5.QtWidgets
        frameworks.append(('PyQt5', 'PyQt5'))
    except ImportError:
        pass
    
    # Test PyQt6
    try:
        import PyQt6.QtWidgets
        frameworks.append(('PyQt6', 'PyQt6'))
    except ImportError:
        pass
    
    # Test tkinter (usually available on most systems)
    try:
        import tkinter
        frameworks.append(('tkinter', 'Tkinter'))
    except ImportError:
        pass
    
    return frameworks

def launch_qt_gui():
    """Launch PyQt-based GUI"""
    try:
        from main_crossplatform import main
        return main()
    except Exception as e:
        print(f"Failed to launch Qt GUI: {e}")
        return None

def launch_tkinter_gui():
    """Launch tkinter-based GUI"""
    try:
        from ui_tkinter import TkinterMainWindow
        app = TkinterMainWindow()
        app.run()
        return 0
    except Exception as e:
        print(f"Failed to launch Tkinter GUI: {e}")
        return None

def launch_console_interface():
    """Launch console-based interface as last resort"""
    try:
        from console_interface import ConsoleInterface
        interface = ConsoleInterface()
        return interface.run()
    except Exception as e:
        print(f"Failed to launch console interface: {e}")
        return 1

def main():
    """Main launcher function"""
    print("Code Monk — Cross-Platform Secure Formatter")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Detect available frameworks
    frameworks = detect_gui_frameworks()
    
    if not frameworks:
        print("No GUI frameworks detected. Falling back to console interface...")
        return launch_console_interface()
    
    print(f"Available GUI frameworks: {', '.join([f[1] for f in frameworks])}")
    
    # Try to launch GUI in order of preference
    for framework_id, framework_name in frameworks:
        print(f"Attempting to launch {framework_name} interface...")
        
        if framework_id in ['PyQt5', 'PyQt6']:
            result = launch_qt_gui()
            if result is not None:
                return result
        elif framework_id == 'tkinter':
            result = launch_tkinter_gui()
            if result is not None:
                return result
    
    # If all GUI attempts fail, use console
    print("All GUI attempts failed. Launching console interface...")
    return launch_console_interface()

if __name__ == "__main__":
    sys.exit(main())
