"""Built-in STT engine modules."""

from __future__ import annotations

# Import modules for side effects (engine plugin registration)
from .google import engine as _google_engine  # noqa: F401
from .openai import engine as _openai_engine  # noqa: F401
from .vosk_local import engine as _vosk_local_engine  # noqa: F401
from .whisper import engine as _whisper_engine  # noqa: F401
from .whisper_local import engine as _whisper_local_engine  # noqa: F401

__all__ = [
    "whisper",
    "google",
    "openai",
    "vosk_local",
    "whisper_local",
]
