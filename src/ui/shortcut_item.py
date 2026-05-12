import os
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolButton
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QCursor, QIcon
from src.core.icon_extractor import get_icon
from .ui_utils import svg_to_icon, ICONS

class ShortcutItem(QWidget):
    deleted = pyqtSignal(str)

    def __init__(self, path, name, icon_size=45, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = name
        self.icon_size = int(icon_size)
        self._base_pixmap = None

        self._apply_geometry_from_icon_size()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 8, 5, 5)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon Container
        self.icon_container = QWidget(self)
        self.icon_container.setFixedSize(self.icon_container_size, self.icon_container_size)
        self.icon_layout = QVBoxLayout(self.icon_container)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel(self.icon_container)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(self.icon_container_size, self.icon_container_size)
        
        pixmap = get_icon(path, 'large')
        if pixmap and not pixmap.isNull():
            self._base_pixmap = pixmap
            self._apply_icon_size()
        elif path.startswith("uwp:") or path.startswith("startapp:"):
            icon = svg_to_icon(ICONS["windows_apps"], "#4fc3f7")
            fallback = icon.pixmap(self.icon_size, self.icon_size)
            if not fallback.isNull():
                self._base_pixmap = fallback
                self._apply_icon_size()
            else:
                self.icon_label.setText("UWP")
        else:
            self.icon_label.setText("?")
            
        self.layout.addWidget(self.icon_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Name
        self.name_label = QLabel(name, self)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("color: #E0E0E0;")
        
        font = self.name_label.font()
        font.setPointSize(10)
        self.name_label.setFont(font)
        self.layout.addWidget(self.name_label, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Delete Button (Overlay on icon)
        self.delete_btn = QToolButton(self)
        self.delete_btn.setIcon(svg_to_icon(ICONS["trash"], "black"))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setFixedSize(24, 24)
        # Position at top-right of the icon area
        self.delete_btn.move(self.delete_btn_x, 5)
        self.delete_btn.hide()
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 6px;
                background-color: rgba(240, 240, 240, 0.9);
            }
            QToolButton:hover {
                background-color: white;
            }
        """)
        
        # Setup hover styling
        self.setStyleSheet("""
            ShortcutItem {
                border-radius: 8px;
            }
            ShortcutItem:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)

    def _apply_geometry_from_icon_size(self):
        # Keep size relationships stable while scaling hitbox with icon size.
        self.icon_container_size = max(52, self.icon_size + 24)
        self.tile_width = max(86, self.icon_size + 56)
        self.tile_height = max(102, self.icon_size + 74)
        self.delete_btn_x = self.icon_container_size - 2
        self.setFixedSize(self.tile_width, self.tile_height)

    def _apply_icon_size(self):
        if self._base_pixmap and not self._base_pixmap.isNull():
            self.icon_label.setPixmap(
                self._base_pixmap.scaled(
                    self.icon_size,
                    self.icon_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def set_icon_size(self, size):
        self.icon_size = int(size)
        self._apply_geometry_from_icon_size()
        self.icon_container.setFixedSize(self.icon_container_size, self.icon_container_size)
        self.icon_label.setFixedSize(self.icon_container_size, self.icon_container_size)
        self.delete_btn.move(self.delete_btn_x, 5)
        self._apply_icon_size()

    def enterEvent(self, event):
        self.delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.hide()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Prevent launching if the delete button was clicked
            if not self.delete_btn.underMouse():
                self._launch_app()
        super().mouseReleaseEvent(event)

    def _launch_app(self):
        if self.path.startswith("uwp:") or self.path.startswith("startapp:"):
            app_id = self.path.split(":", 1)[1]
            if app_id:
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
            return

        if os.path.exists(self.path):
            os.startfile(self.path)

    def _on_delete_clicked(self):
        self.deleted.emit(self.path)
