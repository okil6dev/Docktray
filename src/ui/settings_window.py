from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication

from qfluentwidgets import (FluentWindow, NavigationItemPosition, FluentIcon as FIF,
                            SettingCardGroup, SettingCard, ComboBox, Slider,
                            ScrollArea, ExpandLayout, qconfig, isDarkTheme)
from src.core.config_manager import ConfigManager

class ThemeInterface(ScrollArea):
    """ Theme settings interface """
    themeChanged = pyqtSignal(str)
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
        
        # Color scheme card
        self.themeCard = SettingCard(
            FIF.PALETTE,
            "Color Scheme",
            "Choose black, white, or acrylic background",
            self.themeGroup
        )
        self.comboBox = ComboBox(self.themeCard)
        self.comboBox.addItems(["dark", "light", "acrylic_dark", "acrylic_light"])
        self.comboBox.setFixedWidth(160)
        
        self.themeCard.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.themeCard.hBoxLayout.addSpacing(16)
        
        current_theme = ConfigManager.get_setting("theme", "dark")
        self.comboBox.setCurrentText(current_theme)
        
        self.themeGroup.addSettingCard(self.themeCard)
        
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
        
        # Acrylic opacity card
        self.acrylicCard = SettingCard(
            FIF.ALBUM,
            "Acrylic Opacity",
            "Adjust blur thickness when acrylic theme is active",
            self.themeGroup
        )
        self.acrylicSlider = Slider(Qt.Orientation.Horizontal, self.acrylicCard)
        self.acrylicSlider.setRange(1, 100)
        self.acrylicSlider.setFixedWidth(120)
        
        current_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
        self.acrylicSlider.setValue(current_opacity)
        self.acrylicSlider.setToolTip(f"Thickness: {current_opacity}%")
        
        self.acrylicCard.hBoxLayout.addWidget(self.acrylicSlider, 0, Qt.AlignmentFlag.AlignRight)
        self.acrylicCard.hBoxLayout.addSpacing(16)
        
        self.themeGroup.addSettingCard(self.acrylicCard)
        
        # Hide acrylic card by default; will be shown/hidden based on theme selection
        is_acrylic = "acrylic" in current_theme
        self.acrylicCard.setVisible(is_acrylic)
        
        self.expand_layout.addWidget(self.themeGroup)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.comboBox.currentTextChanged.connect(self._on_theme_combo_changed)
        self.comboBox.currentTextChanged.connect(self.themeChanged.emit)
        self.iconComboBox.currentTextChanged.connect(self._on_icon_color_changed)
        self.acrylicSlider.valueChanged.connect(self._on_acrylic_opacity_changed)
        self.acrylicSlider.sliderMoved.connect(self._on_acrylic_opacity_changed)
        
        # Make scroll area transparent (done once, QFluentWidgets theme engine manages the rest)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")

    def _on_icon_color_changed(self, color):
        ConfigManager.set_setting("icon_color", color)
        self.iconColorChanged.emit(color)

    def _on_theme_combo_changed(self, theme):
        """Show/hide acrylic opacity card based on whether an acrylic theme is selected"""
        is_acrylic = "acrylic" in theme
        self.acrylicCard.setVisible(is_acrylic)

    def _on_acrylic_opacity_changed(self, value):
        """Update slider tooltip and emit signal"""
        self.acrylicSlider.setToolTip(f"Thickness: {value}%")
        ConfigManager.set_setting("acrylic_opacity", value)
        self.acrylicOpacityChanged.emit(value)


class PositionInterface(ScrollArea):
    """ Positioning settings interface """
    positionChanged = pyqtSignal(str)

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
        self.expand_layout.addWidget(self.posGroup)

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.posComboBox.currentTextChanged.connect(self._on_pos_changed)
        
        # Make scroll area transparent (done once, QFluentWidgets theme engine manages the rest)
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.view.setStyleSheet("background: transparent;")

    def _on_pos_changed(self, pos):
        ConfigManager.set_setting("taskbar_position", pos)
        self.positionChanged.emit(pos)


class SettingsWindow(FluentWindow):
    """ Main settings window """
    themeChanged = pyqtSignal(str)
    iconColorChanged = pyqtSignal(str)
    acrylicOpacityChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(str)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("DockTray Settings")
        self.setWindowIcon(FIF.SETTING.icon())
        
        # Create sub-interfaces
        self.themeInterface = ThemeInterface(self)
        self.positionInterface = PositionInterface(self)
        
        # Add to navigation
        self.addSubInterface(self.themeInterface, FIF.PALETTE, "Themes")
        self.addSubInterface(self.positionInterface, FIF.MOVE, "Positioning")
        
        # Connect internal signals to external
        self.themeInterface.themeChanged.connect(self.themeChanged.emit)
        self.themeInterface.themeChanged.connect(self._apply_qfluent_theme)
        self.themeInterface.iconColorChanged.connect(self.iconColorChanged.emit)
        self.themeInterface.acrylicOpacityChanged.connect(self.acrylicOpacityChanged.emit)
        self.positionInterface.positionChanged.connect(self.positionChanged.emit)
        
        # Window size
        self.resize(700, 550)
        
        # Center on primary screen
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen_geo.center().x() - self.width() // 2,
            screen_geo.center().y() - self.height() // 2
        )

    def _apply_qfluent_theme(self, mode):
        """Update QFluentWidgets theme and acrylic effect based on selected mode"""
        # Update QFluentWidgets theme
        if "dark" in mode:
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[1])
        else:
            qconfig.set(qconfig.themeMode, qconfig.themeMode.options[0])
        
        # Always remove any existing background effect first
        self.windowEffect.removeBackgroundEffect(self.winId())
        
        if "acrylic" in mode:
            # Window background must be transparent for acrylic blur to show through
            self.setStyleSheet("FluentWindow { background: transparent; }")
            # Apply acrylic blur with saved opacity
            saved_opacity = ConfigManager.get_setting("acrylic_opacity", 10)
            opacity = max(1, min(255, int(saved_opacity * 2.55)))
            alpha = f"{opacity:02x}"
            color = f"202020{alpha}" if "dark" in mode else f"F2F2F2{alpha}"
            self.windowEffect.setAcrylicEffect(self.winId(), color)
        else:
            # Set solid background matching the theme
            bg = "#1e1e1e" if "dark" in mode else "#f3f3f3"
            self.setStyleSheet(f"FluentWindow {{ background: {bg}; }}")

    def showEvent(self, event):
        super().showEvent(event)
        # Apply current theme from config on first show to override default acrylic
        current_theme = ConfigManager.get_setting("theme", "dark")
        self._apply_qfluent_theme(current_theme)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
