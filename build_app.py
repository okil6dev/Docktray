import os
import subprocess
import sys

def build():
    print("Building DockTray Executable...")
    
    # Path to the main script
    main_script = "main.py"
    
    # PyInstaller command
    # --onefile: Bundle everything into a single exe
    # --noconsole: Don't show the command prompt when running
    # --name: Name of the exe
    # --add-data: Include the src directory
    # --clean: Clean cache before building
    # --hidden-import: Ensure PyInstaller finds all submodules
    
    # Use absolute paths to ensure PyInstaller finds everything
    icon_path = os.path.abspath("icons/app/icon.ico")
    src_path = os.path.abspath("src")
    icons_app_dir = os.path.abspath("icons/app")
    icons_projects_dir = os.path.abspath("icons/projects")
    icons_settings_dir = os.path.abspath("icons/settings_icon")
    
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=DockTray",
        f"--icon={icon_path}",
        f"--add-data={src_path};src",
        f"--add-data={icons_app_dir};icons/app",
        f"--add-data={icons_projects_dir};icons/projects",
        f"--add-data={icons_settings_dir};icons/settings_icon",
        "--hidden-import=PyQt6_Frameless_Window",
        "--hidden-import=PyQt6_Fluent_Widgets",
        "--clean",
        main_script
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    try:
        subprocess.run(command, check=True)
        print("\nBuild Successful!")
        print(f"Your executable is located in: {os.path.join(os.getcwd(), 'dist')}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild Failed: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
    build()