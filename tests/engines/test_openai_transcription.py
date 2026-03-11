import json
from unittest.mock import MagicMock
from dictatux.engines.openai.controller import OpenAIRealtimeProcessRunner
from tests.helpers import MockInputSimulator

def create_runner(input_simulator, **kwargs):
    mock_controller = MagicMock()
    mock_controller._stop_event = MagicMock()
    
    runner = OpenAIRealtimeProcessRunner(
        controller=mock_controller,
        api_key="fake-key",
        model="gpt-4o-transcribe",
        language="es",
        sample_rate=24000,
        channels=1,
        use_partials=kwargs.get("use_partials", False),
        input_simulator=input_simulator,
    )
    runner._ws = MagicMock()
    runner._connected = True
    return runner

def test_openai_transcription_completed():
    mock = MockInputSimulator()
    runner = create_runner(mock)
    
    msg = {
        "type": "conversation.item.input_audio_transcription.completed",
        "transcript": "Esto es una prueba de dictado."
    }
    runner._on_message(runner._ws, json.dumps(msg))
    
    assert mock.text == "Esto es una prueba de dictado."
    runner._controller.emit_transcription.assert_called_with("Esto es una prueba de dictado.")

def test_openai_transcription_partial_deltas():
    mock = MockInputSimulator()
    runner = create_runner(mock, use_partials=True)
    
    deltas = ["Esto", " es", " una", " prueba."]
    for d in deltas:
        msg = {
            "type": "conversation.item.input_audio_transcription.delta",
            "delta": d
        }
        runner._on_message(runner._ws, json.dumps(msg))
        
    msg_final = {
        "type": "conversation.item.input_audio_transcription.completed",
        "transcript": "Esto es una prueba."
    }
    runner._on_message(runner._ws, json.dumps(msg_final))
    
    assert mock.text == "Esto es una prueba."

def test_openai_error_message():
    mock = MockInputSimulator()
    runner = create_runner(mock)
    
    msg = {
        "type": "error",
        "error": {"message": "Invalid API key"}
    }
    runner._on_message(runner._ws, json.dumps(msg))
    
    assert mock.text == ""
    runner._controller.emit_error.assert_called_with("Invalid API key")

def test_openai_empty_transcript_ignored():
    mock = MockInputSimulator()
    runner = create_runner(mock)
    
    msg = {
        "type": "conversation.item.input_audio_transcription.completed",
        "transcript": "   "
    }
    runner._on_message(runner._ws, json.dumps(msg))
    
    assert mock.text == ""

def test_openai_response_output_text_delta_accumulation():
    mock = MockInputSimulator()
    runner = create_runner(mock)
    
    # 1. Created
    runner._on_message(runner._ws, json.dumps({
        "type": "response.created",
        "response": {"id": "resp_001"}
    }))
    
    # 2. Deltas
    deltas = ["Hola,", " ¿cómo", " estás?"]
    for d in deltas:
        runner._on_message(runner._ws, json.dumps({
            "type": "response.output_text.delta",
            "delta": d,
            "response_id": "resp_001"
        }))
        
    # 3. Completed
    runner._on_message(runner._ws, json.dumps({
        "type": "response.completed",
        "response": {"id": "resp_001"}
    }))
    
    assert mock.text == "Hola, ¿cómo estás?"
    runner._controller.emit_transcription.assert_called_with("Hola, ¿cómo estás?")
