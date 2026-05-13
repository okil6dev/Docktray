import os
import sys
import json
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QFileDialog, QMessageBox

from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF,
                            SettingCardGroup, SettingCard, ComboBox, Slider, CheckBox,
                            ScrollArea, ExpandLayout, qconfig, isDarkTheme, SwitchButton)
from src.core.config_manager import ConfigManager
from src.core.startup_manager import StartupManager

# Determine base path (works for dev and PyInstaller builds)
if hasattr(sys, '_MEIPASS'):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    return os.path.join(BASE_PATH, relative_path)


def load_settings_icon():
    """Load the settings icon from file, or return None if unavailable"""
    icon_path = get_resource_path("icons/settings_icon/icon.ico")
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        # Also try to load from PNG for better compatibility
        png_path = get_resource_path("icons/settings_icon/icon_32x32.png")
        if os.path.exists(png_path) and icon.isNull():
            icon = QIcon(QPixmap(png_path))
        if not icon.isNull():
            return icon
    # Fallback: try PNG directly
    png_path = get_resource_path("icons/settings_icon/icon_256x256.png")
    if os.path.exists(png_path):
        return QIcon(QPixmap(png_path))
    return None


def load_settings_icon_pixmap(size=32):
    """Load a specific size settings icon as QPixmap"""
    png_path = get_resource_path(f"icons/settings_icon/icon_{size}x{size}.png")
    if os.path.exists(png_path):
        return QPixmap(png_path)
    # Try .ico as fallback
    icon_path = get_resource_path("icons/settings_icon/icon.ico")
    if os.path.exists(icon_path):
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return QPixmap()
# Try to import win32 API for Windows-specific taskbar handling
try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class GeneralInterface(ScrollArea):
    """ General settings interface - startup, etc. """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.expand_layout = ExpandLayout(self.view)

        self.setObjectName("GeneralInterface")
        self.view.setObjectName("GeneralInterfaceView")

        self.generalGroup = SettingCardGroup("General", self.view)

        # Startup card
        self.startupCard = SettingCard(
            FIF.SETTING,
            "Start on Startup",
            "Automatically start DockTray when you log in to Windows",
            self.generalGroup
        )
        self.startupSwitch = SwitchButton(self.startupCard)
        self.startupSwitch.setChecked(StartupManager.is_startup_enabled())
        self.startupSwitch.checkedChanged.connect(StartupManager.set_startup)

        self.startupCard.hBoxLayout.addWidget(self.startupSwitch, 0, Qt.AlignmentFlag.AlignRight)
        self.startupCard.hBoxLayout.addSpacing(16)

        self.generalGroup.addSettingCard(self.startupCard)
        self.expand_layout.addWidget(self.generalGroup)

        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")


class ThemeInterface(ScrollArea):
    """ Theme settings interface - solid black/white or acrylic with whiteness slider """
    themeModeChanged = pyqtSignal(str)
    whitenessChanged = pyqtSignal(int)
    iconColorChanged = pyqtSignal(str)
    acrylicOpacityChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.expand_layout = ExpandLayout(self.view)

        self.setObjectName("ThemeInterface")
        self.view.setObjectName("ThemeInterfaceView")

        # Theme group
        self.themeGroup = SettingCardGroup("Appearance", self.view)

        # Theme mode card - choose Black, White, or Acrylic
        self.themeModeCard = SettingCard(
            FIF.PALETTE,
            "Theme Mode",
            "Choose Black (no acrylic), White (no acrylic), or Acrylic",
            self.themeGroup
        )
        self.themeModeCombo = ComboBox(self.themeModeCard)
        self.themeModeCombo.addItems(["Black (No Acrylic)", "White (No Acrylic)", "Acrylic"])
        self.themeModeCombo.setFixedWidth(180)

        self.themeModeCard.hBoxLayout.addWidget(self.themeModeCombo, 0, Qt.AlignmentFlag.AlignRight)
        self.themeModeCard.hBoxLayout.addSpacing(16)

        current_mode = ConfigManager.get_setting("theme_mode", "acrylic")
        # Map old theme values to new modes for backwards compatibility
        if current_mode not in ["black", "white", "acrylic"]:
            if current_mode in ["dark", "light", "acrylic_dark", "acrylic_light"]:
                current_mode = "acrylic"
            else:
                current_mode = "acrylic"
        display_text = {"black": "Black (No Acrylic)", "white": "White (No Acrylic)", "acrylic": "Acrylic"}
        self.themeModeCombo.setCurrentText(display_text.get(current_mode, "Acrylic"))
        self._current_mode = current_mode

        self.themeGroup.addSettingCard(self.themeModeCard)

        # Whiteness slider card (only visible in Acrylic mode)
        self.whitenessCard = SettingCard(
            FIF.PALETTE,
            "Theme Whiteness",
            "Slide left for dark acrylic, right for light acrylic. Click Apply to confirm.",
            self.themeGroup
        )
        self.whitenessSlider = Slider(Qt.Orientation.Horizontal, self.whitenessCard)
        self.whitenessSlider.setRange(0, 100)
        self.whitenessSlider.setFixedWidth(120)

        self.whitenessValueLabel = QLabel("0%", self.whitenessCard)
        self.whitenessValueLabel.setFixedWidth(40)
        self.whitenessValueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.whitenessApplyBtn = QPushButton("Apply", self.whitenessCard)
        self.whitenessApplyBtn.setFixedWidth(80)

        self.whitenessResetBtn = QPushButton("Reset", self.whitenessCard)
        self.whitenessResetBtn.setFixedWidth(80)

        current_whiteness = ConfigManager.get_setting("theme_whiteness", 0)
        self._pending_whiteness = current_whiteness
        self.whitenessSlider.setValue(current_whiteness)
        self.whitenessValueLabel.setText(f"{current_whiteness}%")

        self.whitenessCard.hBoxLayout.addWidget(self.whitenessSlider, 0, Qt.AlignmentFlag.AlignRight)
        self.whitenessCard.hBoxLayout.addSpacing(8)
        self.whitenessCard.hBoxLayout.addWidget(self.whitenessValueLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.whitenessCard.hBoxLayout.addSpacing(8)
        self.whitenessCard.hBoxLayout.addWidget(self.whitenessApplyBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.whitenessCard.hBoxLayout.addSpacing(8)
        self.whitenessCard.hBoxLayout.addWidget(self.whitenessResetBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.whitenessCard.hBoxLayout.addSpacing(16)

        self.themeGroup.addSettingCard(self.whitenessCard)

        # Update visibility based on current mode
        is_acrylic = current_mode == "acrylic"
        self.whitenessCard.setVisible(is_acrylic)

        # Icon color card
        self.iconCard = SettingCard(
            FIF.BRUSH,
            "Icon Color",
            "Choose white or black icons",
            self.themeGroup
        )
        self.iconComboBox = ComboBox(self.iconCard)
        self.iconComboBox.addItems(["white", "black"])
        self.iconComboBox.setFixedWidth(160)

        self.iconCard.hBoxLayout.addWidget(self.iconComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.iconCard.hBoxLayout.addSpacing(16)

        current_icon_color = ConfigManager.get_setting("icon_color", "white")
        self.iconComboBox.setCurrentText(current_icon_color)

        self.themeGroup.addSettingCard(self.iconCard)

        self.expand_layout.addWidget(self.themeGroup)

        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # Connections
        self.themeModeCombo.currentTextChanged.connect(self._on_theme_mode_changed)
        self.whitenessSlider.valueChanged.connect(self._on_whiteness_slider_changed)
        self.whitenessSlider.sliderMoved.connect(self._on_whiteness_slider_changed)
        self.whitenessApplyBtn.clicked.connect(self._on_whiteness_apply)
        self.whitenessResetBtn.clicked.connect(self._on_whiteness_reset)
        self.iconComboBox.currentTextChanged.connect(self._on_icon_color_changed)

        # Button styling
        action_btn_style = """
            QPushButton {
                padding: 4px 10px;
                text-align: center;
            }
        """
        self.whitenessApplyBtn.setStyleSheet(action_btn_style)
        self.whitenessResetBtn.setStyleSheet(action_btn_style)

        # Make scroll area transparent
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")

    def _on_theme_mode_changed(self, text):
        """Show/hide acrylic controls based on selected mode, emit signal"""
        mode_map = {"Black (No Acrylic)": "black", "White (No Acrylic)": "white", "Acrylic": "acrylic"}
        mode = mode_map.get(text, "acrylic")
        self._current_mode = mode
        ConfigManager.set_setting("theme_mode", mode)

        is_acrylic = mode == "acrylic"
        self.whitenessCard.setVisible(is_acrylic)

        self.themeModeChanged.emit(mode)

    def _on_whiteness_slider_changed(self, value):
        self._pending_whiteness = value
        self.whitenessValueLabel.setText(f"{value}%")

    def _on_whiteness_apply(self):
        ConfigManager.set_setting("theme_whiteness", self._pending_whiteness)
        self.whitenessChanged.emit(self._pending_whiteness)

    def _on_whiteness_reset(self):
        self.whitenessSlider.setValue(0)
        self._pending_whiteness = 0
        self.whitenessValueLabel.setText("0%")
        ConfigManager.set_setting("theme_whiteness", 0)
        self.whitenessChanged.emit(0)

    def _on_icon_color_changed(self, color):
        ConfigManager.set_setting("icon_color", color)
        self.iconColorChanged.emit(color)

    def _on_acrylic_opacity_changed(self, value):
        ConfigManager.set_setting("acrylic_opacity", value)
        self.acrylicOpacityChanged.emit(value)


class PositionInterface(ScrollArea):
    """ Positioning settings interface """
    positionChanged = pyqtSignal(str)
    iconSizeChanged = pyqtSignal(int)
    buttonSizeChanged = pyqtSignal(int)
    traySizeEditRequested = pyqtSignal()
    traySizeResetRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.expand_layout = ExpandLayout(self.view)

        self.setObjectName("PositionInterface")
        self.view.setObjectName("PositionInterfaceView")

        self.posGroup = SettingCardGroup("Taskbar & Positioning", self.view)

        self.positionCard = SettingCard(
            FIF.MOVE,
            "Taskbar Position",
            "Align the launcher based on your taskbar location",
            self.posGroup
        )
        self.posComboBox = ComboBox(self.positionCard)
        self.posComboBox.addItems([
            "Bottom Taskbar",
            "Top Taskbar",
            "Left Taskbar (Vertical)",
            "Right Taskbar (Vertical)"
        ])
        self.posComboBox.setFixedWidth(200)

        self.positionCard.hBoxLayout.addWidget(self.posComboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.positionCard.hBoxLayout.addSpacing(16)

        current_pos = ConfigManager.get_setting("taskbar_position", "Bottom Taskbar")
        self.posComboBox.setCurrentText(current_pos)

        self.posGroup.addSettingCard(self.positionCard)

        self.iconSizeCard = SettingCard(
            FIF.ZOOM,
            "Icon Size",
            "Adjust shortcut icon size in the launcher",
            self.posGroup
        )
        self.iconSizeSlider = Slider(Qt.Orientation.Horizontal, self.iconSizeCard)
        self.iconSizeSlider.setRange(28, 72)
        self.iconSizeSlider.setFixedWidth(140)
        current_icon_size = ConfigManager.get_setting("shortcut_icon_size", 45)
        self.iconSizeSlider.setValue(int(current_icon_size))

        self.iconSizeValueLabel = QLabel(f"{int(current_icon_size)} px", self.iconSizeCard)
        self.iconSizeValueLabel.setFixedWidth(52)
        self.iconSizeValueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.iconSizeCard.hBoxLayout.addWidget(self.iconSizeSlider, 0, Qt.AlignmentFlag.AlignRight)
        self.iconSizeCard.hBoxLayout.addSpacing(8)
        self.iconSizeCard.hBoxLayout.addWidget(self.iconSizeValueLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.iconSizeResetBtn = QPushButton("Reset", self.iconSizeCard)
        self.iconSizeResetBtn.setFixedWidth(80)
        self.iconSizeCard.hBoxLayout.addSpacing(8)
        self.iconSizeCard.hBoxLayout.addWidget(self.iconSizeResetBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.iconSizeCard.hBoxLayout.addSpacing(16)

        self.posGroup.addSettingCard(self.iconSizeCard)

        self.buttonSizeCard = SettingCard(
            FIF.LAYOUT,
            "Button Size",
            "Adjust bottom bar button size",
            self.posGroup
        )
        self.buttonSizeSlider = Slider(Qt.Orientation.Horizontal, self.buttonSizeCard)
        self.buttonSizeSlider.setRange(32, 56)
        self.buttonSizeSlider.setFixedWidth(140)
        current_button_size = int(ConfigManager.get_setting("launcher_button_size", 40))
        self.buttonSizeSlider.setValue(current_button_size)

        self.buttonSizeValueLabel = QLabel(f"{current_button_size} px", self.buttonSizeCard)
        self.buttonSizeValueLabel.setFixedWidth(52)
        self.buttonSizeValueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.buttonSizeCard.hBoxLayout.addWidget(self.buttonSizeSlider, 0, Qt.AlignmentFlag.AlignRight)
        self.buttonSizeCard.hBoxLayout.addSpacing(8)
        self.buttonSizeCard.hBoxLayout.addWidget(self.buttonSizeValueLabel, 0, Qt.AlignmentFlag.AlignRight)
        self.buttonSizeResetBtn = QPushButton("Reset", self.buttonSizeCard)
        self.buttonSizeResetBtn.setFixedWidth(80)
        self.buttonSizeCard.hBoxLayout.addSpacing(8)
        self.buttonSizeCard.hBoxLayout.addWidget(self.buttonSizeResetBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.buttonSizeCard.hBoxLayout.addSpacing(16)
        self.posGroup.addSettingCard(self.buttonSizeCard)

        self.traySizeCard = SettingCard(
            FIF.ZOOM,
            "Tray Size",
            "Drag the launcher corner handle, then click Apply.",
            self.posGroup
        )
        self.traySizeBtn = QPushButton("Resize Tray", self.traySizeCard)
        self.traySizeBtn.setFixedWidth(132)
        self.traySizeResetBtn = QPushButton("Reset", self.traySizeCard)
        self.traySizeResetBtn.setFixedWidth(80)
        self.traySizeCard.hBoxLayout.addWidget(self.traySizeBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.traySizeCard.hBoxLayout.addSpacing(8)
        self.traySizeCard.hBoxLayout.addWidget(self.traySizeResetBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.traySizeCard.hBoxLayout.addSpacing(16)
        self.posGroup.addSettingCard(self.traySizeCard)
        self.expand_layout.addWidget(self.posGroup)

        action_btn_style = """
            QPushButton {
                padding: 4px 10px;
                text-align: center;
            }
        """
        self.iconSizeResetBtn.setStyleSheet(action_btn_style)
        self.buttonSizeResetBtn.setStyleSheet(action_btn_style)
        self.traySizeBtn.setStyleSheet(action_btn_style)
        self.traySizeResetBtn.setStyleSheet(action_btn_style)

        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.posComboBox.currentTextChanged.connect(self._on_pos_changed)
        self.iconSizeSlider.valueChanged.connect(self._on_icon_size_changed)
        self.buttonSizeSlider.valueChanged.connect(self._on_button_size_changed)
        self.iconSizeResetBtn.clicked.connect(self._reset_icon_size)
        self.buttonSizeResetBtn.clicked.connect(self._reset_button_size)
        self.traySizeBtn.clicked.connect(self.traySizeEditRequested.emit)
        self.traySizeResetBtn.clicked.connect(self._reset_tray_size)

        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")

    def _on_pos_changed(self, pos):
        ConfigManager.set_setting("taskbar_position", pos)
        self.positionChanged.emit(pos)

    def _on_icon_size_changed(self, value):
        value = int(value)
        self.iconSizeValueLabel.setText(f"{value} px")
        ConfigManager.set_setting("shortcut_icon_size", value)
        self.iconSizeChanged.emit(value)

    def _on_button_size_changed(self, value):
        value = int(value)
        self.buttonSizeValueLabel.setText(f"{value} px")
        ConfigManager.set_setting("launcher_button_size", value)
        self.buttonSizeChanged.emit(value)

    def _reset_icon_size(self):
        self.iconSizeSlider.setValue(45)

    def _reset_button_size(self):
        self.buttonSizeSlider.setValue(40)

    def _reset_tray_size(self):
        ConfigManager.set_setting("tray_width", 400)
        ConfigManager.set_setting("tray_height", 250)
        self.traySizeResetRequested.emit()


class ExportInterface(ScrollArea):
    """ Export/Backup settings interface """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.expand_layout = ExpandLayout(self.view)

        self.setObjectName("ExportInterface")
        self.view.setObjectName("ExportInterfaceView")

        self.exportGroup = SettingCardGroup("Export Data", self.view)

        # Export settings card
        self.exportSettingsCard = SettingCard(
            FIF.SETTING,
            "Export Settings",
            "Save your app settings (theme, positions, etc.) to a JSON file",
            self.exportGroup
        )
        self.exportSettingsBtn = QPushButton("Export Settings", self.exportSettingsCard)
        self.exportSettingsBtn.setFixedWidth(132)
        self.exportSettingsCard.hBoxLayout.addWidget(self.exportSettingsBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.exportSettingsCard.hBoxLayout.addSpacing(16)
        self.exportGroup.addSettingCard(self.exportSettingsCard)

        # Export shortcuts card
        self.exportShortcutsCard = SettingCard(
            FIF.APPLICATION,
            "Export Shortcuts",
            "Save your launcher shortcuts to a JSON file",
            self.exportGroup
        )
        self.exportShortcutsBtn = QPushButton("Export Shortcuts", self.exportShortcutsCard)
        self.exportShortcutsBtn.setFixedWidth(132)
        self.exportShortcutsCard.hBoxLayout.addWidget(self.exportShortcutsBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.exportShortcutsCard.hBoxLayout.addSpacing(16)
        self.exportGroup.addSettingCard(self.exportShortcutsCard)

        # Export both card
        self.exportBothCard = SettingCard(
            FIF.SAVE,
            "Export All (Backup)",
            "Save both settings and shortcuts to a single JSON file",
            self.exportGroup
        )
        self.exportBothBtn = QPushButton("Export All", self.exportBothCard)
        self.exportBothBtn.setFixedWidth(132)
        self.exportBothCard.hBoxLayout.addWidget(self.exportBothBtn, 0, Qt.AlignmentFlag.AlignRight)
        self.exportBothCard.hBoxLayout.addSpacing(16)
        self.exportGroup.addSettingCard(self.exportBothCard)

        self.expand_layout.addWidget(self.exportGroup)

        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # Connections
        self.exportSettingsBtn.clicked.connect(self._export_settings)
        self.exportShortcutsBtn.clicked.connect(self._export_shortcuts)
        self.exportBothBtn.clicked.connect(self._export_both)

        action_btn_style = """
            QPushButton {
                padding: 4px 10px;
                text-align: center;
            }
        """
        self.exportSettingsBtn.setStyleSheet(action_btn_style)
        self.exportShortcutsBtn.setStyleSheet(action_btn_style)
        self.exportBothBtn.setStyleSheet(action_btn_style)

        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")

    def _export_settings(self):
        """Export only settings portion of config.json"""
        config = ConfigManager._load_full_config()
        settings = config.get("settings", {})

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "docktray_settings.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"settings": settings}, f, indent=4)
            QMessageBox.information(self, "Success", f"Settings exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export settings:\n{e}")

    def _export_shortcuts(self):
        """Export only shortcuts from config.json"""
        shortcuts = ConfigManager.load_shortcuts()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Shortcuts", "docktray_shortcuts.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"shortcuts": shortcuts}, f, indent=4)
            QMessageBox.information(self, "Success", f"Shortcuts exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export shortcuts:\n{e}")

    def _export_both(self):
        """Export full config (settings + shortcuts) as backup"""
        config = ConfigManager._load_full_config()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All (Backup)", "docktray_backup.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Success", f"Full backup exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export backup:\n{e}")


class SettingsWindow(FluentWindow):
    """ Main settings window """
    themeModeChanged = pyqtSignal(str)
    whitenessChanged = pyqtSignal(int)
    iconColorChanged = pyqtSignal(str)
    acrylicOpacityChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(str)
    iconSizeChanged = pyqtSignal(int)
    buttonSizeChanged = pyqtSignal(int)
    traySizeEditRequested = pyqtSignal()
    traySizeResetRequested = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("DockTray Settings")

        # Pre-load icon reference for reuse
        self._settings_icon = load_settings_icon()
        if self._settings_icon is None or self._settings_icon.isNull():
            self._settings_icon = FIF.SETTING.icon()

        self.generalInterface = GeneralInterface(self)
        self.themeInterface = ThemeInterface(self)
        self.positionInterface = PositionInterface(self)
        self.exportInterface = ExportInterface(self)

        self.addSubInterface(self.themeInterface, FIF.PALETTE, "Themes")
        self.addSubInterface(self.generalInterface, FIF.SETTING, "General")
        self.addSubInterface(self.positionInterface, FIF.MOVE, "Positioning")
        self.addSubInterface(self.exportInterface, FIF.SAVE, "Exporting")

        # Set icon AFTER addSubInterface to prevent FluentWindow from overriding it
        self.setWindowIcon(self._settings_icon)

        # Also set the application icon so the taskbar displays it correctly
        QApplication.setWindowIcon(self._settings_icon)

        self.themeInterface.themeModeChanged.connect(self.themeModeChanged.emit)
        self.themeInterface.whitenessChanged.connect(self.whitenessChanged.emit)
        self.themeInterface.iconColorChanged.connect(self.iconColorChanged.emit)
        self.themeInterface.acrylicOpacityChanged.connect(self.acrylicOpacityChanged.emit)
        self.positionInterface.positionChanged.connect(self.positionChanged.emit)
        self.positionInterface.iconSizeChanged.connect(self.iconSizeChanged.emit)
        self.positionInterface.buttonSizeChanged.connect(self.buttonSizeChanged.emit)
        self.positionInterface.traySizeEditRequested.connect(self.traySizeEditRequested.emit)
        self.positionInterface.traySizeResetRequested.connect(self.traySizeResetRequested.emit)

        # Also connect theme mode changes to update the settings window theme
        self.themeInterface.themeModeChanged.connect(self._apply_settings_theme)

        self.resize(700, 550)

        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen_geo.center().x() - self.width() // 2,
            screen_geo.center().y() - self.height() // 2
        )

        # Use a timer to call win32 API after the window is fully created
        if WIN32_AVAILABLE:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._force_taskbar_visibility)


    def _force_taskbar_visibility(self):
        """Force the window to appear in the Windows taskbar using win32 API"""
        if not WIN32_AVAILABLE:
            return

        try:
            from PyQt6.QtCore import QTimer

            hwnd = int(self.winId())
            if hwnd == 0:
                # Window not created yet, retry later
                QTimer.singleShot(100, self._force_taskbar_visibility)
                return

            # Get current extended window style
            current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            # Remove tool window style (prevents taskbar icon)
            new_style = current_style & ~win32con.WS_EX_TOOLWINDOW

            # Add app window style (forces taskbar icon)
            new_style |= win32con.WS_EX_APPWINDOW

            # Apply the new style
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)

            # Remove WS_EX_NOACTIVATE if present (prevents Alt+Tab)
            new_style = new_style & ~win32con.WS_EX_NOACTIVATE
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)

            # Force window to show in taskbar by showing and hiding it
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            # Load the icon using win32 API to ensure taskbar shows it
            # Try .ico first (for taskbar), then PNG as fallback
            settings_icon_path = get_resource_path("icons/settings_icon/icon.ico")
            if not os.path.exists(settings_icon_path):
                # Fallback to 32x32 PNG if .ico doesn't exist
                settings_icon_path = get_resource_path("icons/settings_icon/icon_32x32.png")
            if os.path.exists(settings_icon_path):
                try:
                    if settings_icon_path.lower().endswith('.ico'):
                        # Load large icon (32x32 for taskbar) and small icon (16x16 for title bar)
                        large_icon = win32gui.LoadImage(0, settings_icon_path, win32con.IMAGE_ICON, 32, 32, win32con.LR_LOADFROMFILE)
                        small_icon = win32gui.LoadImage(0, settings_icon_path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE)
                    else:
                        # For PNG, load as image and use as icon
                        large_icon = win32gui.LoadImage(0, settings_icon_path, win32con.IMAGE_BITMAP, 32, 32, win32con.LR_LOADFROMFILE)
                        small_icon = win32gui.LoadImage(0, settings_icon_path, win32con.IMAGE_BITMAP, 16, 16, win32con.LR_LOADFROMFILE)
                    if large_icon:
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, large_icon)
                        # Also change the window class icon (affects taskbar)
                        win32gui.SetClassLong(hwnd, win32con.GCL_HICON, large_icon)
                    if small_icon:
                        win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, small_icon)
                        win32gui.SetClassLong(hwnd, win32con.GCL_HICONSM, small_icon)
                except Exception:
                    pass

        except Exception:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(200, self._force_taskbar_visibility)


    def showEvent(self, event):
        super().showEvent(event)
        # Apply theme from config on first show
        current_mode = ConfigManager.get_setting("theme_mode", "acrylic")
        self._apply_settings_theme(current_mode)

        # Re-apply the icon every time the window is shown (FluentWindow may override it)
        self.setWindowIcon(self._settings_icon)

        # Also force taskbar visibility on show (in case it wasn't applied yet)
        if WIN32_AVAILABLE:
            QTimer.singleShot(0, self._force_taskbar_visibility)

    def _apply_settings_theme(self, mode):
        """Apply acrylic or solid background to settings window based on mode"""
        self.windowEffect.removeBackgroundEffect(self.winId())

        if mode == "acrylic":
            is_dark = ConfigManager.get_setting("theme_whiteness", 0) < 50
            # Acrylic mode - apply acrylic effect
            self.setStyleSheet("FluentWindow { background: transparent; }")
            whiteness = ConfigManager.get_setting("theme_whiteness", 0)
            ratio = whiteness / 100.0
            r = int(0x20 + (0xFF - 0x20) * ratio)
            g = int(0x20 + (0xFF - 0x20) * ratio)
            b = int(0x20 + (0xFF - 0x20) * ratio)
            base_color = f"{r:02x}{g:02x}{b:02x}"
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
            opacity = max(1, min(255, int(saved_opacity * 2.55)))
            alpha = f"{opacity:02x}"
            color = f"{base_color}{alpha}"

            # Apply acrylic effect with or without overlay based on setting
            disable_overlay = ConfigManager.get_setting("disable_acrylic_overlay", False)
            if disable_overlay:
                # Use absolute default acrylic effect (no color overlay)
                self.windowEffect.setAcrylicEffect(self.winId(), "00000000")
            else:
                # Use the colored overlay
                self.windowEffect.setAcrylicEffect(self.winId(), color)

            if is_dark:
                text = "#F2F2F2"
                card_bg = "rgba(22, 22, 22, 0.62)"
                border = "rgba(255, 255, 255, 0.18)"
            else:
                text = "#1F1F1F"
                card_bg = "rgba(255, 255, 255, 0.74)"
                border = "rgba(0, 0, 0, 0.12)"
        else:
            # For non-acrylic modes (black/white), remove acrylic effect completely
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1 if mode == "black" else 0])

            if mode == "black":
                # Solid dark mode - no acrylic effect
                self.setStyleSheet("FluentWindow { background: #1e1e1e; }")
                text = "#F2F2F2"
                card_bg = "#2d2d2d"
                border = "#444444"
            else:  # white
                # Solid light mode - no acrylic effect
                self.setStyleSheet("FluentWindow { background: #f3f3f3; }")
                text = "#1F1F1F"
                card_bg = "#ffffff"
                border = "#cccccc"

        self.setStyleSheet(f"""
            FluentWindow {{ background: transparent; }}
            FluentWindow {{
                background: {"transparent" if mode == "acrylic" else ("#1e1e1e" if mode == "black" else "#f3f3f3")};
            }}
            QLabel {{ color: {text}; }}
            QPushButton {{ color: {text}; }}
            SettingCard, SettingCardGroup {{
                background: {card_bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QComboBox, Slider {{
                color: {text};
            }}
        """)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)