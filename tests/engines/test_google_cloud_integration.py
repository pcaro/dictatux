"""
Integration tests for Google Cloud Speech with real API mock data.

This test simulates the EXACT responses captured from the log and verifies
that the current code writes the text correctly.
"""

from __future__ import annotations

import queue
from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List, Callable

from tests.helpers import MockInputSimulator


# ============================================================================
# Google Cloud Speech API mocks (real data from log)
# ============================================================================


@dataclass
class MockRecognitionAlternative:
    """Mock of a recognition alternative."""

    transcript: str
    confidence: float = 0.0


@dataclass
class MockRecognitionResult:
    """Mock of a recognition result."""

    alternatives: List[MockRecognitionAlternative]
    is_final: bool
    stability: float = 0.0


@dataclass
class MockStreamingResponse:
    """Mock of a streaming API response."""

    results: List[MockRecognitionResult]


# EXACT API responses from log (13:15:38 - 13:15:53)
REAL_API_RESPONSES: List[MockStreamingResponse] = [
    # 13:15:38.425 - First INTERIM
    MockStreamingResponse(
        [
            MockRecognitionResult(
                alternatives=[
                    MockRecognitionAlternative(
                        transcript="Esto es una prueba de dictado hablando fluido. Estoy",
                        confidence=0.0,
                    )
                ],
                is_final=False,
                stability=0.0,
            )
        ]
    ),
    # 13:15:43.379 - Second INTERIM (accumulative)
    MockStreamingResponse(
        [
            MockRecognitionResult(
                alternatives=[
                    MockRecognitionAlternative(
                        transcript="Esto es una prueba de dictado hablando fluido. Estoy intentando realizar un párrafo bastante largo para ver si tenemos",
                        confidence=0.0,
                    )
                ],
                is_final=False,
                stability=0.0,
            )
        ]
    ),
    # 13:15:45.838 - First FINAL
    MockStreamingResponse(
        [
            MockRecognitionResult(
                alternatives=[
                    MockRecognitionAlternative(
                        transcript="Esto es una prueba de dictado hablando fluido. Estoy intentando realizar un párrafo bastante largo para ver si tenemos resultados intermedios.",
                        confidence=0.0,
                    )
                ],
                is_final=True,
                stability=0.0,
            )
        ]
    ),
    # 13:15:51.515 - Third INTERIM (new phrase after pause)
    MockStreamingResponse(
        [
            MockRecognitionResult(
                alternatives=[
                    MockRecognitionAlternative(
                        transcript="Eso es la prueba. Ahora mismo termino el párrafo y voy a ver",
                        confidence=0.0,
                    )
                ],
                is_final=False,
                stability=0.0,
            )
        ]
    ),
    # 13:15:53.907 - Second FINAL (with correction: "Esto"->"Eso", "."->",")
    MockStreamingResponse(
        [
            MockRecognitionResult(
                alternatives=[
                    MockRecognitionAlternative(
                        transcript=" Eso es la prueba, ahora mismo termino el párrafo y voy a ver si transcribe.",
                        confidence=0.0,
                    )
                ],
                is_final=True,
                stability=0.0,
            )
        ]
    ),
]


# Expected final text (finals only, current behavior)
EXPECTED_FINAL_TEXT = (
    "Esto es una prueba de dictado hablando fluido. Estoy intentando realizar "
    "un párrafo bastante largo para ver si tenemos resultados intermedios."
    " Eso es la prueba, ahora mismo termino el párrafo y voy a ver si transcribe."
)


# ============================================================================
# Helper to create the runner
# ============================================================================


def create_runner(
    input_simulator: Callable[[str], None], **kwargs
) -> GoogleCloudSpeechProcessRunner:  # noqa: F821
    """
    Creates a GoogleCloudSpeechProcessRunner configured for testing.

    Args:
        input_simulator: Function that will receive the writes (mock)
        **kwargs: Extra parameters for the runner

    Returns:
        The runner ready to run _response_loop()
    """
    from dictatux.engines.google.controller import GoogleCloudSpeechProcessRunner

    mock_controller = MagicMock()
    mock_controller._stop_event = MagicMock()

    runner = GoogleCloudSpeechProcessRunner(
        controller=mock_controller,
        credentials_path="/fake/path.json",
        project_id="test-project",
        location="eu",
        language_code="es-ES",
        model="chirp_3",
        sample_rate=16000,
        channels=1,
        vad_enabled=False,
        use_partials=kwargs.get("use_partials", False),
        input_simulator=input_simulator,
    )

    # Setup internal state needed for _response_loop
    runner._client = MagicMock()
    runner._speech_types = MagicMock()
    runner._audio_queue = queue.Queue()
    runner._request_generator = lambda: iter([])

    return runner


# ============================================================================
# Tests for current behavior
# ============================================================================


class TestGoogleCloudSpeechCurrentBehavior:
    """Tests for CURRENT behavior (finals only)."""

    def test_final_text_is_correct(self):
        """The final written text must be the concatenation of finals."""
        mock = MockInputSimulator()
        runner = create_runner(mock)

        runner._client.streaming_recognize.return_value = REAL_API_RESPONSES
        runner._response_loop()

        assert mock.text == EXPECTED_FINAL_TEXT

    def test_only_finals_generate_calls(self):
        """Only FINAL results generate calls to input_simulator."""
        mock = MockInputSimulator()
        runner = create_runner(mock)

        runner._client.streaming_recognize.return_value = REAL_API_RESPONSES
        runner._response_loop()

        # 3 INTERIM + 2 FINAL in sequence -> only 2 calls
        assert len(mock.calls) == 2
        assert (
            mock.calls[0] == REAL_API_RESPONSES[2].results[0].alternatives[0].transcript
        )
        assert (
            mock.calls[1] == REAL_API_RESPONSES[4].results[0].alternatives[0].transcript
        )

    def test_empty_transcript_ignored(self):
        """A final result with empty text does not generate a write."""
        mock = MockInputSimulator()
        runner = create_runner(mock)

        runner._client.streaming_recognize.return_value = [
            MockStreamingResponse(
                [
                    MockRecognitionResult(
                        alternatives=[MockRecognitionAlternative(transcript="   ")],
                        is_final=True,
                    )
                ]
            )
        ]
        runner._response_loop()

        assert mock.text == ""
        assert len(mock.calls) == 0

    def test_no_alternatives_ignored(self):
        """A result without alternatives does not generate a write."""
        mock = MockInputSimulator()
        runner = create_runner(mock)

        runner._client.streaming_recognize.return_value = [
            MockStreamingResponse(
                [MockRecognitionResult(alternatives=[], is_final=True)]
            )
        ]
        runner._response_loop()

        assert mock.text == ""
        assert len(mock.calls) == 0


# ============================================================================
# Tests for future behavior with partials (TDD)
# ============================================================================


class TestGoogleCloudSpeechWithPartials:
    """
    Tests for FUTURE behavior with partials.

    These tests define what should happen when we implement support
    for showing intermediate transcriptions in real time.
    """

    def test_interim_generates_call(self):
        """INTERIMs must generate calls to input_simulator."""
        mock = MockInputSimulator()
        runner = create_runner(mock, use_partials=True)

        runner._client.streaming_recognize.return_value = REAL_API_RESPONSES
        runner._response_loop()

        # With partials enabled, we should have more calls (INTERIMS + FINALS)
        # 3 interims + 2 finals. But let's count exactly.
        # REAL_API_RESPONSES has 5 responses:
        # 0: INTERIM "Esto es una prueba de dictado hablando fluido. Estoy" (len=50)
        # 1: INTERIM "... Estoy intentando realizar un párrafo bastante largo para ver si tenemos" (len=112)
        # 2: FINAL   "... si tenemos resultados intermedios." (len=135)
        # 3: INTERIM "Eso es la prueba. Ahora mismo termino el párrafo y voy a ver" (len=60)
        # 4: FINAL   " Eso es la prueba, ahora mismo termino el párrafo y voy a ver si transcribe." (len=77)

        # With the new common prefix optimization:
        # 1. Type partial 1: 'Esto es una prueba de dictado hablando fluido. Estoy'
        # 2. Type suffix of partial 2: ' intentando realizar un párrafo bastante largo para ver si tenemos'
        # 3. Type suffix of final 1: ' resultados intermedios.'
        # 4. Type partial 3: 'Eso es la prueba. Ahora mismo termino el párrafo y voy a ver'
        # 5. BS partial 3 (0 common prefix due to leading space in final): 60 backspaces
        # 6. Type final 2: ' Eso es la prueba, ahora mismo termino el párrafo y voy a ver si transcribe.'
        # Total: 6 calls to input_simulator
        assert len(mock.calls) == 6
        assert mock.text.endswith(EXPECTED_FINAL_TEXT)

    def test_interim_replaced_by_final(self):
        """
        When a FINAL arrives, the previous INTERIM text must be "corrected".
        """
        mock = MockInputSimulator()
        runner = create_runner(mock, use_partials=True)

        runner._client.streaming_recognize.return_value = REAL_API_RESPONSES
        runner._response_loop()

        # Let's check the sequence of calls with the common prefix optimization
        # Call 0: First interim
        assert mock.calls[0] == "Esto es una prueba de dictado hablando fluido. Estoy"
        # Call 1: Second interim is an extension of the first, so only the suffix is typed
        assert (
            mock.calls[1]
            == " intentando realizar un párrafo bastante largo para ver si tenemos"
        )
        # Call 2: First final is an extension of the second interim, only the suffix is typed
        assert mock.calls[2] == " resultados intermedios."
        # Call 3: Next interim (after a pause)
        assert (
            mock.calls[3]
            == "Eso es la prueba. Ahora mismo termino el párrafo y voy a ver"
        )
        # Call 4: The second final starts with a space and changes punctuation,
        # so there's no common prefix. We expect 60 backspaces.
        assert mock.calls[4] == "\b" * len(
            "Eso es la prueba. Ahora mismo termino el párrafo y voy a ver"
        )
        # Call 5: The full second final is typed
        assert (
            mock.calls[5]
            == " Eso es la prueba, ahora mismo termino el párrafo y voy a ver si transcribe."
        )

    def test_final_text_is_correct(self):
        """The final written text must be correct even with partials enabled."""
        mock = MockInputSimulator()
        runner = create_runner(mock, use_partials=True)

        runner._client.streaming_recognize.return_value = REAL_API_RESPONSES
        runner._response_loop()

        # With the improved MockInputSimulator, mock.text should handle backspaces correctly
        assert mock.text == EXPECTED_FINAL_TEXT
