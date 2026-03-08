#!/usr/bin/env python3
"""Translation extraction file for engine names.

This file exists solely for lupdate to extract translatable engine display names.
These names are retrieved dynamically via plugin.display_name.
"""

from PySide6.QtCore import QCoreApplication

_translate = QCoreApplication.translate

#: Engine display names for translation extraction
engine_names = [
    _translate("EngineRegistry", "Vosk (Local)"),
    _translate("EngineRegistry", "Whisper (Local)"),
    _translate("EngineRegistry", "Whisper (Docker)"),
    _translate("EngineRegistry", "Google Cloud Speech"),
    _translate("EngineRegistry", "OpenAI Realtime API"),
    _translate("EngineRegistry", "Gemini Live API"),
]
