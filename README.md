# DockTray

A lightweight, translucent **launcher & quick-access dock** for Windows, built with PyQt6 and the Fluent design system. DockTray lives in your system tray and pops a glassy acrylic panel of your favourite apps, files, folders, UWP / Microsoft Store apps, and Start-menu apps — all just a click away.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="PyQt6" src="https://img.shields.io/badge/PyQt6-6.5%2B-41CD52?logo=qt&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-CC0%201.0-lightgrey">
  <img alt="Build" src="https://img.shields.io/badge/Build-PyInstaller-orange?logo=python&logoColor=white">
</p>

---

## Features

### Core Launcher
- **System-tray resident** — click the tray icon to toggle the launcher window; right-click for an Exit menu.
- **Animated show / hide** — slides in from the correct edge of the screen and fades in/out smoothly.
- **Adaptive positioning** — automatically anchors to the corner that matches your Windows taskbar position (Bottom, Top, Left, Right).
- **Live resize mode** — drag the corner handle to make the launcher any size you like, then click **Apply**. A **Reset** button restores the default `400 x 250` size.
- **Auto-hide on focus loss** — disappears when you click away (configurable behaviour for drag mode and dialogs).
- **Tray context menu** with an **Exit DockTray** action.

### Themes & Appearance
Three theme modes, switchable on the fly from the **Themes** settings page:

| Mode | Description |
|---|---|
| **Black** (no acrylic) | Solid dark surface — `#1e1e1e`. Fastest, lowest CPU. |
| **White** (no acrylic) | Solid light surface — `#f3f3f3`. |
| **Acrylic** | True Windows **acrylic blur** behind the launcher, with a **whiteness slider (0 to 100 %)**. Drag it left for a dark, glassy look; drag it right for a frosted / milky look. Includes an **Apply** and **Reset** button. |

Additional appearance controls:
- **Icon color** — switch bottom-bar icons between white and black to match the theme.
- **Adjustable acrylic translucency** — the container background and overlay are tuned for maximum see-through without sacrificing readability.
- **Real-time updates** — every change is applied instantly; no restart required.

### Shortcuts
- **Multiple target types**:
  - **Files & executables** — any file path; launches via `os.startfile`.
  - **Folders** — opens in Explorer.
  - **UWP / Microsoft Store apps** — supported via the `uwp:` prefix; resolves the app's real package logo from its `AppxManifest.xml` and falls back to the AppsFolder shell icon.
  - **Start-menu apps** — supported via the `startapp:` prefix (full AUMID `PackageFamily!AppId`); launches through `shell:AppsFolder\<AUMID>` so it works for both real Store apps and classic Start-menu shortcuts.
- **High-quality icon extraction**:
  - Reads embedded `HICON` resources via the Windows Shell API (`SHGetFileInfoW`).
  - For UWP / Start apps, walks the Appx manifest to find the best-matching `Square44x44Logo`, `Square150x150Logo`, or `targetsize-*` variant — preferring unplated tiles for crispness.
  - Uses `QImage.fromHICON` and smooth `QPixmap.scaled` for pixel-perfect results.
- **De-duplication** — adding the same shortcut twice is a silent no-op.
- **Hover delete** — hover any shortcut to reveal a small trash button; click to remove.
- **Right-click menu** for per-item customisation:
  - **Set Custom Name...** — override the display name. Leave blank or pick the original to reset.
  - **Set Custom Icon...** — pick any `.png`, `.ico`, `.jpg`, `.bmp`, `.gif`, or `.webp` file to use as the icon.
  - **Reset Custom Name / Reset Custom Icon** — clear the override and fall back to the original.
  - **Delete** — remove the shortcut (any custom data is wiped at the same time).
  - A small blue **C** badge appears in the bottom-right of the tile while any custom data is active.
- **Single-click launch** with a click cursor, plus a fallback "?" / "UWP" badge when an icon cannot be resolved.
- **Custom icon size** — slider from **28 px to 72 px**, with tile geometry scaling proportionally.
- **Custom bottom-bar button size** — slider from **32 px to 56 px**, icons scale automatically.

### Adding Shortcuts
- **Add File** — pick any file or executable.
- **Add Folder** — pick any folder.
- **Add Window Apps** — browse your installed Start-menu apps; pre-resolved with names from `Get-StartApps`.
- **Drag & Drop mode** — toggle Drag Mode, then **drop files / folders / apps directly onto the launcher** to add them.

### Settings
A polished **FluentWindow** (qfluentwidgets) with four sub-pages, accessible from the **Settings** button in the bottom bar:

| Page | What it does |
|---|---|
| **Themes** | Theme mode (Black / White / Acrylic), whiteness slider with Apply/Reset, icon color picker. |
| **General** | **Start on Startup** toggle — creates / removes a `DockTray.lnk` in the Windows Startup folder. |
| **Positioning** | Taskbar position, shortcut icon size + Reset, bottom button size + Reset, **Resize Tray** button (drag-corner mode), **Reset** tray size. |
| **Exporting** | Export **Settings**, **Shortcuts**, or **All (Backup)** to a JSON file via the standard Save dialog. |

Settings persist to `config.json` in the working directory, and changes propagate live to the launcher.

### Taskbar / Window Behaviour
- The settings window forces itself into the **Windows taskbar / Alt-Tab list** using the `win32gui` extended-style trick (`WS_EX_APPWINDOW`), so it doesn't behave like a hidden tool window.
- The launcher itself is a `Tool` window that stays on top, so it floats above other apps when summoned.
- Proper `AppUserModelID` (`DockTray.Launcher.1`) is set at startup so the taskbar shows the right icon and grouping.

### Configuration & Data
All state is stored in plain JSON in `config.json` next to the executable:

```json
{
  "shortcuts": [
    { "path": "C:\\Windows\\explorer.exe", "name": "Explorer" },
    { "path": "startapp:Microsoft.WindowsCalculator_8wekyb3d8bbwe!App", "name": "Calculator" }
  ],
  "settings": {
    "theme_mode": "acrylic",
    "theme_whiteness": 100,
    "icon_color": "white",
    "acrylic_opacity": 10,
    "disable_acrylic_overlay": false,
    "tray_width": 457,
    "tray_height": 336,
    "shortcut_icon_size": 45,
    "launcher_button_size": 40,
    "taskbar_position": "Bottom Taskbar"
  }
}
```

Use the **Exporting** tab in Settings to back this up before reinstalling or moving machines.

---

## Installation

### Option 1 — Run from source
Requires **Python 3.10+** on Windows 10/11.

```powershell
git clone https://github.com/okil6dev/Docktray.git
cd Docktray
pip install PyQt6 PyQt6-Frameless-Window PyQt6-Fluent-Widgets pywin32
python main.py
```

The first time the app runs it will create a default `config.json` next to `main.py`.

### Option 2 — Build a standalone `.exe`
```powershell
python build.py
```
The script invokes PyInstaller (`--onefile --noconsole`) and bundles the `src/`, `icons/app/`, `icons/projects/`, and `icons/settings_icon/` directories into a single `dist\DockTray.exe`. No Python install is required for end users.

The app sets the icon to `icons/app/icon.ico` and applies a proper `AppUserModelID`, so the resulting `.exe` shows the right icon in the taskbar and Alt-Tab.

---

## Usage

1. **Launch** — run `main.py` or the built `DockTray.exe`. The launcher icon appears in the system tray.
2. **Open the launcher** — left-click the tray icon, or right-click for the context menu.
3. **Add shortcuts** — use the bottom bar buttons (**Add File**, **Add Folder**, **Add Windows Apps**), or enable **Drag Mode** and drop items onto the launcher.
4. **Launch an item** — single-click any tile.
5. **Remove an item** — hover it and click the trash button that appears in its top-right corner.
6. **Customize** — click the **Settings** button in the bottom bar to open the settings window.
7. **Resize the launcher** — open Settings -> **Positioning** -> **Resize Tray**, then drag the resize handle in the top-left of the launcher to the size you want, then **Apply** (or **Cancel** to revert).
8. **Auto-start with Windows** — open Settings -> **General** and flip the **Start on Startup** switch.
9. **Exit** — right-click the tray icon -> **Exit DockTray**.

---

## Architecture

```
DockTray/
├── main.py                       # Entry point — tray icon, LauncherWindow, tray menu
├── build.py                      # PyInstaller onefile build script
├── config.json                   # Auto-generated user config (shortcuts + settings)
│
├── src/
│   ├── core/
│   │   ├── config_manager.py     # JSON load/save, get/set settings, add/remove shortcuts
│   │   ├── startup_manager.py    # Windows Startup folder .lnk management via win32com
│   │   └── icon_extractor.py     # HICON to QPixmap, UWP manifest logo resolution, AppsFolder PIDL
│   ├── ui/
│   │   ├── launcher_window.py    # Acrylic launcher, bottom bar, drag mode, tray-size resize handle
│   │   ├── shortcut_item.py      # Individual tile: icon + label + hover delete
│   │   ├── flow_layout.py        # Wrap-as-needed layout for the shortcut grid
│   │   ├── settings_window.py    # FluentWindow with Themes / General / Positioning / Exporting tabs
│   │   └── ui_utils.py           # SVG to QIcon, built-in icon set
│   └── settings_window.py        # (compat re-export)
│
└── icons/
    ├── app/                      # Main DockTray.ico + Windows Store-style logo assets
    ├── projects/                 # Project placeholder icons
    └── settings_icon/            # Icon used by the settings window
```

### Key dependencies
| Library | Purpose |
|---|---|
| **PyQt6** | Widgets, signals/slots, system-tray integration, animations. |
| **qframelesswindow** (`AcrylicWindow`) | Windows acrylic blur & borderless window. |
| **PyQt6-Fluent-Widgets** | Fluent-style settings window (cards, sliders, combo boxes, switch buttons). |
| **pywin32** (`win32gui`, `win32com`) | Force taskbar visibility, create the Startup-folder `.lnk`. |
| **ctypes** (`shell32`, `user32`, `ole32`) | Direct calls to `SHGetFileInfoW`, `SHParseDisplayName`, `DestroyIcon` for high-quality icon extraction. |
| **PyInstaller** | Bundles the app into a single distributable `.exe` (`build.py`). |

---

## Settings Reference

| Setting | Default | Description |
|---|---|---|
| `theme_mode` | `acrylic` | `black`, `white`, or `acrylic`. |
| `theme_whiteness` | `0` | `0` (dark acrylic) to `100` (pure white acrylic). |
| `icon_color` | `white` | `white` or `black` — bottom-bar icon tint. |
| `acrylic_opacity` | `10` | Internal multiplier for the acrylic overlay alpha. |
| `disable_acrylic_overlay` | `false` | When `true`, the launcher uses the absolute default acrylic (no color overlay). |
| `tray_width` / `tray_height` | `457` / `336` | Launcher window size in pixels. |
| `shortcut_icon_size` | `45` | Shortcut tile icon size in pixels (28 to 72). |
| `launcher_button_size` | `40` | Bottom-bar button size in pixels (32 to 56). |
| `taskbar_position` | `Bottom Taskbar` | `Bottom Taskbar`, `Top Taskbar`, `Left Taskbar (Vertical)`, `Right Taskbar (Vertical)`. |

---

## Troubleshooting

- **The settings window has no taskbar icon** — the app calls `win32gui.SetWindowLong(... WS_EX_APPWINDOW ...)` on a short delay after the window is created. If `pywin32` isn't installed, this is a no-op and the window will still appear in Alt-Tab and on screen.
- **Acrylic looks too dark / too light** — open **Settings -> Themes** and move the **Whiteness** slider. Click **Apply** to confirm.
- **A UWP / Start-app icon is missing** — the app falls back to a generic tile and labels it `UWP`. If the AUMID is wrong, remove and re-add the entry.
- **Want a fresh start** — close the app, delete `config.json`, relaunch. A clean default config will be regenerated.
- **Portable migration** — open **Settings -> Exporting -> Export All (Backup)** to dump `config.json`'s contents to a single JSON file you can import on another machine.

---

## Contributing

1. Fork & clone the repo.
2. Create a feature branch: `git checkout -b feature/my-thing`.
3. Make your changes and commit.
4. Run `python main.py` to manually verify.
5. Open a pull request describing what you added and why.

Please keep the existing theme/translucency comments up to date if you change acrylic math — the scaling factors are tuned by hand.

---

## License

CC0 1.0 Universal (Public Domain Dedication). Do whatever you like with this — copy it, fork it, ship it, sell it, claim it, remix it. No attribution required, no warranty, no strings attached. If it eats your Start menu, that's on you.

---

## Credits

- **PyQt6** & **Qt** — the foundation.
- **qframelesswindow** — acrylic blur support.
- **PyQt6-Fluent-Widgets** — the Fluent-style settings UI.
- **Microsoft Windows Shell API** — for the real icon and AUMID resolution that makes Start-apps look right.
