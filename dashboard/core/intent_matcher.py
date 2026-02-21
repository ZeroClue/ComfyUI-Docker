"""
Intent Matcher Service
Pattern-matches user intent to suggest workflows.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class IntentPattern:
    """Pattern for matching user intent."""
    keywords: List[str]
    suggested_type: str
    suggested_input_types: List[str]
    suggested_output_types: List[str]


class IntentMatcher:
    """Matches user intent to workflow types using pattern matching."""

    PATTERNS = [
        # Text to Video
        IntentPattern(
            keywords=["video from text", "text to video", "generate video", "create video", "make a video"],
            suggested_type="t2v",
            suggested_input_types=["text"],
            suggested_output_types=["video"]
        ),
        # Image to Video
        IntentPattern(
            keywords=["image to video", "animate image", "into a video", "photo to video", "picture to video"],
            suggested_type="i2v",
            suggested_input_types=["image"],
            suggested_output_types=["video"]
        ),
        # Text to Image
        IntentPattern(
            keywords=["image from text", "text to image", "generate image", "create image", "make an image", "picture of", "image of a", "generate an image"],
            suggested_type="t2i",
            suggested_input_types=["text"],
            suggested_output_types=["image"]
        ),
        # Image to Image
        IntentPattern(
            keywords=["image to image", "transform image", "style transfer", "edit image", "modify image"],
            suggested_type="i2i",
            suggested_input_types=["image"],
            suggested_output_types=["image"]
        ),
        # Upscale
        IntentPattern(
            keywords=["upscale", "enhance resolution", "improve quality", "super resolution"],
            suggested_type="upscale",
            suggested_input_types=["image", "video"],
            suggested_output_types=["image", "video"]
        ),
        # Audio
        IntentPattern(
            keywords=["music", "audio", "sound", "generate audio", "create music"],
            suggested_type="audio",
            suggested_input_types=["text"],
            suggested_output_types=["audio"]
        ),
    ]

    def match(self, intent_text: str) -> Dict[str, Any]:
        """
        Match user intent to workflow suggestions.

        Args:
            intent_text: User's intent description

        Returns:
            Dict with matched status and suggestions
        """
        intent_lower = intent_text.lower().strip()

        for pattern in self.PATTERNS:
            for keyword in pattern.keywords:
                if keyword in intent_lower:
                    return {
                        "matched": True,
                        "suggested_type": pattern.suggested_type,
                        "suggested_input_types": pattern.suggested_input_types,
                        "suggested_output_types": pattern.suggested_output_types,
                        "matched_keyword": keyword,
                        "suggestions": self._get_suggestion_descriptions(pattern),
                    }

        return {
            "matched": False,
            "suggested_type": None,
            "suggestions": [],
        }

    def _get_suggestion_descriptions(self, pattern: IntentPattern) -> List[str]:
        """Get human-readable suggestions for a pattern."""
        descriptions = {
            "t2v": ["Text-to-Video workflows like WAN 2.2, LTX-Video"],
            "i2v": ["Image-to-Video workflows like WAN I2V, Hunyuan I2V"],
            "t2i": ["Text-to-Image workflows like FLUX, SDXL, SD3.5"],
            "i2i": ["Image-to-Image workflows like SDXL Img2Img"],
            "upscale": ["Upscaling workflows for images and videos"],
            "audio": ["Audio generation workflows like ACE Step, MusicGen"],
        }
        return descriptions.get(pattern.suggested_type, [])

    def get_quick_actions(self) -> List[Dict[str, str]]:
        """Get list of quick action buttons for the intent bar."""
        return [
            {"id": "t2v", "label": "Video from text", "icon": "🎬"},
            {"id": "i2v", "label": "Image to video", "icon": "🎥"},
            {"id": "t2i", "label": "Image from text", "icon": "🖼️"},
            {"id": "upscale", "label": "Upscale", "icon": "🔍"},
            {"id": "audio", "label": "Generate audio", "icon": "🎵"},
        ]


__all__ = ["IntentMatcher"]
