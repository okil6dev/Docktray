from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt

def svg_to_icon(svg_str, color="white"):
    """
    Convert an SVG string to a QIcon with a specific color.
    """
    # Replace currentColor with the actual color
    svg_str = svg_str.replace('currentColor', color)
    
    renderer = QSvgRenderer(svg_str.encode('utf-8'))
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)


# Icon SVGs
ICONS = {
    "add_file": '''<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline fill="none" stroke="currentColor" stroke-width="2" points="14 2 14 8 20 8"/><line fill="none" stroke="currentColor" stroke-width="2" x1="12" y1="18" x2="12" y2="12"/><line fill="none" stroke="currentColor" stroke-width="2" x1="9" y1="15" x2="15" y2="15"/></svg>''',
    "add_folder": '''<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><line fill="none" stroke="currentColor" stroke-width="2" x1="12" y1="11" x2="12" y2="17"/><line fill="none" stroke="currentColor" stroke-width="2" x1="9" y1="14" x2="15" y2="14"/></svg>''',
    "windows_apps": '''<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"/><rect x="14" y="3" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"/><rect x="3" y="14" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"/><rect x="14" y="14" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>''',
    "drag_mode": '''<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M7 8l-4 4 4 4"/><path fill="none" stroke="currentColor" stroke-width="2" d="M17 8l4 4-4 4"/><path fill="none" stroke="currentColor" stroke-width="2" d="M3 12h18"/></svg>''',
    "trash": '''<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/></svg>''',
    "close": '''<svg viewBox="0 0 24 24"><line fill="none" stroke="currentColor" stroke-width="2" x1="18" y1="6" x2="6" y2="18"/><line fill="none" stroke="currentColor" stroke-width="2" x1="6" y1="6" x2="18" y2="18"/></svg>''',
    "settings": '''<svg viewBox="0 0 24 24"><circle fill="none" stroke="currentColor" stroke-width="2" cx="12" cy="12" r="3"/><path fill="none" stroke="currentColor" stroke-width="2" d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>''',
    "moon": '''<svg viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>''',
    "sun": '''<svg viewBox="0 0 24 24"><circle fill="none" stroke="currentColor" stroke-width="2" cx="12" cy="12" r="5"/><line fill="none" stroke="currentColor" stroke-width="2" x1="12" y1="1" x2="12" y2="3"/><line fill="none" stroke="currentColor" stroke-width="2" x1="12" y1="21" x2="12" y2="23"/><line fill="none" stroke="currentColor" stroke-width="2" x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line fill="none" stroke="currentColor" stroke-width="2" x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line fill="none" stroke="currentColor" stroke-width="2" x1="1" y1="12" x2="3" y2="12"/><line fill="none" stroke="currentColor" stroke-width="2" x1="21" y1="12" x2="23" y2="12"/><line fill="none" stroke="currentColor" stroke-width="2" x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line fill="none" stroke="currentColor" stroke-width="2" x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>''',
    "acrylic": '''<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 15l4-4 4 4 4-4 4 4" fill="none" stroke="currentColor" stroke-width="2"/></svg>'''
}
