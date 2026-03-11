import pytest
from unittest.mock import MagicMock
from dictatux.engines.whisper_local.inference_backend import WhisperInferenceBackend, ContextManager

class FakeSegment:
    def __init__(self, text, no_speech_prob, start=0.0, end=1.0):
        self.text = text
        self.no_speech_prob = no_speech_prob
        self.start = start
        self.end = end

class FakeInfo:
    def __init__(self, language="es"):
        self.language = language

@pytest.fixture
def whisper_backend():
    backend = WhisperInferenceBackend()
    backend._model = MagicMock()
    backend._context_manager = ContextManager(max_chars=100, auto_reset_seconds=30.0)
    backend._language = "es"
    return backend

def test_whisper_local_filters_hallucinations(whisper_backend):
    # Segments: 1 good, 1 hallucination, 1 good
    segments = [
        FakeSegment(text=" Esto es real.", no_speech_prob=0.1),
        FakeSegment(text=" Gracias por ver.", no_speech_prob=0.9),  # hallucination > 0.6
        FakeSegment(text=" Fin del dictado.", no_speech_prob=0.2),
    ]
    
    whisper_backend._model.transcribe.return_value = (segments, FakeInfo())
    
    # Send dummy bytes (not used by mock)
    dummy_audio = b"\x00" * 32000
    result = whisper_backend.transcribe(dummy_audio)
    
    assert result == "Esto es real. Fin del dictado."

def test_whisper_local_concatenation(whisper_backend):
    segments = [
        FakeSegment(text="Hola ", no_speech_prob=0.1),
        FakeSegment(text="mundo ", no_speech_prob=0.1),
        FakeSegment(text="feliz.", no_speech_prob=0.1),
    ]
    
    whisper_backend._model.transcribe.return_value = (segments, FakeInfo())
    
    result = whisper_backend.transcribe(b"\x00" * 100)
    assert result == "Hola mundo feliz."

def test_whisper_local_context_manager(whisper_backend):
    # First transcription
    whisper_backend._model.transcribe.return_value = (
        [FakeSegment(text="Primera frase.", no_speech_prob=0.1)], FakeInfo()
    )
    whisper_backend.transcribe(b"\x00" * 100)
    
    # Check if context was updated
    assert whisper_backend._context_manager.get() == " Primera frase."
    
    # Second transcription
    whisper_backend._model.transcribe.return_value = (
        [FakeSegment(text=" Segunda frase.", no_speech_prob=0.1)], FakeInfo()
    )
    whisper_backend.transcribe(b"\x00" * 100)
    
    # Verify initial_prompt on the second call used the context
    # Get the arguments of the last call to transcribe
    _, kwargs = whisper_backend._model.transcribe.call_args
    assert kwargs.get("initial_prompt") == " Primera frase."
    
    # Context should now include both
    assert whisper_backend._context_manager.get() == " Primera frase. Segunda frase."

def test_whisper_local_empty_segments(whisper_backend):
    # Empty segments
    whisper_backend._model.transcribe.return_value = ([], FakeInfo())
    
    result = whisper_backend.transcribe(b"\x00" * 100)
    assert result == ""
    assert whisper_backend._context_manager.get() is None

def test_whisper_local_only_hallucinations(whisper_backend):
    segments = [
        FakeSegment(text=" Silencio.", no_speech_prob=0.99),
        FakeSegment(text=" [Música]", no_speech_prob=0.85),
    ]
    
    whisper_backend._model.transcribe.return_value = (segments, FakeInfo())
    
    result = whisper_backend.transcribe(b"\x00" * 100)
    assert result == ""
    assert whisper_backend._context_manager.get() is None
