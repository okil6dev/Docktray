import os
import ctypes
from ctypes import wintypes
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt

# Shell32 constants
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000
SHGFI_SMALLICON = 0x000000001
SHGFI_USEFILEATTRIBUTES = 0x000000010

class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80)
    ]

def get_icon(path, size='large'):
    """
    Extract high-quality icon from a given path (file, folder, executable).
    Returns a QPixmap.
    """
    if not os.path.exists(path):
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
        path,
        0,
        ctypes.byref(shfi),
        ctypes.sizeof(shfi),
        flags
    )

    if res and shfi.hIcon:
        try:
            # Convert HICON to QImage
            # QImage.fromHICON requires the HICON to be converted to a Python int
            # shfi.hIcon is a c_void_p, we can extract the value
            hicon_val = shfi.hIcon
            if hasattr(hicon_val, 'value'):
                hicon_val = hicon_val.value
                
            q_image = QImage.fromHICON(hicon_val)
            
            if not q_image.isNull():
                q_pixmap = QPixmap.fromImage(q_image)
                return q_pixmap
        finally:
            # Clean up the HICON handle
            ctypes.windll.user32.DestroyIcon(shfi.hIcon)

    # Fallback to empty pixmap if extraction fails
    return QPixmap()
