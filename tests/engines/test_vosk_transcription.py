import io
import wave
import pytest
from unittest.mock import MagicMock
from dictatux.engines.vosk_local.inference_backend import VoskInferenceBackend

def load_wav_as_pcm(filepath: str) -> bytes:
    with wave.open(filepath, 'rb') as f:
        return f.readframes(f.getnframes())

@pytest.fixture(scope="module")
def vosk_backend():
    backend = VoskInferenceBackend(sample_rate=16000)
    model_path = "tests/fixtures/vosk-model-small-en-us-0.15"
    backend.load_model(model_path)
    yield backend
    backend.unload_model()

@pytest.mark.slow
def test_vosk_transcribes_english_audio(vosk_backend):
    audio_bytes = load_wav_as_pcm("tests/fixtures/audio/hello_world.wav")
    result = vosk_backend.transcribe(audio_bytes)
    assert "hello" in result.lower()

@pytest.mark.slow
def test_vosk_transcribes_numbers_audio(vosk_backend):
    audio_bytes = load_wav_as_pcm("tests/fixtures/audio/numbers.wav")
    result = vosk_backend.transcribe(audio_bytes)
    assert "one" in result.lower()
    assert "two" in result.lower()

@pytest.mark.slow
def test_vosk_transcribes_silence(vosk_backend):
    audio_bytes = load_wav_as_pcm("tests/fixtures/audio/silence.wav")
    result = vosk_backend.transcribe(audio_bytes)
    # The small vosk model sometimes hallucinates short words on silence like "i've" or "the"
    assert result in ("", "i've", "the", "a")

@pytest.mark.slow
def test_vosk_transcribe_streaming(vosk_backend):
    audio_bytes = load_wav_as_pcm("tests/fixtures/audio/hello_world.wav")
    
    mock_callback = MagicMock()
    vosk_backend._partial_callback = mock_callback
    
    chunk_size = 4000  # quarter a second
    chunks = [audio_bytes[i:i+chunk_size] for i in range(0, len(audio_bytes), chunk_size)]
    
    results = []
    for chunk in chunks:
        # consume iterator
        for res in vosk_backend.transcribe_streaming(chunk):
            if res:
                results.append(res)
    
    # Make sure we finish processing to get the final result
    # Vosk returns partials while processing and final when it thinks it's done or flushed
    # In transcribe_streaming we should get something
    assert len(results) > 0 or mock_callback.called

def test_vosk_lifecycle():
    backend = VoskInferenceBackend()
    assert not backend.is_loaded
    
    model_path = "tests/fixtures/vosk-model-small-en-us-0.15"
    backend.load_model(model_path)
    assert backend.is_loaded
    assert backend._recognizer is not None
    
    backend.unload_model()
    assert not backend.is_loaded
    assert backend._recognizer is None