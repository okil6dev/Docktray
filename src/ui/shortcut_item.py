import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolButton
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QCursor, QIcon
from src.core.icon_extractor import get_icon
from .ui_utils import svg_to_icon, ICONS

class ShortcutItem(QWidget):
    deleted = pyqtSignal(str)

    def __init__(self, path, name, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = name
        
        self.setFixedSize(100, 120)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 8, 5, 5)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon Container
        self.icon_container = QWidget(self)
        self.icon_container.setFixedSize(70, 70)
        self.icon_layout = QVBoxLayout(self.icon_container)
        self.icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel(self.icon_container)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(70, 70)
        
        pixmap = get_icon(path, 'large')
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
        self.delete_btn.move(70, 5)
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
        if os.path.exists(self.path):
            os.startfile(self.path)

    def _on_delete_clicked(self):
        self.deleted.emit(self.path)
