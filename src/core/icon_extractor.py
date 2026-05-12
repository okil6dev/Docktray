import os
import json
import subprocess
import ctypes
from ctypes import wintypes
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt

# Shell32 constants
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000
SHGFI_SMALLICON = 0x000000001
SHGFI_USEFILEATTRIBUTES = 0x000000010
SHGFI_PIDL = 0x000000008

_UWP_ICON_CACHE = {}
_KNOWN_FOLDER_GUIDS = {
    "{6D809377-6AF0-444B-8957-A3773F02200E}": os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles", ""),
    "{7C5A40EF-A0FB-4BFC-874A-C0F2E0B9FA8E}": os.environ.get("ProgramFiles(x86)") or os.environ.get("ProgramFiles", ""),
    "{905E63B6-C1BF-494E-B29C-65B732D3D21A}": os.environ.get("ProgramFiles", ""),
}

class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80)
    ]


def _pixmap_from_hicon(hicon):
    if not hicon:
        return None
    try:
        hicon_val = hicon.value if hasattr(hicon, "value") else hicon
        q_image = QImage.fromHICON(hicon_val)
        if not q_image.isNull():
            return QPixmap.fromImage(q_image)
    finally:
        ctypes.windll.user32.DestroyIcon(hicon)
    return None


def _get_shell_icon_from_parsing_name(parsing_name, size='large'):
    """Resolve shell item via PIDL and get icon. Better for AppsFolder entries."""
    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32

    pidl = ctypes.c_void_p()
    sfgao = wintypes.DWORD(0)

    try:
        hr = shell32.SHParseDisplayName(
            ctypes.c_wchar_p(parsing_name),
            None,
            ctypes.byref(pidl),
            0,
            ctypes.byref(sfgao),
        )
        if hr != 0 or not pidl.value:
            return None

        shfi = SHFILEINFO()
        flags = SHGFI_ICON | SHGFI_PIDL
        flags |= SHGFI_LARGEICON if size == "large" else SHGFI_SMALLICON

        res = shell32.SHGetFileInfoW(
            pidl,
            0,
            ctypes.byref(shfi),
            ctypes.sizeof(shfi),
            flags,
        )
        if res and shfi.hIcon:
            return _pixmap_from_hicon(shfi.hIcon)
    except Exception:
        return None
    finally:
        if pidl.value:
            ole32.CoTaskMemFree(pidl)
    return None


def _pick_best_logo_variant(base_logo_path, desired_px):
    """Pick best existing UWP logo variant for the requested size."""
    base_logo_path = os.path.normpath(base_logo_path)
    folder = os.path.dirname(base_logo_path)
    filename = os.path.basename(base_logo_path)
    stem, ext = os.path.splitext(filename)
    if not ext:
        ext = ".png"

    # Prefer taskbar/app-list style variants first.
    target_sizes = [desired_px, 48, 44, 40, 36, 32, 30, 24, 20, 16]
    scale_sizes = [400, 200, 150, 125, 100]

    candidates = []
    for px in target_sizes:
        candidates.append(os.path.join(folder, f"{stem}.targetsize-{px}_altform-unplated{ext}"))
        candidates.append(os.path.join(folder, f"{stem}.targetsize-{px}{ext}"))
    for scale in scale_sizes:
        candidates.append(os.path.join(folder, f"{stem}.scale-{scale}{ext}"))
    candidates.append(base_logo_path)

    seen = set()
    for path in candidates:
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)
        if os.path.exists(path):
            return path
    return base_logo_path


def _resolve_uwp_logo_path(app_user_model_id, desired_px):
    """Resolve a Store app logo path from package manifest."""
    cache_key = f"{app_user_model_id}|{desired_px}"
    if cache_key in _UWP_ICON_CACHE:
        return _UWP_ICON_CACHE[cache_key]

    if "!" not in app_user_model_id:
        _UWP_ICON_CACHE[cache_key] = None
        return None

    package_family, app_id = app_user_model_id.split("!", 1)

    # Query app package + manifest and return an absolute logo path.
    ps_script = rf"""
$ErrorActionPreference = 'Stop'
$family = '{package_family.replace("'", "''")}'
$appId = '{app_id.replace("'", "''")}'
$pkg = Get-AppxPackage -PackageFamilyName $family | Select-Object -First 1
if (-not $pkg) {{ '' ; exit 0 }}
$manifestPath = Join-Path $pkg.InstallLocation 'AppxManifest.xml'
if (-not (Test-Path $manifestPath)) {{ '' ; exit 0 }}
[xml]$xml = Get-Content -LiteralPath $manifestPath -Raw
$apps = @($xml.Package.Applications.Application)
if (-not $apps -or $apps.Count -eq 0) {{ '' ; exit 0 }}
$appNode = $apps | Where-Object {{ $_.Id -eq $appId }} | Select-Object -First 1
if (-not $appNode) {{ $appNode = $apps | Select-Object -First 1 }}

$logo = $null
$ve = @($appNode.ChildNodes | Where-Object {{ $_.LocalName -eq 'VisualElements' }}) | Select-Object -First 1
if ($ve) {{
    $logo = $ve.GetAttribute('Square44x44Logo')
    if (-not $logo) {{ $logo = $ve.GetAttribute('Logo') }}
    if (-not $logo) {{ $logo = $ve.GetAttribute('Square150x150Logo') }}
}}

if (-not $logo) {{
    $propsLogo = $xml.Package.Properties.Logo
    if ($propsLogo) {{ $logo = [string]$propsLogo }}
}}

if ($logo -and -not ($logo -like 'ms-resource:*')) {{
    $abs = [System.IO.Path]::Combine($pkg.InstallLocation, ($logo -replace '/', '\'))
    if (Test-Path $abs) {{ $abs; exit 0 }}
}}

# Fallback: scan package assets for common tile/app-list icon files.
$assetCandidates = @()
$assetCandidates += Get-ChildItem -Path $pkg.InstallLocation -Recurse -Include *.png,*.jpg,*.jpeg -File -ErrorAction SilentlyContinue |
    Where-Object {{
        $_.Name -match 'targetsize-\d+' -or
        $_.Name -match 'Square44x44|Square150x150|AppList|Logo|StoreLogo'
    }} |
    Sort-Object {{
        # Prefer unplated targetsize icons, then app-list/square logos.
        $n = $_.Name
        if ($n -match 'altform-unplated') {{ 0 }}
        elseif ($n -match 'targetsize-') {{ 1 }}
        elseif ($n -match 'AppList|Square44x44') {{ 2 }}
        else {{ 3 }}
    }}, Length

if ($assetCandidates.Count -gt 0) {{
    $assetCandidates[0].FullName
    exit 0
}}

''
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=True
        )
        raw = (result.stdout or "").strip()
        if not raw:
            _UWP_ICON_CACHE[cache_key] = None
            return None
        best = _pick_best_logo_variant(raw, desired_px)
        _UWP_ICON_CACHE[cache_key] = best if os.path.exists(best) else None
        return _UWP_ICON_CACHE[cache_key]
    except Exception:
        _UWP_ICON_CACHE[cache_key] = None
        return None

def get_icon(path, size='large'):
    """
    Extract high-quality icon from a given path (file, folder, executable).
    Returns a QPixmap.
    """
    is_uwp = isinstance(path, str) and path.startswith("uwp:")
    is_startapp = isinstance(path, str) and path.startswith("startapp:")
    target = path
    if is_startapp:
        app_id = path.split(":", 1)[1]
        if not app_id:
            return None
        # For StartApps entries that are real AUMIDs (PackageFamily!AppId),
        # use manifest logos first to avoid generic shell icons.
        if "!" in app_id:
            desired_px = 64 if size == 'large' else 32
            logo_path = _resolve_uwp_logo_path(app_id, desired_px)
            if logo_path and os.path.exists(logo_path):
                startapp_pixmap = QPixmap(logo_path)
                if not startapp_pixmap.isNull():
                    return startapp_pixmap
        # Start menu icon resolution via AppsFolder identity.
        appsfolder_path = f"shell:AppsFolder\\{app_id}"
        pidl_pixmap = _get_shell_icon_from_parsing_name(appsfolder_path, size)
        if pidl_pixmap and not pidl_pixmap.isNull():
            return pidl_pixmap
        target = f"shell:AppsFolder\\{app_id}"
    elif is_uwp:
        app_id = path.split(":", 1)[1]
        if not app_id:
            return None

        # Try mapping Start-app style IDs like "{GUID}\App\app.exe" to real file paths first.
        if "!" not in app_id and "\\" in app_id and app_id.startswith("{"):
            parts = app_id.split("\\", 1)
            if len(parts) == 2:
                root = _KNOWN_FOLDER_GUIDS.get(parts[0].upper())
                if root:
                    resolved = os.path.normpath(os.path.join(root, parts[1]))
                    if os.path.exists(resolved):
                        return get_icon(resolved, size)

        # True UWP IDs can resolve through manifest logo assets.
        if "!" in app_id:
            desired_px = 64 if size == 'large' else 32
            logo_path = _resolve_uwp_logo_path(app_id, desired_px)
            if logo_path and os.path.exists(logo_path):
                uwp_pixmap = QPixmap(logo_path)
                if not uwp_pixmap.isNull():
                    return uwp_pixmap

        # Fallback: ask shell for the AppsFolder item icon.
        appsfolder_path = f"shell:AppsFolder\\{app_id}"
        pidl_pixmap = _get_shell_icon_from_parsing_name(appsfolder_path, size)
        if pidl_pixmap and not pidl_pixmap.isNull():
            return pidl_pixmap
        target = f"shell:AppsFolder\\{app_id}"
    elif not os.path.exists(path):
        return None

    shell32 = ctypes.windll.shell32
    shfi = SHFILEINFO()
    flags = SHGFI_ICON
    
    if size == 'large':
        flags |= SHGFI_LARGEICON
    else:
        flags |= SHGFI_SMALLICON

    # Call SHGetFileInfoW
    res = shell32.SHGetFileInfoW(
        target,
        0,
        ctypes.byref(shfi),
        ctypes.sizeof(shfi),
        flags
    )

    if res and shfi.hIcon:
        pix = _pixmap_from_hicon(shfi.hIcon)
        if pix and not pix.isNull():
            return pix

    # Fallback to empty pixmap if extraction fails
    return QPixmap()
