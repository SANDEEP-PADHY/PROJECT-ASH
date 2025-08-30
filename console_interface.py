"""
console_interface.py
Console-based interface for Project ASH Secure Formatter
Ultimate fallback when no GUI frameworks are available
"""
import os
import sys
import datetime
import threading
import time
from pathlib import Path

# Import compatibility layer
from linux_compat import is_admin, detect_drives, get_wipe_commands, execute_secure_command
from main_crossplatform import SecureWipeWorker

class ConsoleInterface:
    """Console-based interface for the secure formatter"""
    
    def __init__(self):
        self.worker = None
        self.worker_thread = None
        
    def print_header(self):
        """Print application header"""
        print("\n" + "=" * 60)
        print("CODE MONK — CROSS-PLATFORM SECURE FORMATTER")
        print("=" * 60)
        print(f"Platform: {os.name} ({sys.platform})")
        
        if is_admin():
            print("✅ Running with administrator/root privileges")
        else:
            print("⚠️  Not running as admin/root - some operations may fail")
        print()
    
    def list_drives(self):
        """List available drives"""
        try:
            drives = detect_drives()
            if not drives:
                print("No drives detected!")
                return []
            
            print("Available drives:")
            print("-" * 50)
            for i, drive in enumerate(drives, 1):
                display = drive.get('display', drive.get('device'))
                print(f"{i:2d}. {display}")
            print()
            return drives
        except Exception as e:
            print(f"Error detecting drives: {e}")
            return []
    
    def get_user_choice(self, prompt, max_choice):
        """Get user choice with validation"""
        while True:
            try:
                choice = input(prompt).strip()
                if choice.lower() in ['q', 'quit', 'exit']:
                    return None
                choice_num = int(choice)
                if 1 <= choice_num <= max_choice:
                    return choice_num - 1
                else:
                    print(f"Please enter a number between 1 and {max_choice}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nOperation cancelled by user")
                return None
    
    def get_security_level(self):
        """Get security level from user"""
        print("Security Levels:")
        print("1. Quick (1 pass)")
        print("2. Secure (3 passes)")
        print("3. Ultra (7 passes)")
        print()
        
        choice = self.get_user_choice("Select security level (1-3): ", 3)
        if choice is None:
            return None
        
        return [1, 3, 7][choice]
    
    def confirm_operation(self, drive_info):
        """Get user confirmation for the destructive operation"""
        print("\n" + "!" * 60)
        print("CRITICAL WARNING - DATA DESTRUCTION")
        print("!" * 60)
        print(f"Target: {drive_info.get('display', drive_info.get('device'))}")
        print("\nThis operation will:")
        print("• PERMANENTLY DESTROY ALL DATA on the selected drive")
        print("• CANNOT be undone or recovered")
        print("• May take several hours to complete")
        print("\n" + "!" * 60)
        
        # First confirmation
        response1 = input("\nDo you understand this will destroy all data? (yes/no): ").strip().lower()
        if response1 != 'yes':
            return False
        
        # Second confirmation
        response2 = input("Type 'DESTROY' to confirm: ").strip()
        if response2 != 'DESTROY':
            return False
        
        # Final confirmation
        print(f"\nFINAL WARNING: About to wipe {drive_info.get('display', drive_info.get('device'))}")
        response3 = input("Type 'CONFIRM' to proceed: ").strip()
        return response3 == 'CONFIRM'
    
    def progress_callback(self, percent):
        """Progress callback for console display"""
        bar_length = 50
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f"\rProgress: |{bar}| {percent:3d}%", end='', flush=True)
        if percent == 100:
            print()  # New line when complete
    
    def status_callback(self, message):
        """Status callback for console display"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {message}")
    
    def run_secure_wipe(self, drive_info, passes):
        """Run the secure wipe operation"""
        print(f"\nStarting secure wipe with {passes} passes...")
        print("Press Ctrl+C to cancel (may take time to respond)\n")
        
        self.worker = SecureWipeWorker(
            drive_info, passes,
            progress_callback=self.progress_callback,
            status_callback=self.status_callback
        )
        
        try:
            result = self.worker.run()
            
            print("\n" + "=" * 60)
            if result.startswith("ERROR"):
                print(f"OPERATION FAILED: {result}")
                return False
            else:
                print("OPERATION COMPLETED SUCCESSFULLY!")
                print(f"Certificate saved: {result}")
                return True
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            if self.worker:
                self.worker.stop()
            return False
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return False
    
    def run(self):
        """Main console interface loop"""
        self.print_header()
        
        try:
            while True:
                # List drives
                drives = self.list_drives()
                if not drives:
                    print("No drives available. Exiting.")
                    return 1
                
                # Get drive selection
                choice = self.get_user_choice("Select drive to wipe (or 'q' to quit): ", len(drives))
                if choice is None:
                    print("Exiting...")
                    return 0
                
                selected_drive = drives[choice]
                
                # Get security level
                passes = self.get_security_level()
                if passes is None:
                    continue
                
                # Confirm operation
                if not self.confirm_operation(selected_drive):
                    print("Operation cancelled.")
                    continue
                
                # Run the wipe
                success = self.run_secure_wipe(selected_drive, passes)
                
                # Ask if user wants to continue
                if success:
                    response = input("\nWipe another drive? (y/n): ").strip().lower()
                    if response != 'y':
                        break
                else:
                    response = input("\nTry again? (y/n): ").strip().lower()
                    if response != 'y':
                        break
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            return 0
        except Exception as e:
            print(f"\nFatal error: {e}")
            return 1

def main():
    """Main entry point for console interface"""
    interface = ConsoleInterface()
    return interface.run()

if __name__ == "__main__":
    sys.exit(main())
