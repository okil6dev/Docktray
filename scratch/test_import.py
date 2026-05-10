from PyQt6.QtWidgets import QApplication
try:
    from qfluentwidgets import QFluentWindow
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
