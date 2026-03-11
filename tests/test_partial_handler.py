from dictatux.partial_handler import PartialTextHandler
from tests.helpers import MockInputSimulator


def test_initial_partial():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello")
    assert mock.calls == ["hello"]
    assert mock.text == "hello"


def test_extending_partial():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello")
    handler.handle_partial("hello world")

    assert mock.calls == ["hello", " world"]
    assert mock.text == "hello world"


def test_changing_partial_suffix():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello worl")
    handler.handle_partial("hello world")

    assert mock.calls == ["hello worl", "d"]
    assert mock.text == "hello world"


def test_changing_partial_middle():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello word")
    # "hello wor" is the common prefix (9 chars).
    # Differing suffix of previous: "d" (1 char). So 1 backspace.
    # New suffix: "ld"
    handler.handle_partial("hello world")

    assert mock.calls == ["hello word", "\b", "ld"]
    assert mock.text == "hello world"


def test_identical_partials():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello")
    handler.handle_partial("hello")

    assert mock.calls == ["hello"]  # Should not call again


def test_empty_partials():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("")
    handler.handle_partial("   ")

    assert mock.calls == []
    assert mock.text == ""


def test_final_text_replaces_partial():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello worl")
    # Final has a typo fix at the start or completely different capitalization
    # Prefix: "H" vs "h" -> 0 common prefix
    # Must backspace 10 times, then type "Hello world."
    handler.handle_final("Hello world.")

    assert mock.calls == ["hello worl", "\b" * 10, "Hello world."]
    assert mock.text == "Hello world."


def test_final_text_extends_partial():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello ")
    handler.handle_final("hello world")

    assert mock.calls == ["hello ", "world"]
    assert mock.text == "hello world"


def test_final_empty_clears_partial():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_partial("hello")
    handler.handle_final("")

    assert mock.calls == ["hello", "\b\b\b\b\b"]
    assert mock.text == ""


def test_consecutive_finals():
    mock = MockInputSimulator()
    handler = PartialTextHandler(mock)

    handler.handle_final("hello")
    # There is no partial state, so it shouldn't try to backspace
    handler.handle_final(" world")

    assert mock.calls == ["hello", " world"]
    assert mock.text == "hello world"
