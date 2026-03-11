from pathlib import Path
from PySide6.QtGui import QIcon


def get_icon(name, fallback_resource=None):
    """
    Load an icon by name from theme, or resource fallback, or filesystem fallback.
    """
    # 1. Try from theme
    icon = QIcon.fromTheme(name)
    if not icon.isNull():
        return icon

    # 2. Try from resource
    if fallback_resource:
        icon = QIcon(fallback_resource)
        if not icon.isNull():
            return icon

    # 3. Try from filesystem (relative to this package)
    # Mapping common icon names to paths in our icons directory
    fs_map = {
        "audio-input-microphone": "scalable/micro.svg",
        "microphone-sensitivity-muted": "scalable/nomicro.svg",
    }

    if name in fs_map:
        current_dir = Path(__file__).resolve().parent
        # Go up one level to repo root, then into icons/dictatux/
        icon_path = current_dir.parent / "icons" / "dictatux" / fs_map[name]
        if icon_path.exists():
            return QIcon(str(icon_path))

    # If still not found, return empty icon or try the resource name directly as file
    return icon
