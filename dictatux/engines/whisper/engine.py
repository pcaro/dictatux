"""Plugin definition for Whisper Docker engine."""

from __future__ import annotations

from dataclasses import asdict
import shutil
from typing import Dict, Tuple, TYPE_CHECKING

from dictatux.engine_plugin import EnginePlugin, register_plugin
from .settings import WhisperSettings
from dictatux.stt_engine import STTController, STTProcessRunner
from .controller import (
    WhisperDockerController,
    WhisperDockerProcessRunner,
)

if TYPE_CHECKING:  # pragma: no cover
    from dictatux.settings import Settings


class WhisperDockerPlugin(EnginePlugin):
    """Built-in plugin for the Whisper Docker engine."""

    @property
    def name(self) -> str:
        return "whisper-docker"

    @property
    def display_name(self) -> str:
        return "Whisper Docker"

    def get_settings_schema(self):  # type: ignore[override]
        return WhisperSettings

    def create_controller_runner(
        self, settings: WhisperSettings
    ) -> Tuple[STTController, STTProcessRunner]:  # type: ignore[override]
        params: Dict[str, object] = asdict(settings)
        params.pop("engine_type", None)
        params.pop("device_name", None)
        api_port = params.pop("port", None)
        if api_port is not None:
            params["api_port"] = api_port
        controller = WhisperDockerController(settings)
        runner = WhisperDockerProcessRunner(controller, **params)
        return controller, runner

    def apply_to_settings(
        self, app_settings: "Settings", engine_settings: WhisperSettings
    ) -> None:
        app_settings.sttEngine = self.name
        app_settings.deviceName = engine_settings.device_name
        app_settings.whisperModel = engine_settings.model
        app_settings.whisperPort = engine_settings.port
        app_settings.whisperLanguage = engine_settings.language or ""
        app_settings.whisperChunkDuration = engine_settings.chunk_duration
        app_settings.whisperSampleRate = engine_settings.sample_rate
        app_settings.whisperChannels = engine_settings.channels
        app_settings.whisperVadEnabled = engine_settings.vad_enabled
        app_settings.whisperVadThreshold = engine_settings.vad_threshold
        app_settings.whisperAutoReconnect = engine_settings.auto_reconnect

    def load_settings_from_app(self, app_settings: "Settings") -> WhisperSettings:
        """Create WhisperSettings from application Settings."""
        return WhisperSettings(
            engine_type=self.name,
            device_name=app_settings.deviceName,
            model=app_settings.whisperModel,
            port=app_settings.whisperPort,
            language=app_settings.whisperLanguage or None,
            chunk_duration=app_settings.whisperChunkDuration,
            sample_rate=app_settings.whisperSampleRate,
            channels=app_settings.whisperChannels,
            vad_enabled=app_settings.whisperVadEnabled,
            vad_threshold=app_settings.whisperVadThreshold,
            auto_reconnect=app_settings.whisperAutoReconnect,
        )

    def check_availability(self):  # type: ignore[override]
        if shutil.which("docker"):
            return True, ""
        return False, "Docker executable not found in PATH"


register_plugin(WhisperDockerPlugin())
