"""
Tests for Intent Matcher Service
Tests pattern-matching user intent to suggest workflows.
"""

import pytest
from pathlib import Path
import sys
import importlib.util

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load module directly from file to avoid circular import in dashboard.core.__init__.py
_spec = importlib.util.spec_from_file_location(
    "intent_matcher",
    project_root / "dashboard" / "core" / "intent_matcher.py"
)
intent_matcher_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(intent_matcher_module)
IntentMatcher = intent_matcher_module.IntentMatcher


def test_match_intent_returns_workflow_suggestions():
    """Test that intent matcher suggests workflows based on keywords."""
    matcher = IntentMatcher()

    # Test video from text intent
    result = matcher.match("I want to create a video from text")
    assert result["matched"] == True
    assert result["suggested_type"] == "t2v"
    assert len(result["suggestions"]) > 0


def test_match_intent_handles_image_to_video():
    """Test image to video intent detection."""
    matcher = IntentMatcher()

    result = matcher.match("turn this image into a video")
    assert result["matched"] == True
    assert result["suggested_type"] == "i2v"


def test_match_intent_handles_no_match():
    """Test that unclear intent returns no match."""
    matcher = IntentMatcher()

    result = matcher.match("hello world")
    assert result["matched"] == False


def test_match_intent_case_insensitive():
    """Test that matching is case-insensitive."""
    matcher = IntentMatcher()

    result = matcher.match("I Want To CREATE A VIDEO From Text")
    assert result["matched"] == True
    assert result["suggested_type"] == "t2v"


def test_match_intent_text_to_image():
    """Test text to image intent detection."""
    matcher = IntentMatcher()

    result = matcher.match("generate an image of a sunset")
    assert result["matched"] == True
    assert result["suggested_type"] == "t2i"


def test_match_intent_upscale():
    """Test upscale intent detection."""
    matcher = IntentMatcher()

    result = matcher.match("upscale this image to 4k")
    assert result["matched"] == True
    assert result["suggested_type"] == "upscale"


def test_match_intent_audio():
    """Test audio generation intent detection."""
    matcher = IntentMatcher()

    result = matcher.match("create music for my video")
    assert result["matched"] == True
    assert result["suggested_type"] == "audio"


def test_match_intent_returns_suggestions():
    """Test that matched intent returns suggestion descriptions."""
    matcher = IntentMatcher()

    result = matcher.match("I want a picture of a cat")
    assert result["matched"] == True
    assert len(result["suggestions"]) > 0
    assert any("FLUX" in s or "SDXL" in s for s in result["suggestions"])


def test_match_intent_returns_input_output_types():
    """Test that matched intent returns input and output types."""
    matcher = IntentMatcher()

    result = matcher.match("video from text")
    assert result["matched"] == True
    assert "text" in result["suggested_input_types"]
    assert "video" in result["suggested_output_types"]


def test_get_quick_actions():
    """Test that quick actions are returned correctly."""
    matcher = IntentMatcher()

    actions = matcher.get_quick_actions()

    assert len(actions) == 5
    assert all("id" in a and "label" in a and "icon" in a for a in actions)

    # Check that all types are represented
    action_ids = [a["id"] for a in actions]
    assert "t2v" in action_ids
    assert "i2v" in action_ids
    assert "t2i" in action_ids
    assert "upscale" in action_ids
    assert "audio" in action_ids


def test_match_intent_empty_string():
    """Test that empty string returns no match."""
    matcher = IntentMatcher()

    result = matcher.match("")
    assert result["matched"] == False


def test_match_intent_whitespace_only():
    """Test that whitespace-only string returns no match."""
    matcher = IntentMatcher()

    result = matcher.match("   ")
    assert result["matched"] == False


def test_match_intent_partial_keyword_no_match():
    """Test that partial keyword matches don't trigger."""
    matcher = IntentMatcher()

    # "vide" is not "video"
    result = matcher.match("I want a vide")
    assert result["matched"] == False
