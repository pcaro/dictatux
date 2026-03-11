import io
import struct
import wave
from unittest.mock import MagicMock, patch
from dictatux.engines.whisper.controller import WhisperDockerProcessRunner
from tests.helpers import MockInputSimulator
import requests

REAL_API_RESPONSE = {"text": "Esto es una prueba de dictado."}


def make_audio_chunk(level=1000, duration_samples=16000):
    """Generates a valid WAV chunk with controlled RMS level."""
    # 16-bit PCM, 16000Hz, mono.
    pcm_data = struct.pack(f"<{duration_samples}h", *[level] * duration_samples)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_data)

    return wav_buffer.getvalue()


def create_runner(input_simulator, **kwargs):
    mock_controller = MagicMock()
    mock_controller._stop_event = MagicMock()

    runner = WhisperDockerProcessRunner(
        controller=mock_controller,
        container_name="test-whisper",
        api_port=9000,
        model="base",
        language="es",
        chunk_duration=5.0,
        sample_rate=16000,
        channels=1,
        vad_enabled=kwargs.get("vad_enabled", False),
        vad_threshold=kwargs.get("vad_threshold", 500.0),
        auto_reconnect=kwargs.get("auto_reconnect", False),
        input_simulator=input_simulator,
    )
    return runner


@patch("dictatux.engines.whisper.controller.requests.post")
def test_whisper_docker_transcription_success(mock_post):
    mock_simulator = MockInputSimulator()
    runner = create_runner(mock_simulator)

    mock_response = MagicMock()
    mock_response.json.return_value = REAL_API_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    audio_chunk = make_audio_chunk(level=1000)
    runner._process_audio_chunk(audio_chunk)

    assert mock_simulator.text == "Esto es una prueba de dictado."
    runner._controller.set_transcribing.assert_called()


@patch("dictatux.engines.whisper.controller.requests.post")
def test_whisper_docker_vad_silence_skipped(mock_post):
    mock_simulator = MockInputSimulator()
    runner = create_runner(mock_simulator, vad_enabled=True, vad_threshold=500.0)

    audio_chunk = make_audio_chunk(level=100)  # Below threshold
    runner._process_audio_chunk(audio_chunk)

    mock_post.assert_not_called()
    assert mock_simulator.text == ""


@patch("dictatux.engines.whisper.controller.requests.post")
def test_whisper_docker_empty_response(mock_post):
    mock_simulator = MockInputSimulator()
    runner = create_runner(mock_simulator)

    mock_response = MagicMock()
    mock_response.json.return_value = {"text": ""}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    audio_chunk = make_audio_chunk(level=1000)
    runner._process_audio_chunk(audio_chunk)

    assert mock_simulator.text == ""


@patch("dictatux.engines.whisper.controller.time.sleep")
@patch("dictatux.engines.whisper.controller.requests.post")
def test_whisper_docker_http_error_retry(mock_post, mock_sleep):
    mock_simulator = MockInputSimulator()
    runner = create_runner(mock_simulator, auto_reconnect=True)

    # Mock container check to avoid real docker calls
    runner._is_container_running = MagicMock(return_value=True)

    mock_post.side_effect = requests.exceptions.RequestException("API down")

    audio_chunk = make_audio_chunk(level=1000)
    runner._process_audio_chunk(audio_chunk)

    assert mock_simulator.text == ""
    # With max_retries=3, post should be called 3 times
    assert mock_post.call_count == 3
