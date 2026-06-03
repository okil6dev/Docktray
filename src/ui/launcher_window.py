import os
import json
import subprocess
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QScrollArea, QFrame, QApplication, QToolButton, QMenu, QMessageBox, QLabel, QPushButton, QListWidget, QInputDialog
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize, QPoint, pyqtSignal, QEventLoop, QEvent
from PyQt6.QtGui import QColor, QPalette, QAction, QPainter

from .flow_layout import FlowLayout
from .shortcut_item import ShortcutItem
from src.core.config_manager import ConfigManager
from .ui_utils import svg_to_icon, ICONS
from src.settings_window import SettingsWindow
from qfluentwidgets import qconfig

from qframelesswindow import AcrylicWindow
try:
    from qframelesswindow import WindowEffect
except Exception:
    WindowEffect = None

class StartAppPickerDialog(AcrylicWindow):
    accepted = pyqtSignal(str)
    rejected = pyqtSignal()

    def __init__(self, labels, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Window Apps")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.titleBar.hide()
        self.selected_label = ""
        self._mode = mode
        self._is_acrylic = "acrylic" in mode
        self._is_dark = "dark" in mode
        self._drag_active = False
        self._drag_offset = QPoint()
        self._window_effect = WindowEffect(self) if WindowEffect else None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        panel = QFrame(self)
        panel.setObjectName("PickerPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 10, 12, 10)
        panel_layout.setSpacing(10)

        self.title_bar_widget = QFrame(panel)
        title_bar = QHBoxLayout(self.title_bar_widget)
        title_bar.setContentsMargins(0, 0, 0, 0)
        title_bar.setSpacing(8)
        self.title_label = QLabel("Add Window Apps", self.title_bar_widget)
        self.close_btn = QToolButton(self.title_bar_widget)
        self.close_btn.setText("✕")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.close)
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()
        title_bar.addWidget(self.close_btn)

        title = QLabel("Select a Start menu app:", panel)
        self.app_list = QListWidget(panel)
        self.app_list.addItems(labels)
        self.app_list.setCurrentRow(0 if labels else -1)
        self.app_list.itemDoubleClicked.connect(lambda _: self._accept())

        actions = QHBoxLayout()
        actions.addStretch()
        ok_btn = QPushButton("OK", panel)
        cancel_btn = QPushButton("Cancel", panel)
        ok_btn.clicked.connect(self._accept)
        cancel_btn.clicked.connect(self.close)
        actions.addWidget(ok_btn)
        actions.addWidget(cancel_btn)

        panel_layout.addWidget(self.title_bar_widget)
        panel_layout.addWidget(title)
        panel_layout.addWidget(self.app_list)
        panel_layout.addLayout(actions)
        root.addWidget(panel)

        root_bg = "transparent" if self._is_acrylic else ("#1f1f1f" if self._is_dark else "#f3f3f3")
        panel_bg = "rgba(20, 20, 20, 0.55)" if self._is_dark else "rgba(255, 255, 255, 0.62)"
        border = "rgba(255, 255, 255, 0.16)" if self._is_dark else "rgba(0, 0, 0, 0.12)"
        panel_surface = "rgba(28, 28, 28, 0.78)" if self._is_dark else "rgba(255, 255, 255, 0.78)"
        if self._is_acrylic:
            # Keep host transparent for blur, but keep panel readable.
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
            # Lower panel alpha so acrylic remains visible, while still readable.
            panel_alpha = max(0.18, min(0.55, 0.12 + (float(saved_opacity) * 0.004)))
            panel_surface = (
                f"rgba(28, 28, 28, {panel_alpha:.2f})"
                if self._is_dark else
                f"rgba(255, 255, 255, {panel_alpha:.2f})"
            )
            control_alpha = max(0.28, min(0.62, panel_alpha + 0.10))
            panel_bg = (
                f"rgba(28, 28, 28, {control_alpha:.2f})"
                if self._is_dark else
                f"rgba(245, 245, 245, {control_alpha:.2f})"
            )
            border = "rgba(255, 255, 255, 0.20)" if self._is_dark else "rgba(0, 0, 0, 0.16)"
        text = "#f0f0f0" if self._is_dark else "#202020"
        self.setStyleSheet(f"""
            StartAppPickerDialog {{
                background: {root_bg};
            }}
            QFrame#PickerPanel {{
                background: {panel_surface};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame#titleBar {{
                background: transparent;
                border: none;
            }}
            QLabel {{
                color: {text};
                background: transparent;
                border: none;
                font-size: 15px;
            }}
            QListWidget {{
                background: {panel_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 6px;
            }}
            QListWidget::item:selected {{
                background: rgba(120, 180, 220, 0.28);
                color: {text};
            }}
            QPushButton {{
                background: {panel_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 6px 14px;
                min-width: 78px;
            }}
            QPushButton:hover {{
                background: rgba(120, 180, 220, 0.22);
            }}
            QToolButton {{
                background: transparent;
                color: {text};
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 700;
            }}
            QToolButton:hover {{
                background: rgba(120, 180, 220, 0.22);
            }}
        """)
        # Force consistent foreground rendering on acrylic (prevents washed/faded text).
        ctrl_palette = self.app_list.palette()
        text_col = QColor(240, 240, 240) if self._is_dark else QColor(32, 32, 32)
        bg_col = QColor(40, 40, 40, 170) if self._is_dark else QColor(250, 250, 250, 165)
        ctrl_palette.setColor(QPalette.ColorRole.Text, text_col)
        ctrl_palette.setColor(QPalette.ColorRole.ButtonText, text_col)
        ctrl_palette.setColor(QPalette.ColorRole.WindowText, text_col)
        ctrl_palette.setColor(QPalette.ColorRole.Base, bg_col)
        ctrl_palette.setColor(QPalette.ColorRole.Button, bg_col)
        ctrl_palette.setColor(QPalette.ColorRole.HighlightedText, text_col)
        self.app_list.setPalette(ctrl_palette)
        ok_btn.setPalette(ctrl_palette)
        cancel_btn.setPalette(ctrl_palette)
        self.title_label.setPalette(ctrl_palette)

        self.title_bar_widget.setObjectName("titleBar")
        self.resize(430, 142)

    def _accept(self):
        current_item = self.app_list.currentItem()
        self.selected_label = current_item.text().strip() if current_item else ""
        self.accepted.emit(self.selected_label)
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        if self._is_acrylic:
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
            whiteness = 100 if not self._is_dark else 0  # For StartAppPickerDialog, use full white for light mode

            # Allow higher opacity when whiteness is high to achieve maximum lightness
            if whiteness >= 90:
                opacity = max(1, min(255, int(saved_opacity * 2.55)))  # 100 * 2.55 = 255
            else:
                opacity = max(1, min(255, int(saved_opacity * 13)))

            alpha = f"{opacity:02x}"

            # When whiteness is 100%, use pure white (FFFFFF) for maximum lightness
            if whiteness >= 100:
                base = "FFFFFF"
            elif self._is_dark:
                base = "202020"
            else:
                base = "FFFFFF"

            disable_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
            self.windowEffect.removeBackgroundEffect(self.winId())
            if disable_overlay:
                self.windowEffect.setAcrylicEffect(self.winId(), "00000000")
            else:
                self.windowEffect.setAcrylicEffect(self.winId(), f"{base}{alpha}")
        else:
            self.windowEffect.removeBackgroundEffect(self.winId())
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar_widget.geometry().contains(event.position().toPoint()):
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        if not self.selected_label:
            self.rejected.emit()
        super().closeEvent(event)

class LauncherWindow(AcrylicWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("LauncherWindow")
        self.setWindowTitle("DockTray Launcher")
        
        # Match example structure
        self.titleBar.raise_()
        self.titleBar.hide()
        
        # Merge our tool flags with the library's flags safely
        self.setWindowFlags(
            self.windowFlags() | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Launcher dimensions
        self.window_width = int(ConfigManager.get_setting("tray_width", 400))
        self.window_height = int(ConfigManager.get_setting("tray_height", 250))
        self.resize(self.window_width, self.window_height)
        
        self.setAcceptDrops(False)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setContentsMargins(2, 2, 2, 2) 
        self.layout.addWidget(self.container)
        
        # Scroll area for shortcuts
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background: transparent;")
        
        self.flow_layout = FlowLayout(self.scroll_widget)
        self.flow_layout.setContentsMargins(2, 2, 2, 2)
        self.flow_layout.setSpacing(4)
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.vbox.addWidget(self.scroll_area)
        
        # Bottom Bar - 1.25x height (38 * 1.25 = 47)
        self.bottom_bar = QFrame(self)
        self.bottom_bar.setFixedHeight(47)
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(4, 0, 4, 0)
        self.bottom_layout.setSpacing(4)
        
        # Add File Button - 1.25x (32 * 1.25 = 40)
        self.add_file_btn = QToolButton(self)
        self.add_file_btn.setIcon(svg_to_icon(ICONS["add_file"], "#E0E0E0"))
        self.add_file_btn.setIconSize(QSize(25, 25))
        self.add_file_btn.setToolTip("Add File/App")
        self.add_file_btn.setFixedSize(40, 40)
        self.add_file_btn.clicked.connect(self._add_file)
        
        # Add Folder Button
        self.add_folder_btn = QToolButton(self)
        self.add_folder_btn.setIcon(svg_to_icon(ICONS["add_folder"], "#E0E0E0"))
        self.add_folder_btn.setIconSize(QSize(25, 25))
        self.add_folder_btn.setToolTip("Add Folder")
        self.add_folder_btn.setFixedSize(40, 40)
        self.add_folder_btn.clicked.connect(self._add_folder)

        # Window Apps Button
        self.add_windows_apps_btn = QToolButton(self)
        self.add_windows_apps_btn.setIcon(svg_to_icon(ICONS["windows_apps"], "#E0E0E0"))
        self.add_windows_apps_btn.setIconSize(QSize(24, 24))
        self.add_windows_apps_btn.setToolTip("Add Window Apps")
        self.add_windows_apps_btn.setFixedSize(40, 40)
        self.add_windows_apps_btn.clicked.connect(self._add_windows_app)

        # Drag Mode Button
        self.drag_mode_btn = QToolButton(self)
        self.drag_mode_btn.setIcon(svg_to_icon(ICONS["drag_mode"], "#E0E0E0"))
        self.drag_mode_btn.setIconSize(QSize(24, 24))
        self.drag_mode_btn.setToolTip("Enable Drag Mode")
        self.drag_mode_btn.setFixedSize(40, 40)
        self.drag_mode_btn.setCheckable(True)
        self.drag_mode_btn.toggled.connect(self._toggle_drag_mode)
        self.drag_mode_enabled = False
        
        # Settings Button
        self.settings_btn = QToolButton(self)
        self.settings_btn.setIcon(svg_to_icon(ICONS["settings"], "#E0E0E0"))
        self.settings_btn.setIconSize(QSize(24, 24))
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.clicked.connect(self._show_settings_menu)
        
        # Close Button
        self.close_btn = QToolButton(self)
        self.close_btn.setIcon(svg_to_icon(ICONS["close"], "#E0E0E0"))
        self.close_btn.setIconSize(QSize(24, 24))
        self.close_btn.setToolTip("Hide Launcher")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.clicked.connect(self.hide_launcher)
        
        self.bottom_layout.addWidget(self.add_file_btn)
        self.bottom_layout.addWidget(self.add_folder_btn)
        self.bottom_layout.addWidget(self.add_windows_apps_btn)
        self.bottom_layout.addWidget(self.drag_mode_btn)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.settings_btn)
        self.bottom_layout.addWidget(self.close_btn)
        
        self.vbox.addWidget(self.bottom_bar)

        # Tray resize mode controls (shown only when editing tray size)
        self._tray_resize_mode = False
        self._tray_resizing = False
        self._tray_resize_start_pos = QPoint()
        self._tray_resize_start_size = QSize()
        self._tray_resize_start_geom = QRect()
        self._tray_original_size = QSize(self.window_width, self.window_height)
        self._tray_settings_was_visible = False

        self.resize_corner_btn = QToolButton(self.container)
        self.resize_corner_btn.setText("◢")
        self.resize_corner_btn.setToolTip("Drag to resize tray")
        self.resize_corner_btn.setFixedSize(20, 20)
        self.resize_corner_btn.hide()
        self.resize_corner_btn.installEventFilter(self)

        self.apply_tray_size_btn = QPushButton("Apply", self.container)
        self.apply_tray_size_btn.setFixedSize(64, 24)
        self.apply_tray_size_btn.clicked.connect(self._apply_tray_size)
        self.apply_tray_size_btn.hide()

        self.cancel_tray_size_btn = QPushButton("Cancel", self.container)
        self.cancel_tray_size_btn.setFixedSize(64, 24)
        self.cancel_tray_size_btn.clicked.connect(self._cancel_tray_size)
        self.cancel_tray_size_btn.hide()
        
        # Load theme config
        self.current_theme_mode = ConfigManager.get_setting("theme_mode", "acrylic")
        self.current_whiteness = ConfigManager.get_setting("theme_whiteness", 0)
        self.disable_acrylic_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
        self._is_dialog_open = False
        self.settings_window = None
        self.set_theme(self.current_theme_mode, self.current_whiteness)
        self._apply_button_size(int(ConfigManager.get_setting("launcher_button_size", 40)))
        self.load_shortcuts()
        

    def _show_settings_menu(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self)
            self.settings_window.themeModeChanged.connect(self._on_theme_mode_changed)
            self.settings_window.whitenessChanged.connect(self._on_whiteness_changed)
            self.settings_window.iconColorChanged.connect(self._on_icon_color_changed)
            self.settings_window.acrylicOpacityChanged.connect(self._on_acrylic_opacity_changed)
            self.settings_window.positionChanged.connect(self.reposition)
            self.settings_window.iconSizeChanged.connect(self._on_icon_size_changed)
            self.settings_window.buttonSizeChanged.connect(self._on_button_size_changed)
            self.settings_window.traySizeEditRequested.connect(self._start_tray_size_mode)
            self.settings_window.traySizeResetRequested.connect(self._reset_tray_size_to_default)
            self.settings_window.closed.connect(self._on_settings_closed)
            
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
        # Mark dialog open so launcher doesn't hide when settings is active
        self._is_dialog_open = True

    def _on_theme_mode_changed(self, mode):
        """Handle theme mode changes from settings (black/white/acrylic)"""
        self.current_theme_mode = mode
        ConfigManager.set_setting("theme_mode", mode)

        # Check if settings window is currently open
        settings_was_open = self.settings_window is not None and self.settings_window.isVisible()

        # Close and destroy old settings window so it reloads with new theme
        old_settings = self.settings_window
        self.settings_window = None
        if old_settings:
            old_settings.close()
            old_settings.deleteLater()

        # Apply the new theme to the launcher
        self._apply_full_theme()

        # Recreate and show settings window immediately with fresh theme if it was open
        if settings_was_open:
            self.settings_window = SettingsWindow(self)
            self.settings_window.themeModeChanged.connect(self._on_theme_mode_changed)
            self.settings_window.whitenessChanged.connect(self._on_whiteness_changed)
            self.settings_window.iconColorChanged.connect(self._on_icon_color_changed)
            self.settings_window.acrylicOpacityChanged.connect(self._on_acrylic_opacity_changed)
            self.settings_window.positionChanged.connect(self.reposition)
            self.settings_window.iconSizeChanged.connect(self._on_icon_size_changed)
            self.settings_window.buttonSizeChanged.connect(self._on_button_size_changed)
            self.settings_window.traySizeEditRequested.connect(self._start_tray_size_mode)
            self.settings_window.traySizeResetRequested.connect(self._reset_tray_size_to_default)
            self.settings_window.closed.connect(self._on_settings_closed)
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()

            # Force apply the correct theme to the new settings window
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.settings_window._apply_settings_theme(self.current_theme_mode))

    def _on_whiteness_changed(self, whiteness):
        """Apply whiteness to launcher, then completely recreate settings window"""
        self.current_whiteness = whiteness
        ConfigManager.set_setting("theme_whiteness", whiteness)
        self._apply_full_theme()
        
        # Close and destroy old settings window so it reloads with new theme
        old_settings = self.settings_window
        self.settings_window = None
        if old_settings:
            old_settings.close()
            old_settings.deleteLater()
        
        # Recreate and show immediately with fresh theme
        self.settings_window = SettingsWindow(self)
        self.settings_window.themeModeChanged.connect(self._on_theme_mode_changed)
        self.settings_window.whitenessChanged.connect(self._on_whiteness_changed)
        self.settings_window.iconColorChanged.connect(self._on_icon_color_changed)
        self.settings_window.acrylicOpacityChanged.connect(self._on_acrylic_opacity_changed)
        self.settings_window.positionChanged.connect(self.reposition)
        self.settings_window.iconSizeChanged.connect(self._on_icon_size_changed)
        self.settings_window.buttonSizeChanged.connect(self._on_button_size_changed)
        self.settings_window.traySizeEditRequested.connect(self._start_tray_size_mode)
        self.settings_window.traySizeResetRequested.connect(self._reset_tray_size_to_default)
        self.settings_window.closed.connect(self._on_settings_closed)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
        # Force apply acrylic/background settings to the new window
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.settings_window._apply_settings_theme(self.current_theme_mode))

    def _apply_full_theme(self):
        """Apply current theme mode + whiteness to the launcher"""
        # Update QFluentWidgets theme
        if self.current_theme_mode == "acrylic":
            is_dark = self.current_whiteness < 50
            if is_dark:
                qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1])  # Dark
            else:
                qconfig.set(qconfig.themeMode, qconfig.themeMode.options[0])  # Light
        elif self.current_theme_mode == "black":
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1])  # Dark
        else:  # white
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[0])  # Light
        
        self.set_theme(self.current_theme_mode, self.current_whiteness)

    def _on_icon_color_changed(self, color):
        """Update icon colors without changing the color scheme"""
        ConfigManager.set_setting("icon_color", color)
        self._apply_icon_color(color)

    def _on_acrylic_opacity_changed(self, value):
        """Re-apply acrylic effect with new opacity to both windows (acrylic mode only)"""
        ConfigManager.set_setting("acrylic_opacity", value)

        if self.current_theme_mode == "acrylic":
            whiteness = self.current_whiteness

            # When whiteness is 100%, use pure white (FFFFFF) for maximum lightness
            # but respect the user's opacity setting
            if whiteness >= 100:
                base = "FFFFFF"
            elif whiteness >= 90:
                # For high whiteness (90-99), use minimal opacity for maximum color passthrough
                # 50% of original scaling factor (0.8 -> 0.4)
                opacity = max(1, min(255, int(value * 0.4)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFA - 0x20) * ratio)
                g = int(0x20 + (0xFA - 0x20) * ratio)
                b = int(0x20 + (0xFA - 0x20) * ratio)
                base = f"{r:02x}{g:02x}{b:02x}"
            else:
                # For lower whiteness, use 50% of original scaling
                # 50% of original scaling factor (3 -> 1.5)
                opacity = max(1, min(255, int(value * 1.5)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFA - 0x20) * ratio)
                g = int(0x20 + (0xFA - 0x20) * ratio)
                b = int(0x20 + (0xFA - 0x20) * ratio)
                base = f"{r:02x}{g:02x}{b:02x}"

            # For 100% whiteness, use minimal opacity setting
            if whiteness >= 100:
                opacity = max(1, min(255, int(value * 0.4)))
            alpha = f"{opacity:02x}"

            color = f"{base}{alpha}"

            # Apply to launcher
            self.windowEffect.removeBackgroundEffect(self.winId())

            # Apply acrylic effect with or without overlay based on setting
            self.disable_acrylic_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
            if self.disable_acrylic_overlay:
                # Use transparent color for no overlay effect
                self.windowEffect.setAcrylicEffect(self.winId(), "00000000")
            else:
                # Use the colored overlay
                self.windowEffect.setAcrylicEffect(self.winId(), color)

            # Apply to settings window if open
            if self.settings_window:
                self.settings_window.windowEffect.removeBackgroundEffect(self.settings_window.winId())
                # Apply the same overlay setting to settings window
                if self.disable_acrylic_overlay:
                    self.settings_window.windowEffect.setAcrylicEffect(self.settings_window.winId(), "00000000")
                else:
                    self.settings_window.windowEffect.setAcrylicEffect(self.settings_window.winId(), color)

        # Re-apply container styling with current whiteness
        self.setup_style()

    def _on_settings_closed(self):
        self._is_dialog_open = False
        self._exit_tray_size_mode()
        self.settings_window = None

    def _on_acrylic_overlay_changed(self):
        """Handle acrylic overlay checkbox state changes from settings"""
        if self.current_theme_mode == "acrylic":
            # Re-apply the acrylic effect with the updated overlay setting
            self.disable_acrylic_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
            self.windowEffect.removeBackgroundEffect(self.winId())

            if self.disable_acrylic_overlay:
                # Use absolute default acrylic effect (no color overlay)
                self.windowEffect.setAcrylicEffect(self.winId(), "00000000")
            else:
                # Use the colored overlay
                whiteness = self.current_whiteness
                saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)

            # When whiteness is 100%, use pure white (FFFFFF) for maximum lightness
            # but respect the user's opacity setting
            if whiteness >= 100:
                base_color = "FFFFFF"
            elif whiteness >= 90:
                # For high whiteness (90-99), allow higher opacity range
                # Reduced scaling factor to allow more color through (2.55 -> 1.2)
                opacity = max(1, min(255, int(saved_opacity * 1.2)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFF - 0x20) * ratio)
                g = int(0x20 + (0xFF - 0x20) * ratio)
                b = int(0x20 + (0xFF - 0x20) * ratio)
                base_color = f"{r:02x}{g:02x}{b:02x}"
            else:
                # For lower whiteness, use reduced scaling to allow more color through
                # Reduced scaling factor from 13 to 6
                opacity = max(1, min(255, int(saved_opacity * 6)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFF - 0x20) * ratio)
                g = int(0x20 + (0xFF - 0x20) * ratio)
                b = int(0x20 + (0xFF - 0x20) * ratio)
                base_color = f"{r:02x}{g:02x}{b:02x}"

            # For 100% whiteness, use the user's opacity setting with reduced scaling
            if whiteness >= 100:
                opacity = max(1, min(255, int(saved_opacity * 1.2)))
                alpha = f"{opacity:02x}"

                color = f"{base_color}{alpha}"
                self.windowEffect.setAcrylicEffect(self.winId(), color)

    def _settings_is_open(self):
        return self.settings_window is not None and self.settings_window.isVisible()

    def eventFilter(self, obj, event):
        if obj is self.resize_corner_btn and self._tray_resize_mode:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._tray_resizing = True
                self._tray_resize_start_pos = event.globalPosition().toPoint()
                self._tray_resize_start_size = self.size()
                self._tray_resize_start_geom = self.geometry()
                return True
            if event.type() == QEvent.Type.MouseMove and self._tray_resizing:
                delta = event.globalPosition().toPoint() - self._tray_resize_start_pos
                min_w, min_h = 320, 190

                # Top-left handle: keep bottom-right fixed, resize toward top-left.
                new_w = self._tray_resize_start_size.width() - delta.x()
                new_h = self._tray_resize_start_size.height() - delta.y()
                new_w = max(min_w, new_w)
                new_h = max(min_h, new_h)

                start_right = self._tray_resize_start_geom.x() + self._tray_resize_start_geom.width()
                start_bottom = self._tray_resize_start_geom.y() + self._tray_resize_start_geom.height()
                new_x = start_right - new_w
                new_y = start_bottom - new_h

                self.setGeometry(new_x, new_y, new_w, new_h)
                self.window_width = new_w
                self.window_height = new_h
                self._position_resize_controls()
                return True
            if event.type() == QEvent.Type.MouseButtonRelease and self._tray_resizing:
                self._tray_resizing = False
                return True
        return super().eventFilter(obj, event)

    def _on_icon_size_changed(self, size):
        size = int(size)
        ConfigManager.set_setting("shortcut_icon_size", size)
        for i in range(self.flow_layout.count()):
            widget = self.flow_layout.itemAt(i).widget()
            if isinstance(widget, ShortcutItem):
                widget.set_icon_size(size)

    def _on_button_size_changed(self, size):
        size = int(size)
        ConfigManager.set_setting("launcher_button_size", size)
        self._apply_button_size(size)

    def _apply_button_size(self, size):
        size = max(32, min(56, int(size)))
        self.bottom_bar.setFixedHeight(size + 7)
        action_icon = max(18, int(size * 0.62))
        settings_icon = max(17, int(size * 0.60))

        self.add_file_btn.setFixedSize(size, size)
        self.add_folder_btn.setFixedSize(size, size)
        self.add_windows_apps_btn.setFixedSize(size, size)
        self.drag_mode_btn.setFixedSize(size, size)
        self.settings_btn.setFixedSize(size, size)
        self.close_btn.setFixedSize(size, size)

        self.add_file_btn.setIconSize(QSize(action_icon, action_icon))
        self.add_folder_btn.setIconSize(QSize(action_icon, action_icon))
        self.add_windows_apps_btn.setIconSize(QSize(settings_icon, settings_icon))
        self.drag_mode_btn.setIconSize(QSize(settings_icon, settings_icon))
        self.settings_btn.setIconSize(QSize(settings_icon, settings_icon))
        self.close_btn.setIconSize(QSize(settings_icon, settings_icon))
        self._position_resize_controls()

    def _start_tray_size_mode(self):
        self._tray_settings_was_visible = self._settings_is_open()
        if self._tray_settings_was_visible and self.settings_window:
            self.settings_window.hide()
        self._tray_original_size = self.size()
        self._tray_resize_mode = True
        self._is_dialog_open = True
        self.resize_corner_btn.show()
        self.apply_tray_size_btn.show()
        self.cancel_tray_size_btn.show()
        self._position_resize_controls()
        self.raise_()
        self.activateWindow()

    def _exit_tray_size_mode(self):
        self._tray_resize_mode = False
        self._tray_resizing = False
        self.resize_corner_btn.hide()
        self.apply_tray_size_btn.hide()
        self.cancel_tray_size_btn.hide()

    def _apply_tray_size(self):
        ConfigManager.set_setting("tray_width", int(self.width()))
        ConfigManager.set_setting("tray_height", int(self.height()))
        self.window_width = int(self.width())
        self.window_height = int(self.height())

        # Instant launcher reload to re-apply acrylic and sizing visuals.
        current_geom = self.geometry()
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
            self.setGeometry(current_geom)
            self.show()
            self.raise_()
            self.activateWindow()

        # Re-apply theme/effects explicitly after resize.
        self.set_theme(self.current_theme_mode, self.current_whiteness)

        # Bring settings back to the front.
        if self._tray_settings_was_visible and self.settings_window:
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()

        self._exit_tray_size_mode()
        self._is_dialog_open = self._settings_is_open()

    def _reset_tray_size_to_default(self):
        default_w, default_h = 400, 250
        ConfigManager.set_setting("tray_width", default_w)
        ConfigManager.set_setting("tray_height", default_h)
        self.window_width = default_w
        self.window_height = default_h
        self.resize(default_w, default_h)
        self.reposition()
        self.set_theme(self.current_theme_mode, self.current_whiteness)

    def _cancel_tray_size(self):
        self.resize(self._tray_original_size)
        self.window_width = int(self._tray_original_size.width())
        self.window_height = int(self._tray_original_size.height())
        if self._tray_settings_was_visible and self.settings_window:
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
        self._exit_tray_size_mode()
        self._is_dialog_open = self._settings_is_open()

    def _position_resize_controls(self):
        if not hasattr(self, "container"):
            return
        margin = 6
        handle_w = self.resize_corner_btn.width()
        handle_h = self.resize_corner_btn.height()
        x = margin
        y = margin
        self.resize_corner_btn.move(x, y)

        btn_w = self.apply_tray_size_btn.width()
        btn_h = self.apply_tray_size_btn.height()
        self.apply_tray_size_btn.move(x + handle_w + 8, max(0, y - (btn_h - handle_h) // 2))
        cancel_w = self.cancel_tray_size_btn.width()
        self.cancel_tray_size_btn.move(x + handle_w + btn_w + 16, max(0, y - (btn_h - handle_h) // 2))

    def set_theme(self, mode, whiteness=None):
        """Apply theme based on mode and optional whiteness.
        mode: 'black' (solid dark), 'white' (solid light), 'acrylic' (acrylic with whiteness)
        """
        self.current_theme_mode = mode
        if whiteness is not None:
            self.current_whiteness = whiteness
            ConfigManager.set_setting("theme_whiteness", self.current_whiteness)

        is_dark = self.current_whiteness < 50 if mode == "acrylic" else (mode == "black")

        # Update QFluentWidgets theme
        qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1 if is_dark else 0])

        # Clear any existing background effect
        self.windowEffect.removeBackgroundEffect(self.winId())

        if mode == "acrylic":
            # Acrylic mode - transparent background with blur
            self.setStyleSheet("background: transparent;")
            whiteness = self.current_whiteness
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)

            # When whiteness is 100%, use pure white (FFFFFF) for maximum lightness
            # but respect the user's opacity setting
            if whiteness >= 100:
                base_color = "FFFFFF"
            elif whiteness >= 90:
                # For high whiteness (90-99), use minimal opacity for maximum color passthrough
                # 50% of original scaling factor (0.8 -> 0.4)
                opacity = max(1, min(255, int(saved_opacity * 0.4)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFF - 0x20) * ratio)
                g = int(0x20 + (0xFF - 0x20) * ratio)
                b = int(0x20 + (0xFF - 0x20) * ratio)
                base_color = f"{r:02x}{g:02x}{b:02x}"
            else:
                # For lower whiteness, use 50% of original scaling
                # 50% of original scaling factor (3 -> 1.5)
                opacity = max(1, min(255, int(saved_opacity * 1.5)))
                ratio = whiteness / 100.0
                r = int(0x20 + (0xFF - 0x20) * ratio)
                g = int(0x20 + (0xFF - 0x20) * ratio)
                b = int(0x20 + (0xFF - 0x20) * ratio)
                base_color = f"{r:02x}{g:02x}{b:02x}"

            # For 100% whiteness, use minimal opacity setting
            if whiteness >= 100:
                opacity = max(1, min(255, int(saved_opacity * 0.4)))
            alpha = f"{opacity:02x}"

            color = f"{base_color}{alpha}"

            # Apply acrylic effect with or without overlay based on setting
            self.disable_acrylic_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
            if self.disable_acrylic_overlay:
                # Use transparent color for no overlay effect
                self.windowEffect.setAcrylicEffect(self.winId(), "00000000")
            else:
                # Use the colored overlay
                self.windowEffect.setAcrylicEffect(self.winId(), color)
        elif mode == "black":
            # Solid dark mode - no acrylic
            self.setStyleSheet("background: #1e1e1e;")
        else:  # white
            # Solid light mode - no acrylic
            self.setStyleSheet("background: #f3f3f3;")

        # Apply the rest of the styling
        self.setup_style()

        # Update shortcut items text color
        text_color = "white" if is_dark else "#333333"
        hover_bg = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.05)"

        for i in range(self.flow_layout.count()):
            widget = self.flow_layout.itemAt(i).widget()
            if isinstance(widget, ShortcutItem):
                widget.name_label.setStyleSheet(f"color: {text_color};")
                widget.setStyleSheet(f"ShortcutItem {{ border-radius: 8px; }} ShortcutItem:hover {{ background-color: {hover_bg}; }}")

    def _apply_icon_color(self, color):
        """Set icon colors based on the icon_color setting (white or black)"""
        icon_color = "#E0E0E0" if color == "white" else "#333333"
        self.add_file_btn.setIcon(svg_to_icon(ICONS["add_file"], icon_color))
        self.add_folder_btn.setIcon(svg_to_icon(ICONS["add_folder"], icon_color))
        self.add_windows_apps_btn.setIcon(svg_to_icon(ICONS["windows_apps"], icon_color))
        self.drag_mode_btn.setIcon(svg_to_icon(ICONS["drag_mode"], icon_color))
        self.settings_btn.setIcon(svg_to_icon(ICONS["settings"], icon_color))
        self.close_btn.setIcon(svg_to_icon(ICONS["close"], icon_color))

    def setup_style(self):
        """Apply container/border/button styling based on current theme mode and whiteness."""
        is_dark = self.current_whiteness < 50 if self.current_theme_mode == "acrylic" else (self.current_theme_mode == "black")
        
        if self.current_theme_mode == "acrylic":
            # Acrylic mode - semi-transparent container so blur shows through
            ratio = self.current_whiteness / 100.0
            
            # When whiteness is high, move towards pure white without darkening
            if ratio >= 0.9:
                # Interpolate between the dimmed light color and pure white
                # At ratio 0.9: r = 0xf3 * 0.55 = 133
                # At ratio 1.0: r = 255
                start_val = int(0xf3 * 0.55)
                progress = (ratio - 0.9) / 0.1
                r = int(start_val + (255 - start_val) * progress)
                bg_color = f"rgba({r}, {r}, {r}, 0.10)"
            else:
                bg_r = int(0x1e + (0xf3 - 0x1e) * ratio)
                bg_g = int(0x1e + (0xf3 - 0x1e) * ratio)
                bg_b = int(0x1e + (0xf3 - 0x1e) * ratio)
                container_r = int(bg_r * 0.55)
                container_g = int(bg_g * 0.55)
                container_b = int(bg_b * 0.55)
                bg_color = f"rgba({container_r}, {container_g}, {container_b}, 0.10)"
            
            border_color = "rgba(255, 255, 255, 0.15)" if is_dark else "rgba(0, 0, 0, 0.1)"
        elif self.current_theme_mode == "black":
            # Solid black mode
            bg_color = "#1e1e1e"
            border_color = "#444444"
        else:  # white
            bg_color = "#f3f3f3"
            border_color = "#cccccc"
        
        btn_hover = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.03)"
            
        # Finalize the stylesheet
        style = f"""
            #LauncherWindow {{
                background: transparent;
            }}
            QFrame#Container {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            QToolButton {{
                border: none;
                border-radius: 6px;
                background-color: transparent;
            }}
            QToolButton:hover {{
                background-color: {btn_hover};
            }}
            QToolButton:pressed {{
                background-color: rgba(0, 0, 0, 0.04);
            }}
            QToolButton:checked {{
                background-color: {btn_hover};
                border: 1px solid {border_color};
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 4px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(128, 128, 128, 0.15);
                min-height: 20px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(128, 128, 128, 0.25);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollArea QWidget {{
                background-color: transparent;
            }}
        """
        self.setStyleSheet(style)
        
        # Update bottom bar icons color using independent icon_color setting
        saved_icon_color = ConfigManager.get_setting("icon_color", "white")
        self._apply_icon_color(saved_icon_color)

    def load_shortcuts(self):
        # Clear existing
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        shortcuts = ConfigManager.load_shortcuts()
        migrated = False
        for s in shortcuts:
            p = s.get("path", "")
            if isinstance(p, str) and p.startswith("uwp:{") and "!" not in p:
                s["path"] = "startapp:" + p[4:]
                migrated = True
        if migrated:
            ConfigManager.save_shortcuts(shortcuts)

        icon_size = int(ConfigManager.get_setting("shortcut_icon_size", 45))
        for s in shortcuts:
            item = ShortcutItem(
                s["path"],
                s["name"],
                icon_size=icon_size,
                custom_icon=s.get("custom_icon"),
                custom_name=s.get("custom_name"),
            )
            item.deleted.connect(self._remove_shortcut)
            item.customDataChanged.connect(self._on_shortcut_custom_data_changed)
            self.flow_layout.addWidget(item)

    def _add_file(self):
        self._is_dialog_open = True
        path, _ = QFileDialog.getOpenFileName(self, "Select App or File")
        self._is_dialog_open = False
        if path:
            self._add_shortcut_path(path)
            
    def _add_folder(self):
        self._is_dialog_open = True
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        self._is_dialog_open = False
        if path:
            self._add_shortcut_path(path)

    def _add_windows_app(self):
        self._is_dialog_open = True
        apps = self._get_windows_apps()
        if not apps:
            self._is_dialog_open = False
            QMessageBox.information(self, "Window Apps", "No Start menu apps were found.")
            return

        labels = [app["name"] for app in apps]
        selected_label, ok = QInputDialog.getItem(
            self,
            "Add Window Apps",
            "Select a Start menu app:",
            labels,
            0,
            False
        )
        self._is_dialog_open = False

        if ok and selected_label:
            selected = next((a for a in apps if a["name"] == selected_label), None)
            if selected:
                self._add_shortcut_path(f'startapp:{selected["app_id"]}', selected["name"])

    def _get_windows_apps(self):
        command = (
            "Get-StartApps | Sort-Object Name | "
            "Select-Object Name, AppID | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                check=True
            )
            output = (result.stdout or "").strip()
            if not output:
                return []

            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            apps = []
            for item in data:
                name = str(item.get("Name", "")).strip()
                app_id = str(item.get("AppID", "")).strip()
                if not name or not app_id:
                    continue
                apps.append({"name": name, "app_id": app_id})
            return apps
        except Exception:
            return []

    def _add_shortcut_path(self, path, name=None):
        if isinstance(path, str) and path.startswith("uwp:{") and "!" not in path:
            # Migrate old non-UWP StartApps entries that were stored as uwp:.
            path = "startapp:" + path[4:]
        if not (isinstance(path, str) and (path.startswith("startapp:") or path.startswith("uwp:"))):
            path = os.path.normpath(path)
        if ConfigManager.add_shortcut(path, name):
            self.load_shortcuts()
    
    def _toggle_drag_mode(self, enabled):
        self.drag_mode_enabled = enabled
        self.setAcceptDrops(enabled)
        if enabled:
            self.drag_mode_btn.setToolTip("Disable Drag Mode")
            self.drag_mode_btn.setStatusTip("Drag and drop files, folders, or apps onto DockTray")
        else:
            self.drag_mode_btn.setToolTip("Enable Drag Mode")
            self.drag_mode_btn.setStatusTip("")

    def _remove_shortcut(self, path):
        if ConfigManager.remove_shortcut(path):
            self.load_shortcuts()

    def _on_shortcut_custom_data_changed(self, path):
        """Persist any new custom_icon / custom_name set via the right-click
        menu on a ShortcutItem. The matching item is still in the layout, so
        we read its current custom values and write them to config.json."""
        for i in range(self.flow_layout.count()):
            widget = self.flow_layout.itemAt(i).widget()
            if isinstance(widget, ShortcutItem) and widget.path == path:
                ConfigManager.update_shortcut(path, {
                    "custom_icon": widget.custom_icon_path,
                    "custom_name": widget.custom_name,
                })
                return

    # Drag and Drop functionality
    def dragEnterEvent(self, event):
        if self.drag_mode_enabled and event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        if not self.drag_mode_enabled:
            event.ignore()
            return

        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self._add_shortcut_path(path)
        event.acceptProposedAction()

    # Animation and Visibility
    def show_launcher(self, tray_geometry):
        # Get screen geometries
        screen_geo = QApplication.primaryScreen().availableGeometry()
        full_geo = QApplication.primaryScreen().geometry()
        pos_mode = ConfigManager.get_setting("taskbar_position", "Bottom")
        
        offset = 15
        
        # Calculate final and start positions based on mode
        # Goal: Bottom Right for Bottom/Right taskbars, Top Right for Top, Bottom Left for Left.
        if pos_mode == "Bottom Taskbar":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
            start_x, start_y = x, y + 20
        elif pos_mode == "Top Taskbar":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + offset
            start_x, start_y = x, y - 20
        elif pos_mode == "Left Taskbar (Vertical)":
            x = screen_geo.x() + offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
            start_x, start_y = x - 20, y
        elif pos_mode == "Right Taskbar (Vertical)":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
            start_x, start_y = x + 20, y
        else:
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
            start_x, start_y = x, y + 20
            
        self.setGeometry(start_x, start_y, self.window_width, self.window_height)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(150)
        self.anim.setStartValue(QRect(start_x, start_y, self.window_width, self.window_height))
        self.anim.setEndValue(QRect(x, y, self.window_width, self.window_height))
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(100)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        
        self.anim.start()
        self.fade_anim.start()

    def hide_launcher(self):
        current_rect = self.geometry()
        pos_mode = ConfigManager.get_setting("taskbar_position", "Bottom")
        
        # Calculate exit position
        if pos_mode == "Bottom":
            end_rect = QRect(current_rect.x(), current_rect.y() + 20, current_rect.width(), current_rect.height())
        elif pos_mode == "Top":
            end_rect = QRect(current_rect.x(), current_rect.y() - 20, current_rect.width(), current_rect.height())
        elif pos_mode == "Left":
            end_rect = QRect(current_rect.x() - 20, current_rect.y(), current_rect.width(), current_rect.height())
        elif pos_mode == "Right":
            end_rect = QRect(current_rect.x() + 20, current_rect.y(), current_rect.width(), current_rect.height())
        else:
            end_rect = QRect(current_rect.x(), current_rect.y() + 20, current_rect.width(), current_rect.height())
        
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(200)
        self.anim.setStartValue(current_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(150)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        
        self.anim.finished.connect(self.hide)
        self.anim.start()
        self.fade_anim.start()

    def reposition(self, pos_mode=None):
        """ Instantly move the launcher to the correct position (used for real-time settings updates) """
        if not self.isVisible():
            return
            
        screen_geo = QApplication.primaryScreen().availableGeometry()
        full_geo = QApplication.primaryScreen().geometry()
        if not pos_mode:
            pos_mode = ConfigManager.get_setting("taskbar_position", "Bottom")
            
        offset = 15
        
        if pos_mode == "Bottom Taskbar":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
        elif pos_mode == "Top Taskbar":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + offset
        elif pos_mode == "Left Taskbar (Vertical)":
            x = screen_geo.x() + offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
        elif pos_mode == "Right Taskbar (Vertical)":
            x = screen_geo.x() + screen_geo.width() - self.window_width - offset
            y = screen_geo.y() + screen_geo.height() - self.window_height - offset
        else:
            x, y = self.x(), self.y()
            
        self.move(x, y)

    # Hide when losing focus
    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange:
            if not self.isActiveWindow() and not self._is_dialog_open and not self._settings_is_open() and not self.drag_mode_enabled:
                if self.isVisible():
                    self.hide_launcher()
        super().changeEvent(event)

    def focusOutEvent(self, event):
        if not self._is_dialog_open and not self._settings_is_open() and not self.drag_mode_enabled and not self._tray_resize_mode and self.isVisible():
            self.hide_launcher()
        super().focusOutEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_resize_controls()
