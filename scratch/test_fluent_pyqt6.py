try:
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    from qfluentwidgets import FluentWindow
    print("FluentWindow imported successfully with PyQt6")
except Exception as e:
    print(f"Error: {e}")
