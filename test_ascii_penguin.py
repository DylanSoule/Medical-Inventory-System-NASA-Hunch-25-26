"""
Tests for ASCII Penguin Module
"""
import pytest
from ascii_penguin import get_penguin, display_penguin

def test_get_penguin_returns_string():
    """Test that get_penguin returns a string."""
    result = get_penguin()
    assert isinstance(result, str)

def test_get_penguin_not_empty():
    """Test that get_penguin returns a non-empty string."""
    result = get_penguin()
    assert len(result) > 0

def test_get_penguin_contains_penguin_features():
    """Test that the penguin ASCII art contains characteristic features."""
    result = get_penguin()
    # Check for eyes
    assert "o o" in result or "O O" in result
    # Check that it's multiline
    assert "\n" in result

def test_display_penguin_prints(capsys):
    """Test that display_penguin prints to stdout."""
    display_penguin()
    captured = capsys.readouterr()
    assert len(captured.out) > 0
    assert "o o" in captured.out or "O O" in captured.out
