# ABOUTME: Settings schema for Google Cloud Speech engine with UI metadata.
# ABOUTME: Defines GoogleCloudSettings dataclass with field metadata for dynamic UI generation.

from __future__ import annotations

from dataclasses import dataclass, field

from dictatux.base_settings import EngineSettings


@dataclass
class GoogleCloudSettings(EngineSettings):
    """Settings for Google Cloud Speech-to-Text engine."""

    engine_type: str = field(
        default="google-cloud-speech",
        metadata={"hidden": True}
    )

    credentials_path: str = field(
        default="",
        metadata={
            "label": "Credentials Path",
            "widget": "file_picker",
            "file_filter": "JSON Files (*.json);;All Files (*)",
            "tooltip": (
                "<b>Service Account Credentials</b><br>"
                "Path to the Google Cloud service account JSON key file.<br><br>"
                "<i>How to obtain:</i><br>"
                "1. Go to Google Cloud Console → IAM & Admin → Service Accounts<br>"
                "2. Create key → Download JSON<br>"
                "3. Set path to the downloaded file"
            ),
        }
    )

    project_id: str = field(
        default="",
        metadata={
            "label": "Project ID",
            "widget": "text",
            "tooltip": "GCP project identifier; leave empty to auto-detect from credentials",
        }
    )

    location: str = field(
        default="global",
        metadata={
            "label": "Location",
            "widget": "dropdown",
            "options": [
                {"label": "Global (Default)", "value": "global"},
                {"label": "United States (Multi-region)", "value": "us"},
                {"label": "European Union (Multi-region)", "value": "eu"},
                {"label": "US Central 1 (Iowa)", "value": "us-central1"},
                {"label": "Europe West 1 (Belgium)", "value": "europe-west1"},
                {"label": "Europe West 4 (Netherlands)", "value": "europe-west4"},
            ],
            "tooltip": (
                "<b>GCP Location</b><br>"
                "The Google Cloud region to use for recognition.<br><br>"
                "<b>Common values:</b><br>"
                "<b>global:</b> Default, works for many models<br>"
                "<b>us/eu:</b> Multi-region (recommended for chirp_3)<br>"
                "<b>Regional:</b> Specific regional endpoints"
            ),
        }
    )

    language_code: str = field(
        default="en-US",
        metadata={
            "label": "Language Code",
            "widget": "text",
            "tooltip": "Primary BCP-47 language code (e.g. en-US, es-ES)",
        }
    )

    model: str = field(
        default="chirp_3",
        metadata={
            "label": "Model",
            "widget": "dropdown",
            "options": [
                {"label": "Chirp 3 (Latest Gen)", "value": "chirp_3"},
                {"label": "Long (Optimized for long-form)", "value": "long"},
                {"label": "Short (Optimized for short utterances)", "value": "short"},
                {"label": "Telephony (Phone calls)", "value": "telephony"},
                {"label": "Medical Dictation", "value": "medical_dictation"},
                {"label": "Medical Conversation", "value": "medical_conversation"},
            ],
            "tooltip": (
                "<b>Speech Recognition Model</b><br>"
                "Google Cloud Speech model to use.<br><br>"
                "<b>Recommended models:</b><br>"
                "<b>chirp_3:</b> Latest generation, best quality<br>"
                "<b>long:</b> Optimized for long-form audio<br>"
                "<b>short:</b> Optimized for short utterances"
            ),
        }
    )

    sample_rate: int = field(
        default=16000,
        metadata={
            "label": "Sample Rate",
            "widget": "text",
            "tooltip": "Sample rate in Hz for audio sent to the gRPC stream",
        }
    )

    channels: int = field(
        default=1,
        metadata={
            "label": "Channels",
            "widget": "text",
            "tooltip": "Number of audio channels (must match recorder configuration)",
        }
    )

    vad_enabled: bool = field(
        default=True,
        metadata={
            "label": "VAD Enabled",
            "widget": "checkbox",
            "tooltip": "Enable voice activity detection when streaming audio",
        }
    )

    vad_threshold: float = field(
        default=50.0,
        metadata={
            "label": "VAD Threshold",
            "widget": "text",
            "tooltip": "RMS loudness threshold used when VAD is enabled",
        }
    )

    def __post_init__(self):
        """Validate sample rate is in valid range."""
        if not 8000 <= self.sample_rate <= 48000:
            raise ValueError(f"Invalid sample rate: {self.sample_rate}")
