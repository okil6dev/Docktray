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
    
    # Use absolute paths to ensure PyInstaller finds everything
    icon_path = os.path.abspath("icons/icon.ico")
    src_path = os.path.abspath("src")
    icons_dir = os.path.abspath("icons")
    
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=DockTray",
        f"--icon={icon_path}",
        f"--add-data={src_path};src",
        f"--add-data={icons_dir};icons",
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
