import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QToolButton,
    QMenu, QInputDialog, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint
from PyQt6.QtGui import QCursor, QIcon, QPixmap
from src.core.icon_extractor import get_icon
from .ui_utils import svg_to_icon, ICONS


def _load_icon_from_file(path):
    """Load a QPixmap from any image file (.png, .ico, .jpg, .bmp, ...)."""
    pix = QPixmap(path)
    if pix.isNull():
        # Fallback: try via QIcon for .ico files with multiple sizes
        icon = QIcon(path)
        if not icon.isNull():
            available = icon.availableSizes()
            if available:
                pix = icon.pixmap(available[-1])
            else:
                pix = icon.pixmap(256, 256)
    return pix


class ShortcutItem(QWidget):
    deleted = pyqtSignal(str)
    # Emitted when custom icon / name changes; payload is the shortcut path.
    customDataChanged = pyqtSignal(str)

    def __init__(self, path, name, icon_size=45,
                 custom_icon=None, custom_name=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = name
        self.custom_icon_path = custom_icon
        self.custom_name = custom_name
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

        self._load_icon()

        self.layout.addWidget(self.icon_container, 0, Qt.AlignmentFlag.AlignCenter)

        # Name
        self.name_label = QLabel(self._display_name(), self)
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

        # Custom-icon indicator (small badge in the bottom-right when set)
        self.custom_badge = QLabel(self)
        self.custom_badge.setFixedSize(16, 16)
        self.custom_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.custom_badge.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(79, 195, 247, 200);
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self.custom_badge.setText("C")
        self.custom_badge.hide()

        # Setup hover styling
        self.setStyleSheet("""
            ShortcutItem {
                border-radius: 8px;
            }
            ShortcutItem:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
        """)

        self._refresh_custom_badge()

    # ------------------------------------------------------------------ icon

    def _load_icon(self):
        """Load the icon: custom file > extracted > fallback."""
        # Reset the label so fallback text doesn't linger.
        self.icon_label.setText("")

        if self.custom_icon_path and os.path.exists(self.custom_icon_path):
            pix = _load_icon_from_file(self.custom_icon_path)
            if pix and not pix.isNull():
                self._base_pixmap = pix
                self._apply_icon_size()
                return

        # Website shortcuts always use the built-in globe icon.
        if self.path.startswith("url:"):
            icon = svg_to_icon(ICONS["website"], "#4fc3f7")
            fallback = icon.pixmap(self.icon_size, self.icon_size)
            if not fallback.isNull():
                self._base_pixmap = fallback
                self._apply_icon_size()
            else:
                self.icon_label.setText("WWW")
            return

        pixmap = get_icon(self.path, 'large')
        if pixmap and not pixmap.isNull():
            self._base_pixmap = pixmap
            self._apply_icon_size()
        elif self.path.startswith("uwp:") or self.path.startswith("startapp:"):
            icon = svg_to_icon(ICONS["windows_apps"], "#4fc3f7")
            fallback = icon.pixmap(self.icon_size, self.icon_size)
            if not fallback.isNull():
                self._base_pixmap = fallback
                self._apply_icon_size()
            else:
                self.icon_label.setText("UWP")
        else:
            self.icon_label.setText("?")

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

    # ----------------------------------------------------------------- name

    def _display_name(self):
        return self.custom_name if self.custom_name else self.name

    # ----------------------------------------------------------- custom badge

    def _refresh_custom_badge(self):
        """Show a small 'C' badge in the bottom-right of the icon when any
        custom data is set."""
        has_custom = bool(self.custom_icon_path) or bool(self.custom_name)
        if has_custom:
            self.custom_badge.show()
            # bottom-right of icon container
            badge_x = self.icon_container_size - self.custom_badge.width() + 4
            badge_y = self.icon_container_size - self.custom_badge.height() + 4
            self.custom_badge.move(max(0, badge_x), max(0, badge_y))
        else:
            self.custom_badge.hide()

    # -------------------------------------------------------------- events

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

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        set_name_action = menu.addAction("Set Custom Name...")
        set_icon_action = menu.addAction("Set Custom Icon...")
        reset_name_action = menu.addAction("Reset Custom Name")
        reset_icon_action = menu.addAction("Reset Custom Icon")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        # Enable / disable the reset actions based on whether custom data exists.
        reset_name_action.setEnabled(bool(self.custom_name))
        reset_icon_action.setEnabled(bool(self.custom_icon_path))

        chosen = menu.exec(event.globalPos())
        if chosen is None:
            return

        if chosen is set_name_action:
            self._prompt_set_custom_name()
        elif chosen is set_icon_action:
            self._prompt_set_custom_icon()
        elif chosen is reset_name_action:
            self._clear_custom_name()
        elif chosen is reset_icon_action:
            self._clear_custom_icon()
        elif chosen is delete_action:
            self._on_delete_clicked()

    # ----------------------------------------------------------- behaviours

    def _launch_app(self):
        if self.path.startswith("uwp:") or self.path.startswith("startapp:"):
            app_id = self.path.split(":", 1)[1]
            if app_id:
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
            return

        if self.path.startswith("url:"):
            url = self.path.split(":", 1)[1]
            if url:
                # On Windows, os.startfile opens the URL in the default browser.
                try:
                    os.startfile(url)  # type: ignore[attr-defined]
                    return
                except Exception:
                    pass
                # Fallback: webbrowser uses the OS's default handler.
                import webbrowser
                webbrowser.open(url)
            return

        if os.path.exists(self.path):
            os.startfile(self.path)

    def _on_delete_clicked(self):
        self.deleted.emit(self.path)

    # ------------------------------------------------------ custom name flow

    def _prompt_set_custom_name(self):
        current = self.custom_name if self.custom_name else self.name
        new_name, ok = QInputDialog.getText(
            self,
            "Set Custom Name",
            f"Display name for this shortcut:\n(Leave blank and press OK to reset.)",
            text=current,
        )
        if not ok:
            return
        new_name = (new_name or "").strip()
        if not new_name:
            # Blank input clears the custom name and falls back to the original.
            self._clear_custom_name()
            return
        if new_name == self.name:
            # Same as the default -> clear the override instead of storing it.
            self._clear_custom_name()
            return
        self.custom_name = new_name
        self.name_label.setText(new_name)
        self._refresh_custom_badge()
        self.customDataChanged.emit(self.path)

    def _clear_custom_name(self):
        if not self.custom_name:
            return
        self.custom_name = None
        self.name_label.setText(self.name)
        self._refresh_custom_badge()
        self.customDataChanged.emit(self.path)

    # ------------------------------------------------------- custom icon flow

    def _prompt_set_custom_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Icon",
            "",
            "Icon files (*.png *.ico *.jpg *.jpeg *.bmp *.gif *.webp);;All files (*.*)",
        )
        if not file_path:
            return
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Invalid Icon", "The selected file does not exist.")
            return
        test_pix = _load_icon_from_file(file_path)
        if test_pix is None or test_pix.isNull():
            QMessageBox.warning(self, "Invalid Icon", "The selected file is not a supported image.")
            return
        self.custom_icon_path = file_path
        self._load_icon()
        self._refresh_custom_badge()
        self.customDataChanged.emit(self.path)

    def _clear_custom_icon(self):
        if not self.custom_icon_path:
            return
        self.custom_icon_path = None
        self._load_icon()
        self._refresh_custom_badge()
        self.customDataChanged.emit(self.path)
