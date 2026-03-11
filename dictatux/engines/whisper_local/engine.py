"""Engine plugin registration for WhisperLocal."""

from typing import TYPE_CHECKING

from dictatux.engine_plugin import EnginePlugin, register_plugin

from .controller import WhisperLocalController
from .runner import WhisperLocalRunner
from .settings import WhisperLocalSettings

if TYPE_CHECKING:  # pragma: no cover
    from dictatux.settings import Settings


class WhisperLocalPlugin(EnginePlugin):
    """Plugin for WhisperLocal STT engine."""

    @property
    def name(self) -> str:
        return "whisper-local"

    @property
    def display_name(self) -> str:
        return "Whisper (Local)"

    def get_settings_schema(self):
        return WhisperLocalSettings

    def create_controller_runner(self, settings):
        controller = WhisperLocalController(settings)
        runner = WhisperLocalRunner(controller, settings)
        return controller, runner

    def apply_to_settings(
        self, app_settings: "Settings", engine_settings: WhisperLocalSettings
    ) -> None:
        """Apply WhisperLocalSettings to the application Settings instance."""
        app_settings.sttEngine = self.name
        app_settings.deviceName = engine_settings.device_name
        app_settings.whisperLocalModelSize = engine_settings.model_size
        app_settings.whisperLocalLanguage = engine_settings.language
        app_settings.whisperLocalDevice = engine_settings.device
        app_settings.whisperLocalComputeType = engine_settings.compute_type
        app_settings.whisperLocalVadThreshold = engine_settings.vad_threshold
        app_settings.whisperLocalContextLimitChars = engine_settings.context_limit_chars
        app_settings.whisperLocalAutoResetContext = engine_settings.auto_reset_context
        app_settings.whisperLocalLocale = engine_settings.locale
        app_settings.whisperLocalMaxQueueDepth = engine_settings.max_queue_depth

    def load_settings_from_app(self, app_settings: "Settings") -> WhisperLocalSettings:
        """Create WhisperLocalSettings from application Settings."""
        return WhisperLocalSettings(
            engine_type=self.name,
            device_name=app_settings.deviceName,
            model_size=app_settings.whisperLocalModelSize,
            language=app_settings.whisperLocalLanguage,
            device=app_settings.whisperLocalDevice,
            compute_type=app_settings.whisperLocalComputeType,
            vad_threshold=app_settings.whisperLocalVadThreshold,
            context_limit_chars=app_settings.whisperLocalContextLimitChars,
            auto_reset_context=app_settings.whisperLocalAutoResetContext,
            locale=app_settings.whisperLocalLocale,
            max_queue_depth=app_settings.whisperLocalMaxQueueDepth,
        )

    def check_availability(self):
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return (
                False,
                "faster-whisper not installed. Run: pip install faster-whisper",
            )

        try:
            import torch  # noqa: F401
            import silero_vad  # noqa: F401
        except ImportError:
            return (
                False,
                'torch or silero-vad not installed. Run: pip install "dictatux[whisper_local]"',
            )

        return True, ""


# Register plugin
register_plugin(WhisperLocalPlugin())
