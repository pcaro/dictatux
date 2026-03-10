"""Helper to handle partial transcriptions and manage backspaces."""

from __future__ import annotations
from typing import Callable


class PartialTextHandler:
    """Helper to handle partial transcriptions and manage backspaces."""

    def __init__(self, input_simulator: Callable[[str], None]) -> None:
        self._input_simulator = input_simulator
        self._last_partial = ""

    def _get_prefix_length(self, s1: str, s2: str) -> int:
        min_len = min(len(s1), len(s2))
        for i in range(min_len):
            if s1[i] != s2[i]:
                return i
        return min_len

    def handle_partial(self, transcript: str) -> None:
        """Process an interim (partial) transcription."""
        if not transcript.strip():
            return

        # If it's the same as before, do nothing
        if transcript == self._last_partial:
            return

        # Calculate common prefix to avoid deleting what didn't change
        prefix_len = self._get_prefix_length(self._last_partial, transcript)

        # Delete the differing suffix of the last partial
        backspaces_needed = len(self._last_partial) - prefix_len
        if backspaces_needed > 0:
            self._input_simulator("\b" * backspaces_needed)

        # Type the new suffix
        new_suffix = transcript[prefix_len:]
        if new_suffix:
            self._input_simulator(new_suffix)
            
        self._last_partial = transcript

    def handle_final(self, transcript: str) -> None:
        """Process a final transcription and reset state."""
        if not transcript.strip():
            if self._last_partial:
                self._input_simulator("\b" * len(self._last_partial))
                self._last_partial = ""
            return

        prefix_len = self._get_prefix_length(self._last_partial, transcript)
        
        backspaces_needed = len(self._last_partial) - prefix_len
        if backspaces_needed > 0:
            self._input_simulator("\b" * backspaces_needed)

        new_suffix = transcript[prefix_len:]
        if new_suffix:
            self._input_simulator(new_suffix)

        self._last_partial = ""
