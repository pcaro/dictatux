#!/usr/bin/env python3
"""Translation extraction file for language names.

This file exists solely for lupdate to extract translatable strings.
These language names are used dynamically in model dialogs.
"""

from PySide6.QtCore import QCoreApplication

_translate = QCoreApplication.translate

#: These strings are extracted for translation but used dynamically
language_names = [
    _translate("Languages", "English"),
    _translate("Languages", "Indian English"),
    _translate("Languages", "Chinese"),
    _translate("Languages", "Russian"),
    _translate("Languages", "French"),
    _translate("Languages", "German"),
    _translate("Languages", "Spanish"),
    _translate("Languages", "Portuguese/Brazilian Portuguese"),
    _translate("Languages", "Greek"),
    _translate("Languages", "Turkish"),
    _translate("Languages", "Vietnamese"),
    _translate("Languages", "Italian"),
    _translate("Languages", "Dutch"),
    _translate("Languages", "Catalan"),
    _translate("Languages", "Arabic"),
    _translate("Languages", "Farsi"),
    _translate("Languages", "Filipino"),
    _translate("Languages", "Ukrainian"),
    _translate("Languages", "Kazakh"),
    _translate("Languages", "Speaker identification model"),
]
