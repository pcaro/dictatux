from tests.helpers import calculate_wer, normalize_text


def test_normalize_text():
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("  Extra   spaces  ") == "extra spaces"
    assert normalize_text("NoPunctuation") == "nopunctuation"
    assert normalize_text("It's a test.") == "its a test"


def test_calculate_wer():
    # Identical
    assert calculate_wer("hello world", "hello world") == 0.0
    # One substitution
    assert calculate_wer("hello world", "hello friend") == 0.5
    # One insertion
    assert calculate_wer("hello", "hello world") == 1.0
    # Empty hypothesis
    assert calculate_wer("hello", "") == 1.0
    # Empty reference (generating text when none is expected is a 100% error rate)
    assert calculate_wer("", "hello") == 1.0
    # Empty both
    assert calculate_wer("", "") == 0.0
