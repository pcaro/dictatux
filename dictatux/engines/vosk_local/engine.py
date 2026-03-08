"""Engine plugin registration for VoskLocal."""

from typing import TYPE_CHECKING

from dictatux.engine_plugin import EnginePlugin, register_plugin

from .controller import VoskLocalController
from .runner import VoskLocalRunner
from .settings import VoskLocalSettings

if TYPE_CHECKING:  # pragma: no cover
    from dictatux.settings import Settings


class VoskLocalPlugin(EnginePlugin):
    """Plugin for VoskLocal STT engine."""

    @property
    def name(self) -> str:
        return "vosk-local"

    @property
    def display_name(self) -> str:
        return "Vosk (Local)"

    def get_settings_schema(self):
        return VoskLocalSettings

    def create_controller_runner(self, settings):
        controller = VoskLocalController(settings)
        runner = VoskLocalRunner(controller, settings)
        return controller, runner

    def apply_to_settings(
        self, app_settings: "Settings", engine_settings: VoskLocalSettings
    ) -> None:
        """Apply VoskLocalSettings to the application Settings instance."""
        app_settings.sttEngine = self.name
        app_settings.deviceName = engine_settings.device_name
        app_settings.voskModelPath = engine_settings.model_path
        app_settings.voskVadType = engine_settings.vad_type
        app_settings.voskVadThreshold = engine_settings.vad_threshold
        app_settings.voskSilenceTimeoutMs = engine_settings.silence_timeout_ms
        app_settings.voskSampleRate = engine_settings.sample_rate
        app_settings.voskPartialResults = engine_settings.partial_results
        app_settings.voskTextFormatting = engine_settings.text_formatting
        app_settings.voskLocale = engine_settings.locale
        app_settings.voskMaxQueueDepth = engine_settings.max_queue_depth

    def load_settings_from_app(self, app_settings: "Settings") -> VoskLocalSettings:
        """Create VoskLocalSettings from application Settings."""
        return VoskLocalSettings(
            engine_type=self.name,
            device_name=app_settings.deviceName,
            model_path=app_settings.voskModelPath,
            sample_rate=app_settings.voskSampleRate,
            device=None,
            vad_threshold=app_settings.voskVadThreshold,
            vad_type=app_settings.voskVadType,
            silence_timeout_ms=app_settings.voskSilenceTimeoutMs,
            partial_results=app_settings.voskPartialResults,
            text_formatting=app_settings.voskTextFormatting,
            locale=app_settings.voskLocale,
            max_queue_depth=app_settings.voskMaxQueueDepth,
        )

    def check_availability(self):
        try:
            import vosk
        except ImportError:
            return False, "vosk not installed. Run: pip install vosk"

        try:
            import torch
            import silero_vad
        except ImportError:
            return (
                False,
                'torch or silero-vad not installed. Run: pip install "dictatux[local_stt]"',
            )

        return True, ""


# Register plugin
register_plugin(VoskLocalPlugin())
