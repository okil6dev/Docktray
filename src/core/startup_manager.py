import os
import sys
import win32com.client

class StartupManager:
    @staticmethod
    def get_startup_folder():
        return os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')

    @staticmethod
    def get_shortcut_path():
        return os.path.join(StartupManager.get_startup_folder(), "DockTray.lnk")

    @staticmethod
    def is_startup_enabled():
        return os.path.exists(StartupManager.get_shortcut_path())

    @staticmethod
    def set_startup(enabled):
        shortcut_path = StartupManager.get_shortcut_path()
        if enabled:
            if not os.path.exists(shortcut_path):
                try:
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut = shell.CreateShortCut(shortcut_path)
                    
                    # If running as script, use sys.executable and main.py path
                    # If running as exe (PyInstaller), sys.executable is the exe
                    if hasattr(sys, '_MEIPASS'):
                        target = sys.executable
                        shortcut.TargetPath = target
                        shortcut.WorkingDirectory = os.path.dirname(target)
                    else:
                        target = sys.executable
                        script = os.path.abspath(sys.argv[0])
                        shortcut.TargetPath = target
                        shortcut.Arguments = f'"{script}"'
                        shortcut.WorkingDirectory = os.getcwd()
                    
                    shortcut.IconLocation = target
                    shortcut.save()
                    return True
                except Exception as e:
                    print(f"Error creating startup shortcut: {e}")
                    return False
        else:
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                    return True
                except Exception as e:
                    print(f"Error removing startup shortcut: {e}")
                    return False
        return True
