import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QScrollArea, QFrame, QApplication, QToolButton, QMenu
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, QSize, QPoint
from PyQt6.QtGui import QColor, QPalette, QAction, QPainter

from .flow_layout import FlowLayout
from .shortcut_item import ShortcutItem
from src.core.config_manager import ConfigManager
from .ui_utils import svg_to_icon, ICONS
from .settings_window import SettingsWindow
from qfluentwidgets import qconfig

from qframelesswindow import AcrylicWindow

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
        self.window_width = 400
        self.window_height = 250 
        self.resize(self.window_width, self.window_height)
        
        self.setAcceptDrops(True)
        
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
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.settings_btn)
        self.bottom_layout.addWidget(self.close_btn)
        
        self.vbox.addWidget(self.bottom_bar)
        
        # Load theme from config
        self.current_mode = ConfigManager.get_setting("theme", "dark")
        self._is_dialog_open = False
        self.settings_window = None
        self.set_theme(self.current_mode)
        self.load_shortcuts()
        

    def _show_settings_menu(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow(self)
            self.settings_window.themeChanged.connect(self._on_theme_changed)
            self.settings_window.iconColorChanged.connect(self._on_icon_color_changed)
            self.settings_window.acrylicOpacityChanged.connect(self._on_acrylic_opacity_changed)
            self.settings_window.positionChanged.connect(self.reposition)
            
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
        # Mark dialog open so launcher doesn't hide when settings is active
        self._is_dialog_open = True

    def _on_theme_changed(self, mode):
        """Apply theme to launcher, then completely recreate settings window"""
        self.set_theme(mode)
        
        # Close and destroy old settings window so it reloads with new theme
        if self.settings_window:
            self.settings_window.close()
            self.settings_window.deleteLater()
            self.settings_window = None
        
        # Recreate and show immediately with fresh theme
        self.settings_window = SettingsWindow(self)
        self.settings_window.themeChanged.connect(self._on_theme_changed)
        self.settings_window.iconColorChanged.connect(self._on_icon_color_changed)
        self.settings_window.acrylicOpacityChanged.connect(self._on_acrylic_opacity_changed)
        self.settings_window.positionChanged.connect(self.reposition)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        
        # Force apply acrylic/background settings to the new window
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.settings_window._apply_qfluent_theme(self.current_mode))

    def _on_icon_color_changed(self, color):
        """Update icon colors without changing the color scheme"""
        ConfigManager.set_setting("icon_color", color)
        self._apply_icon_color(color)

    def _on_acrylic_opacity_changed(self, value):
        """Re-apply acrylic effect with new opacity to both windows"""
        opacity = max(1, min(255, int(value * 2.55)))  # Map 1-100 to 1-255
        alpha = f"{opacity:02x}"
        
        if "acrylic" in self.current_mode:
            is_dark = "dark" in self.current_mode
            base = "202020" if is_dark else "F2F2F2"
            color = f"{base}{alpha}"
            
            # Apply to launcher
            self.windowEffect.removeBackgroundEffect(self.winId())
            self.windowEffect.setAcrylicEffect(self.winId(), color)
            
            # Apply to settings window if open
            if self.settings_window:
                self.settings_window.windowEffect.removeBackgroundEffect(self.settings_window.winId())
                self.settings_window.windowEffect.setAcrylicEffect(self.settings_window.winId(), color)

    def _on_settings_closed(self):
        self._is_dialog_open = False
        self.settings_window = None

    def set_theme(self, mode):
        self.current_mode = mode
        ConfigManager.set_setting("theme", mode)
        
        # Update QFluentWidgets theme so settings window etc. use correct theme instantly
        if "dark" in mode:
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1])
        else:
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[0])
        
        # Apply effects first
        if "acrylic" in mode:
            # Set background to transparent first to allow blur to show
            self.setStyleSheet("background: transparent;")
            # Formatting: RRGGBBAA with saved opacity
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
            opacity = max(1, min(255, int(saved_opacity * 2.55)))
            alpha = f"{opacity:02x}"
            color = f"202020{alpha}" if "dark" in mode else f"F2F2F2{alpha}"
            self.windowEffect.setAcrylicEffect(self.winId(), color)
        else:
            self.windowEffect.removeBackgroundEffect(self.winId())
            
        # Apply the rest of the styling
        self.setup_style()
            
        # Update shortcut items text color
        is_light = (mode == "light" or mode == "acrylic_light")
        text_color = "white" if not is_light else "#333333"
        hover_bg = "rgba(255, 255, 255, 0.08)" if not is_light else "rgba(0, 0, 0, 0.05)"
        
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
        self.settings_btn.setIcon(svg_to_icon(ICONS["settings"], icon_color))
        self.close_btn.setIcon(svg_to_icon(ICONS["close"], icon_color))

    def setup_style(self):
        bg_color = "#1e1e1e"
        border_color = "#333333"
        btn_hover = "rgba(255, 255, 255, 0.08)"
        window_bg = ""
        
        if self.current_mode == "light":
            bg_color = "#f3f3f3"
            border_color = "#cccccc"
            btn_hover = "rgba(0, 0, 0, 0.05)"
        elif "acrylic" in self.current_mode:
            bg_color = "transparent"
            border_color = "rgba(255, 255, 255, 0.15)" if "dark" in self.current_mode else "rgba(0, 0, 0, 0.1)"
            btn_hover = "rgba(255, 255, 255, 0.08)" if "dark" in self.current_mode else "rgba(0, 0, 0, 0.03)"
        else:
            bg_color = "#1e1e1e"
            border_color = "#333333"
            btn_hover = "rgba(255, 255, 255, 0.08)"
            
        # Finalize the stylesheet
        style = f"""
            #LauncherWindow {{
                background: {bg_color if "acrylic" not in self.current_mode else "transparent"};
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
                background-color: {"rgba(0, 0, 0, 1)" if "acrylic" in self.current_mode else "transparent"};
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
        for s in shortcuts:
            item = ShortcutItem(s["path"], s["name"])
            item.deleted.connect(self._remove_shortcut)
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

    def _add_shortcut_path(self, path):
        path = os.path.normpath(path)
        if ConfigManager.add_shortcut(path):
            self.load_shortcuts()

    def _remove_shortcut(self, path):
        if ConfigManager.remove_shortcut(path):
            self.load_shortcuts()

    # Drag and Drop functionality
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self._add_shortcut_path(path)

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
            if not self.isActiveWindow() and not self._is_dialog_open:
                if self.isVisible() and self.windowOpacity() == 1.0:
                    self.hide_launcher()
        super().changeEvent(event)
