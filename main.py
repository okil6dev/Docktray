import sys
import os

# Handle bundled paths for PyInstaller
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.getcwd()

if base_path not in sys.path:
    sys.path.append(base_path)

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt, pyqtSlot
from src.ui.launcher_window import LauncherWindow

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    return os.path.join(base_path, relative_path)

def get_app_icon():
    icon_path = get_resource_path("icons/app/icon.ico")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    
    # Fallback placeholder
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 120, 215))
    return QIcon(pixmap)


def main():
    # Set AppUserModelID at the START - before any window creation
    # This must be here, not in settings_window, to prevent conflicts
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DockTray.Launcher.1")
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    launcher = LauncherWindow()
    
    tray_icon = QSystemTrayIcon(get_app_icon(), app)
    tray_icon.setToolTip("DockTray Launcher")
    
    # Tray menu
    menu = QMenu()
    quit_action = menu.addAction("Exit DockTray")
    quit_action.triggered.connect(app.quit)
    tray_icon.setContextMenu(menu)
    
    # Tray click event
    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if launcher.isVisible() and launcher.windowOpacity() == 1.0:
                launcher.hide_launcher()
            else:
                tray_geometry = tray_icon.geometry()
                launcher.show_launcher(tray_geometry)
                
    tray_icon.activated.connect(on_tray_activated)
    tray_icon.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
